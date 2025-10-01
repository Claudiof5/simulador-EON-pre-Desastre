from collections.abc import Generator
from typing import TYPE_CHECKING

import networkx as nx
from Datacenter.Datacenter import Datacenter
from Datacenter.GeradorDeDatacenter import GeradorDeDatacenter
from Roteamento.IRoteamento import IRoteamento
from Roteamento.Roteamento import Roteamento

if TYPE_CHECKING:
    from Desastre.Desastre import Desastre

    from simulador import Simulador


class ISP:
    def __init__(
        self,
        isp_id: int,
        nodes: list[int],
        edges: list[tuple[int, int]],
        roteamento_de_desastre: "IRoteamento" = Roteamento,
    ) -> None:
        """Initialize the ISP class.

        Args:
            isp_id: The ID of the ISP
            nodes: The nodes of the ISP
            edges: The edges of the ISP
            roteamento_de_desastre: The roteamento de desastre of the ISP
        """
        self.isp_id: int = isp_id
        self.nodes: list[int] = nodes
        self.edges: list[tuple[int, int]] = edges
        self.roteamento_atual: IRoteamento = Roteamento
        self.roteamento_primario: IRoteamento = Roteamento
        self.roteamento_desastre: IRoteamento = roteamento_de_desastre
        self.datacenter: Datacenter = None

    def define_datacenter(
        self, disaster: "Desastre", topology: nx.Graph, specific_values=None
    ) -> None:
        self.datacenter = GeradorDeDatacenter.gerar_datacenter(
            disaster, topology, self.nodes, specific_values
        )

    def iniciar_migracao(self, simulador: "Simulador") -> Generator:
        yield simulador.env.timeout(self.datacenter.tempo_de_reacao - simulador.env.now)
        self.roteamento_atual = self.roteamento_desastre
        self.datacenter.iniciar_migracao(simulador, self)
        yield simulador.env.timeout(
            (simulador.desastre.start + simulador.desastre.duration) - simulador.env.now
        )
        self.roteamento_atual = self.roteamento_primario

    def imprime_isp(self) -> None:
        print("ISP: ", self.isp_id)
        print("Nós: ", self.nodes)
        print("Arestas: ", self.edges)
        print("Datacenter source: ", self.datacenter.source)
        print("Datacenter destination: ", self.datacenter.destination)

    def troca_roteamento_desastre(self, roteamento: "IRoteamento") -> None:
        self.roteamento_desastre = roteamento
