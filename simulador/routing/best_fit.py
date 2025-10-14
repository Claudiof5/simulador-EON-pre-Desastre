import math
from typing import TYPE_CHECKING

from simpy import Environment

from simulador.core.request import Request
from simulador.routing.base import RoutingBase
from simulador.utils.metrics import Metrics

if TYPE_CHECKING:
    from simulador import Topology


class FirstFitBestFit(RoutingBase):
    @staticmethod
    def __str__() -> str:
        """Return a string representation of the routing method."""
        return "FirstFit best fit"

    @staticmethod
    def rotear_requisicao(
        requisicao: Request, topology: "Topology", env: Environment
    ) -> bool:
        requisicao_roteada_com_sucesso = FirstFitBestFit.__rotear_requisicao(
            requisicao, topology, env
        )
        if requisicao_roteada_com_sucesso:
            Metrics.incrementa_numero_requisicoes_aceitas(requisicao, env)
            return True
        Metrics.incrementa_numero_requisicoes_bloqueadas(requisicao, env)
        return False

    @staticmethod
    def rerotear_requisicao(
        requisicao: Request, topology: "Topology", env: Environment
    ) -> bool:
        requisicao.dados_pre_reroteamento = (
            requisicao.retorna_tupla_chave_dicionario_dos_atributos()
        )

        requisicao_roteada_com_sucesso = FirstFitBestFit.__rotear_requisicao(
            requisicao, topology, env
        )
        if requisicao_roteada_com_sucesso:
            Metrics.incrementa_numero_requisicoes_reroteadas_aceitas(requisicao, env)
            return True
        Metrics.incrementa_numero_requisicoes_reroteadas_bloqueadas(requisicao, env)
        return False

    @staticmethod
    def __rotear_requisicao(
        requisicao: Request, topology: "Topology", env: Environment
    ) -> bool:
        (
            informacoes_dos_datapaths,
            pelo_menos_uma_janela_habil,
            indice_melhor_caminho,
        ) = FirstFitBestFit.__retorna_informacoes_datapaths(requisicao, topology)
        if pelo_menos_uma_janela_habil and indice_melhor_caminho is not None:
            FirstFitBestFit.__aloca_requisicao(
                requisicao,
                topology,
                informacoes_dos_datapaths,
                env,
                indice_melhor_caminho,
            )
            return True
        requisicao.bloqueia_requisicao(env.now)
        return False

    @staticmethod
    def __aloca_requisicao(
        requisicao: Request,
        topology: "Topology",
        informacoes_datapaths: list[dict],
        env: Environment,
        indice_melhor_caminho: int,
    ) -> None:
        informacoes_datapath = informacoes_datapaths[indice_melhor_caminho]
        FirstFitBestFit.__aloca_datapath(
            requisicao, topology, informacoes_datapath, env
        )

    @staticmethod
    def __aloca_datapath(
        requisicao: Request,
        topology: "Topology",
        informacoes_datapath: dict,
        env: Environment,
    ) -> None:
        index_inicio = informacoes_datapath["inicio_melhor_janela_habil"]
        index_fim = index_inicio + informacoes_datapath["numero_slots_necessarios"] - 1
        caminho = informacoes_datapath["caminho"]

        topology.aloca_janela(caminho, (index_inicio, index_fim))

        requisicao.processo_de_desalocacao = env.process(
            topology.desaloca_janela(
                caminho, (index_inicio, index_fim), requisicao.holding_time, env
            )
        )
        requisicao.aceita_requisicao(
            informacoes_datapath["numero_slots_necessarios"],
            caminho,
            len(caminho),
            (index_inicio, index_fim),
            env.now,
            env.now + requisicao.holding_time,
            informacoes_datapath["distancia"],
        )

    @staticmethod
    def __retorna_informacoes_datapaths(
        requisicao: Request, topology: "Topology"
    ) -> tuple[list[dict], bool, int | None]:
        caminhos = topology.caminhos_mais_curtos_entre_links[int(requisicao.src)][
            int(requisicao.dst)
        ]

        lista_de_informacoes_datapath = []
        pelo_menos_uma_janela_habil = False

        indice_melhor_caminho = None
        tamanho_melhor_janela = None

        numero_de_caminhos_pulados = 0
        for i, informacoes_caminho in enumerate(caminhos):
            caminho = informacoes_caminho["caminho"]
            if not topology.caminho_em_funcionamento(caminho):
                numero_de_caminhos_pulados += 1
                continue
            distancia = informacoes_caminho["distancia"]
            fator_de_modulacao = informacoes_caminho["fator_de_modulacao"]
            numero_slots_necessarios = FirstFitBestFit.__slots_nescessarios(
                requisicao.bandwidth, fator_de_modulacao
            )

            (
                lista_de_inicios_e_fins,
                tamanho_menor_janela_habil,
                inicio_menor_janela_habil,
            ) = FirstFitBestFit.informacoes_sobre_slots(
                caminho, topology, numero_slots_necessarios
            )
            ###slots_livres, slots_livres_agrupados, lista_de_inicios_e_fins = FirstFitBestFit.__informacoes_sobre_slots(caminho, topology)
            dados_do_caminho = {
                "caminho": caminho,
                "distancia": distancia,
                "fator_de_modulacao": fator_de_modulacao,
                "lista_de_inicios_e_fins": lista_de_inicios_e_fins,
                "numero_slots_necessarios": numero_slots_necessarios,
                "tamanho_menor_janela_habil": tamanho_menor_janela_habil,
                "inicio_melhor_janela_habil": inicio_menor_janela_habil,
            }

            lista_de_informacoes_datapath.append(dados_do_caminho)

            if tamanho_menor_janela_habil is not None:
                pelo_menos_uma_janela_habil = True

                if tamanho_menor_janela_habil == numero_slots_necessarios:
                    tamanho_melhor_janela = tamanho_menor_janela_habil
                    indice_melhor_caminho = i - numero_de_caminhos_pulados
                    break
                if indice_melhor_caminho is None or (
                    tamanho_melhor_janela is not None
                    and tamanho_menor_janela_habil < tamanho_melhor_janela
                ):
                    tamanho_melhor_janela = tamanho_menor_janela_habil
                    indice_melhor_caminho = i - numero_de_caminhos_pulados

        return (
            lista_de_informacoes_datapath,
            pelo_menos_uma_janela_habil,
            indice_melhor_caminho,
        )

    @staticmethod
    def informacoes_sobre_slots(
        caminho, topology: "Topology", numero_slots_nescessarios: int
    ) -> tuple[list[tuple[int, int]], int | None, int | None]:
        lista_de_inicios_e_fins = []
        current_start: int | None = None
        last_slot_was_free = False
        tamanho_menor_janela_habil: int | None = None
        inicio_menor_janela_habil: int | None = None
        for i in range(topology.numero_de_slots):
            if FirstFitBestFit.__checa_concurrency_slot(caminho, topology, i):
                if not last_slot_was_free:
                    current_start = i
                    last_slot_was_free = True
                    tamanho_janela_atual = 1
                else:
                    tamanho_janela_atual += 1

            elif last_slot_was_free and current_start is not None:
                lista_de_inicios_e_fins.append((current_start, i - 1))
                if tamanho_janela_atual >= numero_slots_nescessarios and (
                    tamanho_menor_janela_habil is None
                    or tamanho_janela_atual < tamanho_menor_janela_habil
                ):
                    tamanho_menor_janela_habil = tamanho_janela_atual
                    inicio_menor_janela_habil = current_start
                last_slot_was_free = False

        if last_slot_was_free and current_start is not None:
            lista_de_inicios_e_fins.append((current_start, i))
            if tamanho_janela_atual >= numero_slots_nescessarios and (
                tamanho_menor_janela_habil is None
                or tamanho_janela_atual < tamanho_menor_janela_habil
            ):
                tamanho_menor_janela_habil = tamanho_janela_atual
                inicio_menor_janela_habil = current_start
            last_slot_was_free = False

        return (
            lista_de_inicios_e_fins,
            tamanho_menor_janela_habil,
            inicio_menor_janela_habil,
        )

    @staticmethod
    def __checa_concurrency_slot(
        caminho: list, topology: "Topology", indice: int
    ) -> bool:
        for i in range(0, (len(caminho) - 1)):
            if topology.topology[caminho[i]][caminho[i + 1]]["slots"][indice] != 0:
                return False
        return True

    @staticmethod
    def __slots_nescessarios(demanda, fator_modulacao) -> int:
        return int(math.ceil(float(demanda) / fator_modulacao))
