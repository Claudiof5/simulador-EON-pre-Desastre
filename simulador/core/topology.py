"""Network topology management for EON simulation.

Contains the Topology class that manages the network topology including:
- Network graph structure and slot allocation
- Shortest path calculations for routing
- ISP assignment to nodes and edges
- Disaster-aware path computation
- Resource allocation and deallocation
"""

from collections.abc import Generator
from typing import TYPE_CHECKING

import networkx as nx
import simpy

from simulador.core.path_manager import PathManager
from simulador.entities.isp import ISP

if TYPE_CHECKING:
    from simulador.entities.disaster import Disaster


class Topology:
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
        self.lista_de_isps: list[ISP] = list_of_isp
        self.numero_de_slots = numero_de_slots
        self.caminhos_mais_curtos_entre_links: dict[int, dict[int, list[dict]]] = {}
        self.caminhos_mais_curtos_entre_links_durante_desastre: dict[
            int, dict[int, list[dict]]
        ] = {}
        self.desastre: Disaster | None = None
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
                self.topology.nodes[node]["ISPs"].append(isp.isp_id)

            for edge in isp.edges:
                self.topology[edge[0]][edge[1]]["ISPs"].append(isp.isp_id)

    def __inicia_caminhos_mais_curtos(self, numero_de_caminhos: int) -> None:
        """Precompute shortest paths between all node pairs using PathManager.

        Args:
            numero_de_caminhos: Number of alternative paths to compute

        """
        self.caminhos_mais_curtos_entre_links = PathManager.precompute_all_pairs_paths(
            self.topology, k=numero_de_caminhos
        )

    def inicia_caminhos_mais_curtos_durante_desastre(
        self, numero_de_caminhos: int, node_desastre: int
    ) -> None:
        """Compute shortest paths excluding disaster-affected nodes using PathManager.

        Args:
            numero_de_caminhos: Number of alternative paths to compute
            node_desastre: Node identifier that will fail during disaster

        """
        # Create disaster topology by removing the affected node
        topologia_desastre = self.topology.copy()
        topologia_desastre.remove_node(node_desastre)

        print("node_desastre", node_desastre)

        # Get all nodes except the disaster node
        available_nodes = [
            node for node in self.topology.nodes() if node != node_desastre
        ]

        # Compute all pairs paths on disaster topology using PathManager
        self.caminhos_mais_curtos_entre_links_durante_desastre = (
            PathManager.precompute_all_pairs_paths(
                topologia_desastre, available_nodes, numero_de_caminhos
            )
        )

        # Initialize empty paths for disaster node connections
        for node in self.topology.nodes():
            if int(node) not in self.caminhos_mais_curtos_entre_links_durante_desastre:
                self.caminhos_mais_curtos_entre_links_durante_desastre[int(node)] = {}

            # Ensure all node pairs have an entry (empty if involving disaster node)
            for target_node in self.topology.nodes():
                if (
                    int(target_node)
                    not in self.caminhos_mais_curtos_entre_links_durante_desastre[
                        int(node)
                    ]
                ):
                    self.caminhos_mais_curtos_entre_links_durante_desastre[int(node)][
                        int(target_node)
                    ] = []

    def distancia_caminho(self, caminho: list[int]) -> float:
        """Calculate total distance of a path using PathManager.

        Args:
            caminho: List of nodes representing the path

        Returns:
            float: Total distance of the path

        """
        return PathManager.calculate_path_distance(self.topology, caminho)

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
        if not self.desastre:
            return False
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
        """Calculate modulation factor based on transmission distance using PathManager.

        Args:
            distancia: Transmission distance in kilometers

        Returns:
            float: Modulation factor (spectral efficiency × slot size)

        """
        return PathManager.calculate_modulation_factor(
            distancia, include_slot_size=True
        )
