import math
from typing import TYPE_CHECKING

from simpy import Environment

from simulador.core.request import Request
from simulador.routing.base import RoutingBase
from simulador.utils.metrics import Metrics

if TYPE_CHECKING:
    from simulador import Topology


class FirstFitDisasterAware(RoutingBase):
    @staticmethod
    def __str__() -> str:
        """Return a string representation of the routing method."""
        return "FirstFit first fit"

    @staticmethod
    def rotear_requisicao(
        requisicao: Request, topology: "Topology", env: Environment
    ) -> bool:
        requisicao_roteada_com_sucesso = FirstFitDisasterAware.__rotear_requisicao(
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

        requisicao_roteada_com_sucesso = FirstFitDisasterAware.__rotear_requisicao(
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
        informacoes_dos_datapaths, pelo_menos_uma_janela_habil = (
            FirstFitDisasterAware.__retorna_informacoes_datapaths(requisicao, topology)
        )
        if pelo_menos_uma_janela_habil:
            FirstFitDisasterAware.__aloca_requisicao(
                requisicao, topology, informacoes_dos_datapaths, env
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
    ) -> None:
        for informacoes_datapath in informacoes_datapaths:
            if (
                informacoes_datapath["maior_janela_contigua_continua"]
                >= informacoes_datapath["numero_slots_necessarios"]
            ):
                FirstFitDisasterAware.__aloca_datapath(
                    requisicao, topology, informacoes_datapath, env
                )
                break

    @staticmethod
    def __aloca_datapath(
        requisicao: Request,
        topology: "Topology",
        informacoes_datapath: dict,
        env: Environment,
    ) -> None:
        # janelas_possiveis = [ janela for janela in informacoes_datapath["slots_livres_agrupados"] if len(janela) >= informacoes_datapath["numero_slots_necessarios"]]
        index_inicio = next(
            (
                index_inicio
                for index_inicio, index_final in informacoes_datapath[
                    "lista_de_inicios_e_fins"
                ]
                if index_final - index_inicio + 1
                >= informacoes_datapath["numero_slots_necessarios"]
            ),
            0,
        )

        index_final = int(
            index_inicio + informacoes_datapath["numero_slots_necessarios"] - 1
        )
        caminho = informacoes_datapath["caminho"]

        topology.aloca_janela(caminho, (index_inicio, index_final))

        requisicao.processo_de_desalocacao = env.process(
            topology.desaloca_janela(
                caminho, (index_inicio, index_final), requisicao.holding_time, env
            )
        )

        requisicao.aceita_requisicao(
            informacoes_datapath["numero_slots_necessarios"],
            caminho,
            len(caminho),
            (index_inicio, index_final),
            env.now,
            env.now + requisicao.holding_time,
            informacoes_datapath["distancia"],
        )

    @staticmethod
    def __retorna_informacoes_datapaths(
        requisicao: Request, topology: "Topology"
    ) -> tuple[list[dict], bool]:
        if (
            requisicao.dst in topology.caminhos_mais_curtos_entre_links_durante_desastre
            and requisicao.src
            in topology.caminhos_mais_curtos_entre_links_durante_desastre
        ):
            caminhos = topology.caminhos_mais_curtos_entre_links_durante_desastre[
                int(requisicao.src)
            ][int(requisicao.dst)]
        else:
            caminhos = topology.caminhos_mais_curtos_entre_links[int(requisicao.src)][
                int(requisicao.dst)
            ]

        lista_de_informacoes_datapath = []
        pelo_menos_uma_janela_habil = False

        for informacoes_caminho in caminhos:
            caminho = informacoes_caminho["caminho"]
            if not topology.caminho_em_funcionamento(
                caminho
            ) or not topology.pode_passar_pelo_caminho_que_vai_falhar(caminho):
                continue
            distancia = informacoes_caminho["distancia"]
            fator_de_modulacao = informacoes_caminho["fator_de_modulacao"]
            numero_slots_necessarios = FirstFitDisasterAware.__slots_nescessarios(
                requisicao.bandwidth, fator_de_modulacao
            )

            lista_de_inicios_e_fins, maior_janela_caminho = (
                FirstFitDisasterAware.informacoes_sobre_slots(caminho, topology)
            )

            dados_do_caminho = {
                "caminho": caminho,
                "distancia": distancia,
                "fator_de_modulacao": fator_de_modulacao,
                "lista_de_inicios_e_fins": lista_de_inicios_e_fins,
                "numero_slots_necessarios": numero_slots_necessarios,
                "maior_janela_contigua_continua": maior_janela_caminho,
            }

            lista_de_informacoes_datapath.append(dados_do_caminho)
            if maior_janela_caminho >= numero_slots_necessarios:
                pelo_menos_uma_janela_habil = True
                break

        return (lista_de_informacoes_datapath, pelo_menos_uma_janela_habil)

    @staticmethod
    def informacoes_sobre_slots(
        caminho, topology: "Topology"
    ) -> tuple[list[tuple[int, int]], int]:
        lista_de_inicios_e_fins = []
        current_start: int | None = None
        last_slot_was_free = False
        maior_janela = 0

        for i in range(topology.numero_de_slots):
            if FirstFitDisasterAware.__checa_concurrency_slot(caminho, topology, i):
                if not last_slot_was_free:
                    current_start = i
                    last_slot_was_free = True
                    tamanho_janela_atual = 1
                else:
                    tamanho_janela_atual += 1

            elif last_slot_was_free and current_start is not None:
                lista_de_inicios_e_fins.append((current_start, i - 1))
                maior_janela = max(maior_janela, tamanho_janela_atual)
                last_slot_was_free = False

        if last_slot_was_free and current_start is not None:
            lista_de_inicios_e_fins.append((current_start, i))
            maior_janela = max(maior_janela, tamanho_janela_atual)
            last_slot_was_free = False

        return lista_de_inicios_e_fins, maior_janela

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
