from collections.abc import Generator
from typing import TYPE_CHECKING

from simulador.core.request import Request
from simulador.routing.base import RoutingBase
from simulador.utils.logger import Logger
from simulador.utils.metrics import Metrics

if TYPE_CHECKING:
    from simulador.core.topology import Topology
    from simulador.main import Simulator


class Disaster:
    def __init__(
        self,
        start: float,
        duration: float,
        list_of_dict_node_per_start_time: list[dict],
        list_of_dict_link_per_start_time: list[dict],
        eventos: list[dict],
    ) -> None:
        """Initialize the Disaster class.

        Args:
            start: The start time of the disaster
            duration: The duration of the disaster
            list_of_dict_node_per_start_time: The list of dictionaries of nodes per start time
            list_of_dict_link_per_start_time: The list of dictionaries of links per start time
            eventos: The events of the disaster
        """
        self.start: float = start
        self.duration: float = duration
        self.eventos_nao_iniciados: list[dict] = eventos
        self.list_of_dict_node_per_start_time: list[dict] = (
            list_of_dict_node_per_start_time
        )
        self.list_of_dict_link_per_start_time: list[dict] = (
            list_of_dict_link_per_start_time
        )

    def imprime_desastre(self) -> None:
        print("Início do desastre: ", self.start)
        print("Duração do desastre: ", self.duration)
        print("Eventos: ", self.eventos_nao_iniciados)

    def iniciar_desastre(self, simulador: "Simulator") -> None:
        simulador.env.process(self.__gerar_falhas(simulador))

        # Always start ISP routing switches for all ISPs
        # This ensures roteamento_atual switches to roteamento_desastre at reaction times
        # and switches back after disaster ends, regardless of pre-generated vs runtime migration
        for isp in simulador.lista_de_isps:
            simulador.env.process(isp.iniciar_migracao(simulador))

    def seta_links_como_prestes_a_falhar(self, topology: "Topology") -> None:
        for dict_link in self.list_of_dict_link_per_start_time:
            src = dict_link["src"]
            dst = dict_link["dst"]
            topology.topology[src][dst]["vai falhar"] = True
            print("Link ", src, dst, " vai falhar")

        for dict_node in self.list_of_dict_node_per_start_time:
            node = dict_node["node"]
            for neighbor in topology.topology.neighbors(node):
                topology.topology[node][neighbor]["vai falhar"] = True
                print("Link ", node, neighbor, " vai falhar")

    def __gerar_falhas(self, simulador: "Simulator") -> Generator:
        while self.eventos_nao_iniciados != []:
            tempo_pro_proximo_evento = (
                self.eventos_nao_iniciados[0]["start_time"] + self.start
            ) - simulador.env.now
            yield simulador.env.timeout(tempo_pro_proximo_evento)
            evento = self.eventos_nao_iniciados.pop(0)
            self.__ativa_evento(evento, simulador)
            simulador.env.process(self.__desativa_evento(evento, simulador))

        yield simulador.env.timeout(self.start + self.duration - simulador.env.now)
        Logger.mensagem_desastre_finalizado(int(simulador.env.now))

    def __ativa_evento(self, informacoes_evento, simulador: "Simulator") -> None:
        if informacoes_evento["tipo"] == "node":
            self.__falha_no_no(informacoes_evento["node"], simulador)
            Logger.mensagem_acompanha_node_desastre(
                informacoes_evento["node"], int(simulador.env.now)
            )

        elif informacoes_evento["tipo"] == "link":
            self.__falha_no_link(
                informacoes_evento["src"], informacoes_evento["dst"], simulador
            )
            Logger.mensagem_acompanha_link_desastre(
                informacoes_evento["src"],
                informacoes_evento["dst"],
                int(simulador.env.now),
            )

    def __desativa_evento(
        self, informacoes_evento: dict, simulador: "Simulator"
    ) -> Generator:
        yield simulador.env.timeout(self.start + self.duration - simulador.env.now)

        if informacoes_evento["tipo"] == "node":
            self.__restaura_no(informacoes_evento, simulador)
            Logger.mensagem_acompanha_node_desastre(
                informacoes_evento["node"], int(simulador.env.now)
            )

        elif informacoes_evento["tipo"] == "link":
            self.__restaura_link(informacoes_evento, simulador)
            Logger.mensagem_acompanha_link_desastre(
                informacoes_evento["src"],
                informacoes_evento["dst"],
                int(simulador.env.now),
            )

    def __restaura_link(self, informacoes_evento: dict, simulador: "Simulator") -> None:
        src = informacoes_evento["src"]
        dst = informacoes_evento["dst"]
        if (
            simulador.topology.topology.has_edge(src, dst)
            and simulador.topology.topology[src][dst]["failed"]
        ):
            simulador.topology.topology[src][dst]["failed"] = False
            simulador.topology.topology[src][dst]["vai falhar"] = False

    def __restaura_no(self, informacoes_evento, simulador: "Simulator") -> None:
        node = informacoes_evento["node"]
        if node in simulador.topology.topology.nodes:
            for neighbor in simulador.topology.topology.neighbors(node):
                self.__restaura_link({"src": node, "dst": neighbor}, simulador)

    def __falha_no_link(self, node1: int, node2: int, simulador: "Simulator") -> None:
        topology = simulador.topology
        if (
            topology.topology.has_edge(node1, node2)
            and not topology.topology[node1][node2]["failed"]
        ):
            topology.topology[node1][node2]["failed"] = True

            requisicoes_falhas: list[Request] = self.__quem_falhou_link(
                node1, node2, simulador
            )

            for requisicao in requisicoes_falhas:
                if not requisicao.afetada_por_desastre:
                    Metrics.registra_requisicao_afetada(requisicao)

                    if requisicao.processo_de_desalocacao is not None:
                        requisicao.processo_de_desalocacao.interrupt()
                    index_isp = requisicao.src_isp_index
                    topology.desalocate(
                        requisicao.caminho, requisicao.index_de_inicio_e_final
                    )
                    requisicao.afetada_por_desastre = True
                    roteador: type[RoutingBase] = simulador.lista_de_isps[
                        index_isp
                    ].roteamento_atual
                    roteador.rerotear_requisicao(requisicao, topology, simulador.env)
                    requisicao.afetada_por_desastre = True

    def __falha_no_no(self, node: int, simulador: "Simulator") -> None:
        topology = simulador.topology.topology

        if node in topology.nodes:
            for neighbor in topology.neighbors(node):
                self.__falha_no_link(node, neighbor, simulador)

    def __quem_falhou_link(
        self, pontaa: int, pontab: int, simulador: "Simulator"
    ) -> list[Request]:
        requisicoes_ativas_que_falharam_no_link: list[Request] = []
        requisicoes = Metrics.get_requisicoes()

        for req in requisicoes:
            if (
                not req.bloqueada
                and simulador.topology.caminho_passa_por_link(
                    pontaa, pontab, req.caminho
                )
                and req.tempo_criacao is not None
                and req.tempo_desalocacao is not None
                and simulador.env.now >= req.tempo_criacao
                and simulador.env.now < req.tempo_desalocacao
            ):
                req.dados_pre_reroteamento = (
                    req.retorna_tupla_chave_dicionario_dos_atributos()
                )
                requisicoes_ativas_que_falharam_no_link.append(req)

        return requisicoes_ativas_que_falharam_no_link
