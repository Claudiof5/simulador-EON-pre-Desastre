"""Network topology management for EON simulation.

Contains the Topologia class that manages the network topology including:
- Network graph structure and slot allocation
- Shortest path calculations for routing
- ISP assignment to nodes and edges
- Disaster-aware path computation
- Resource allocation and deallocation
"""

from collections.abc import Generator
from itertools import islice
from typing import TYPE_CHECKING

import networkx as nx
import simpy
from ISP.ISP import ISP
from variaveis import (
    DISTANCIA_MODULACAO_2,
    DISTANCIA_MODULACAO_3,
    DISTANCIA_MODULACAO_4,
    FATOR_MODULACAO_1,
    FATOR_MODULACAO_2,
    FATOR_MODULACAO_3,
    FATOR_MODULACAO_4,
    SLOT_SIZE,
)

if TYPE_CHECKING:
    from Desastre.Desastre import Desastre


class Topologia:
    """Network topology management for EON simulation.

    Manages the optical network topology including:
    - Network graph structure and slot allocation
    - Shortest path calculations for routing
    - ISP assignment to nodes and edges
    - Disaster-aware path computation
    - Resource allocation and deallocation

    Attributes:
        topology: NetworkX graph representing the network
        numero_de_slots: Total number of frequency slots available
        caminhos_mais_curtos_entre_links: Precomputed shortest paths
        caminhos_mais_curtos_entre_links_durante_desastre: Disaster-aware paths
        desastre: Associated disaster event handler

    """

    def __init__(
        self,
        topology: nx.Graph,
        list_of_isp: list[ISP],
        numero_de_caminhos: int,
        numero_de_slots: int,
    ) -> None:
        """Initialize the network topology.

        Args:
            topology: NetworkX graph representing the network structure
            list_of_isp: List of Internet Service Providers
            numero_de_caminhos: Number of shortest paths to compute
            numero_de_slots: Total number of frequency slots per link

        """
        self.topology: nx.Graph = topology
        self.numero_de_slots = numero_de_slots
        self.caminhos_mais_curtos_entre_links = {}
        self.caminhos_mais_curtos_entre_links_durante_desastre = {}
        self.desastre: Desastre = None
        self.__inicia_topologia(list_of_isp, numero_de_caminhos, numero_de_slots)

    def imprime_topologia(self) -> None:
        """Print topology information for debugging.

        Outputs nodes, edges, and their attributes to console.
        """
        print("Nós: ", self.topology.nodes())
        print("Arestas: ", self.topology.edges())
        print("Arestas com atributos: ", self.topology.edges(data=True))
        print("Nós com atributos: ", self.topology.nodes(data=True))

    def __inicia_topologia(
        self, list_of_isp: list[ISP], numero_de_caminhos: int, numero_de_slots: int
    ) -> None:
        """Initialize topology components.

        Args:
            list_of_isp: List of ISPs to assign to topology
            numero_de_caminhos: Number of paths to precompute
            numero_de_slots: Number of frequency slots per link

        """
        self.__inicia_status(numero_de_slots)
        self.__inicia_lista_de_isps_por_link_e_node(list_of_isp)
        self.__inicia_caminhos_mais_curtos(numero_de_caminhos)

    def __inicia_status(self, numero_de_slots: int) -> None:
        """Initialize link status and slot arrays.

        Args:
            numero_de_slots: Number of frequency slots per link

        """
        for edge in self.topology.edges():
            self.topology[edge[0]][edge[1]]["slots"] = [0] * numero_de_slots
            self.topology[edge[0]][edge[1]]["failed"] = False
            self.topology[edge[0]][edge[1]]["vai falhar"] = False

    def __inicia_lista_de_isps_por_link_e_node(self, list_of_isp: list[ISP]) -> None:
        """Assign ISPs to network nodes and edges.

        Args:
            list_of_isp: List of ISPs to assign to topology

        """
        for edge in self.topology.edges():
            self.topology[edge[0]][edge[1]]["ISPs"] = []
        for node in self.topology.nodes():
            self.topology.nodes[node]["ISPs"] = []

        for isp in list_of_isp:
            for node in isp.nodes:
                self.topology.nodes[node]["ISPs"].append(isp.id)

            for edge in isp.edges:
                self.topology[edge[0]][edge[1]]["ISPs"].append(isp.id)

    def __inicia_caminhos_mais_curtos(self, numero_de_caminhos: int) -> None:
        """Precompute shortest paths between all node pairs.

        Args:
            numero_de_caminhos: Number of alternative paths to compute

        """
        for node1 in self.topology.nodes():
            self.caminhos_mais_curtos_entre_links[int(node1)] = {}

            for node2 in self.topology.nodes():
                if node1 == node2:
                    continue

                caminhos_mais_curtos_entre_i_e_j = self.__k_shortest_paths(
                    self.topology, node1, node2, numero_de_caminhos, weight="weight"
                )
                informacoes_caminhos_mais_curtos_entre_i_e_j = []

                for caminho in caminhos_mais_curtos_entre_i_e_j:
                    distancia = self.distancia_caminho(caminho)
                    fator_de_modulacao = self.__fator_de_modulacao(distancia)
                    informacoes_caminhos_mais_curtos_entre_i_e_j.append(
                        {
                            "caminho": caminho,
                            "distancia": distancia,
                            "fator_de_modulacao": fator_de_modulacao,
                        }
                    )

                self.caminhos_mais_curtos_entre_links[int(node1)][int(node2)] = (
                    informacoes_caminhos_mais_curtos_entre_i_e_j
                )

    def inicia_caminhos_mais_curtos_durante_desastre(
        self, numero_de_caminhos: int, node_desastre: int
    ) -> None:
        """Compute shortest paths excluding disaster-affected nodes.

        Args:
            numero_de_caminhos: Number of alternative paths to compute
            node_desastre: Node identifier that will fail during disaster

        """
        topologia_desastre = self.topology.copy()
        topologia_desastre.remove_node(node_desastre)
        print("node_desastre", node_desastre)
        for node1 in self.topology.nodes():
            self.caminhos_mais_curtos_entre_links_durante_desastre[int(node1)] = {}
            for node2 in self.topology.nodes():
                self.caminhos_mais_curtos_entre_links_durante_desastre[int(node1)][
                    int(node2)
                ] = []
                if node1 in (node2, node_desastre) or node2 == node_desastre:
                    continue
                caminhos_mais_curtos_entre_i_e_j_desastre = self.__k_shortest_paths(
                    topologia_desastre,
                    node1,
                    node2,
                    numero_de_caminhos,
                    weight="weight",
                )
                informacoes_caminhos_mais_curtos_entre_i_e_j_desastre = []

                for caminho in caminhos_mais_curtos_entre_i_e_j_desastre:
                    distancia = self.distancia_caminho(caminho)
                    fator_de_modulacao = self.__fator_de_modulacao(distancia)
                    informacoes_caminhos_mais_curtos_entre_i_e_j_desastre.append(
                        {
                            "caminho": caminho,
                            "distancia": distancia,
                            "fator_de_modulacao": fator_de_modulacao,
                        }
                    )

                self.caminhos_mais_curtos_entre_links_durante_desastre[int(node1)][
                    int(node2)
                ] = informacoes_caminhos_mais_curtos_entre_i_e_j_desastre

    def __k_shortest_paths(
        self, graph: nx.Graph, source, target, k, weight="weight"
    ) -> list:
        """Compute k shortest paths between source and target nodes.

        Args:
            graph: NetworkX graph to search
            source: Source node identifier
            target: Target node identifier
            k: Number of shortest paths to find
            weight: Edge attribute to use as weight

        Returns:
            list: List of k shortest paths as node sequences

        """
        return list(
            islice(nx.shortest_simple_paths(graph, source, target, weight=weight), k)
        )

    def desalocate(self, path, spectro) -> None:
        """Immediately deallocate frequency slots along a path.

        Args:
            path: List of nodes representing the path
            spectro: Tuple of (start_slot, end_slot) to deallocate

        """
        for i in range(0, (len(path) - 1)):
            for slot in range(spectro[0], spectro[1] + 1):
                self.topology[path[i]][path[i + 1]]["slots"][slot] = 0

    def desaloca_janela(
        self, path, spectro, holding_time, env: simpy.Environment
    ) -> Generator:
        """Deallocate frequency slots after holding time expires.

        Args:
            path: List of nodes representing the path
            spectro: Tuple of (start_slot, end_slot) to deallocate
            holding_time: Duration to hold the allocation
            env: SimPy simulation environment

        Yields:
            Generator: SimPy timeout events

        """
        try:
            yield env.timeout(holding_time)
            self.desalocate(path, spectro)

        except simpy.Interrupt:
            self.desalocate(path, spectro)

    def aloca_janela(self, path, spectro) -> None:
        """Allocate frequency slots along a path.

        Args:
            path: List of nodes representing the path
            spectro: Tuple of (start_slot, end_slot) to allocate

        """
        inicio = spectro[0]
        fim = spectro[1]
        for i in range(0, len(path) - 1):
            for slot in range(inicio, fim + 1):
                self.topology[path[i]][path[i + 1]]["slots"][slot] = 1

    def distancia_caminho(self, path) -> int:
        """Calculate total distance of a path.

        Args:
            path: List of nodes representing the path

        Returns:
            int: Total distance in kilometers

        """
        soma = 0
        for i in range(0, (len(path) - 1)):
            soma += self.topology[path[i]][path[i + 1]]["weight"]
        return soma

    def caminho_passa_por_link(self, ponto_a, ponto_b, caminho) -> bool:
        """Check if path traverses a specific link.

        Args:
            ponto_a: First endpoint of the link
            ponto_b: Second endpoint of the link
            caminho: List of nodes representing the path

        Returns:
            bool: True if path uses the specified link

        """
        return any(
            (
                caminho[index] == ponto_a
                and caminho[index + 1]
                or caminho[index] == ponto_b
                and caminho[index + 1] == ponto_b
            )
            for index in range(len(caminho) - 1)
        )

    def caminho_em_funcionamento(self, caminho) -> bool:
        """Check if all links in a path are operational.

        Args:
            caminho: List of nodes representing the path

        Returns:
            bool: True if all links are functional, False otherwise

        """
        return not any(
            self.topology[caminho[i]][caminho[i + 1]]["failed"]
            for i in range(len(caminho) - 1)
        )

    def pode_passar_pelo_caminho_que_vai_falhar(self, caminho) -> bool:
        """Check if path can be used despite upcoming link failures.

        Args:
            caminho: List of nodes representing the path

        Returns:
            bool: True if path is usable, False if blocked by failures

        """
        caminho_inicia_ou_termina_no_node_desastre = (
            caminho[0] == self.desastre.list_of_dict_node_per_start_time[0]["node"]
            or caminho[-1] == self.desastre.list_of_dict_node_per_start_time[0]["node"]
        )
        return (
            not any(
                self.topology[caminho[i]][caminho[i + 1]]["vai falhar"]
                for i in range(len(caminho) - 1)
            )
            or caminho_inicia_ou_termina_no_node_desastre
        )

    def __fator_de_modulacao(self, distancia) -> float:
        """Calculate modulation factor based on transmission distance.

        Args:
            distancia: Transmission distance in kilometers

        Returns:
            float: Modulation factor (spectral efficiency × slot size)

        """
        if distancia <= DISTANCIA_MODULACAO_4:
            return float(FATOR_MODULACAO_4 * SLOT_SIZE)
        if DISTANCIA_MODULACAO_4 < distancia <= DISTANCIA_MODULACAO_3:
            return float(FATOR_MODULACAO_3 * SLOT_SIZE)
        if DISTANCIA_MODULACAO_3 < distancia <= DISTANCIA_MODULACAO_2:
            return float(FATOR_MODULACAO_2 * SLOT_SIZE)
        return float(FATOR_MODULACAO_1 * SLOT_SIZE)
