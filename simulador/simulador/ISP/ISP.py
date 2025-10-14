"""ISP (Internet Service Provider) management for EON simulation.

This module contains the ISP class that represents an Internet Service Provider
with its own nodes, edges, datacenters, and routing strategies.
"""

from collections.abc import Generator
from itertools import islice
from typing import TYPE_CHECKING

import networkx as nx
from simulador.Datacenter.Datacenter import Datacenter
from simulador.Datacenter.GeradorDeDatacenter import GeradorDeDatacenter
from simulador.Roteamento.IRoteamento import IRoteamento
from simulador.Roteamento.Roteamento import Roteamento
from simulador.variaveis import (
    DISTANCIA_MODULACAO_2,
    DISTANCIA_MODULACAO_3,
    DISTANCIA_MODULACAO_4,
    FATOR_MODULACAO_1,
    FATOR_MODULACAO_2,
    FATOR_MODULACAO_3,
    FATOR_MODULACAO_4,
)

if TYPE_CHECKING:
    from simulador.Desastre.Desastre import Desastre

    from simulador.simulador import Simulador


class ISP:
    """Internet Service Provider class for network simulation.

    Manages ISP-specific resources including nodes, edges, datacenters,
    routing policies, and precomputed paths within the ISP's network.
    """

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

        # Precomputed paths within the ISP
        self.caminhos_internos_isp: dict[int, dict[int, list[dict]]] = {}

        # Disaster-aware paths within the ISP
        self.caminhos_internos_isp_durante_desastre: dict[
            int, dict[int, list[dict]]
        ] = {}

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
        """Change the disaster routing method.

        Args:
            roteamento: New routing method for disaster scenarios
        """
        self.roteamento_desastre = roteamento

    def computar_caminhos_internos(
        self, topology: nx.Graph, numero_de_caminhos: int = 3
    ) -> None:
        """Compute shortest paths between all ISP nodes.

        Args:
            topology: Network topology graph
            numero_de_caminhos: Number of alternative paths to compute per node pair
        """
        # Create subgraph with only ISP nodes and edges
        isp_subgraph = self._criar_subgrafo_isp(topology)

        # Initialize the paths dictionary
        self.caminhos_internos_isp = {}

        for src_node in self.nodes:
            self.caminhos_internos_isp[src_node] = {}

            for dst_node in self.nodes:
                if src_node == dst_node:
                    continue

                # Compute k shortest paths within ISP
                caminhos = self._k_shortest_paths_isp(
                    isp_subgraph, src_node, dst_node, numero_de_caminhos
                )

                # Store paths with additional information
                informacoes_caminhos = []
                for caminho in caminhos:
                    distancia = self._calcular_distancia_caminho(topology, caminho)
                    fator_modulacao = self._calcular_fator_modulacao(distancia)

                    informacoes_caminhos.append(
                        {
                            "caminho": caminho,
                            "distancia": distancia,
                            "fator_de_modulacao": fator_modulacao,
                        }
                    )

                self.caminhos_internos_isp[src_node][dst_node] = informacoes_caminhos

    def computar_caminhos_internos_durante_desastre(
        self, topology: nx.Graph, node_desastre: int, numero_de_caminhos: int = 3
    ) -> None:
        """Compute disaster-aware shortest paths between all ISP nodes.

        Args:
            topology: Network topology graph
            node_desastre: Node that will fail during disaster
            numero_de_caminhos: Number of alternative paths to compute per node pair
        """
        # Create disaster-aware ISP subgraph by removing disaster node
        isp_subgraph = self._criar_subgrafo_isp(topology)

        # Remove disaster node if it belongs to this ISP
        if node_desastre in self.nodes and isp_subgraph.has_node(node_desastre):
            isp_subgraph.remove_node(node_desastre)

        # Initialize the disaster paths dictionary
        self.caminhos_internos_isp_durante_desastre = {}

        # Get available nodes (excluding disaster node)
        available_nodes = [node for node in self.nodes if node != node_desastre]

        for src_node in available_nodes:
            self.caminhos_internos_isp_durante_desastre[src_node] = {}

            for dst_node in available_nodes:
                if src_node == dst_node:
                    continue

                # Compute k shortest paths within ISP avoiding disaster node
                caminhos = self._k_shortest_paths_isp(
                    isp_subgraph, src_node, dst_node, numero_de_caminhos
                )

                # Store paths with additional information
                informacoes_caminhos = []
                for caminho in caminhos:
                    distancia = self._calcular_distancia_caminho(topology, caminho)
                    fator_modulacao = self._calcular_fator_modulacao(distancia)

                    informacoes_caminhos.append(
                        {
                            "caminho": caminho,
                            "distancia": distancia,
                            "fator_de_modulacao": fator_modulacao,
                        }
                    )

                self.caminhos_internos_isp_durante_desastre[src_node][dst_node] = (
                    informacoes_caminhos
                )

        # Initialize empty paths for disaster node connections
        for node in self.nodes:
            if node not in self.caminhos_internos_isp_durante_desastre:
                self.caminhos_internos_isp_durante_desastre[node] = {}

            # Ensure all node pairs have an entry (empty if involving disaster node)
            for target_node in self.nodes:
                if target_node not in self.caminhos_internos_isp_durante_desastre[node]:
                    self.caminhos_internos_isp_durante_desastre[node][target_node] = []

    def _criar_subgrafo_isp(self, topology: nx.Graph) -> nx.Graph:
        """Create a subgraph containing only ISP nodes and edges.

        Args:
            topology: Full network topology

        Returns:
            nx.Graph: Subgraph with only ISP nodes and edges
        """
        # Create subgraph with ISP nodes
        isp_subgraph = topology.subgraph(self.nodes).copy()

        # Ensure all ISP edges are included (some might be between non-ISP nodes)
        for edge in self.edges:
            if (
                edge[0] in self.nodes
                and edge[1] in self.nodes
                and not isp_subgraph.has_edge(edge[0], edge[1])
                and topology.has_edge(edge[0], edge[1])
            ):
                edge_data = topology[edge[0]][edge[1]].copy()
                isp_subgraph.add_edge(edge[0], edge[1], **edge_data)

        return isp_subgraph

    def _k_shortest_paths_isp(
        self, graph: nx.Graph, source: int, target: int, k: int
    ) -> list[list[int]]:
        """Compute k shortest paths between source and target within ISP.

        Args:
            graph: ISP subgraph
            source: Source node
            target: Target node
            k: Number of paths to find

        Returns:
            list[list[int]]: List of k shortest paths
        """
        try:
            paths_generator = nx.shortest_simple_paths(
                graph, source, target, weight="weight"
            )
            # Return up to k paths
            return list(islice(paths_generator, k))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # No path exists between source and target
            return []

    def _calcular_distancia_caminho(
        self, topology: nx.Graph, caminho: list[int]
    ) -> float:
        """Calculate total distance of a path.

        Args:
            topology: Network topology
            caminho: List of nodes representing the path

        Returns:
            float: Total distance of the path
        """
        distancia_total = 0.0
        for i in range(len(caminho) - 1):
            if topology.has_edge(caminho[i], caminho[i + 1]):
                distancia_total += topology[caminho[i]][caminho[i + 1]]["weight"]
        return distancia_total

    def _calcular_fator_modulacao(self, distancia: float) -> float:
        """Calculate modulation factor based on distance.

        Args:
            distancia: Path distance

        Returns:
            float: Modulation factor
        """
        if distancia <= DISTANCIA_MODULACAO_4:
            return FATOR_MODULACAO_4
        if distancia <= DISTANCIA_MODULACAO_3:
            return FATOR_MODULACAO_3
        if distancia <= DISTANCIA_MODULACAO_2:
            return FATOR_MODULACAO_2
        return FATOR_MODULACAO_1

    def get_caminhos_entre_nodes(self, src: int, dst: int) -> list[dict]:
        """Get precomputed paths between two nodes within the ISP.

        Args:
            src: Source node
            dst: Destination node

        Returns:
            list[dict]: List of path information dictionaries
        """
        if src in self.caminhos_internos_isp and dst in self.caminhos_internos_isp[src]:
            return self.caminhos_internos_isp[src][dst]
        return []

    def tem_caminho_interno(self, src: int, dst: int) -> bool:
        """Check if there are precomputed paths between two nodes.

        Args:
            src: Source node
            dst: Destination node

        Returns:
            bool: True if paths exist, False otherwise
        """
        return (
            src in self.caminhos_internos_isp
            and dst in self.caminhos_internos_isp[src]
            and len(self.caminhos_internos_isp[src][dst]) > 0
        )

    def get_caminhos_entre_nodes_durante_desastre(
        self, src: int, dst: int
    ) -> list[dict]:
        """Get precomputed disaster-aware paths between two nodes within the ISP.

        Args:
            src: Source node
            dst: Destination node

        Returns:
            list[dict]: List of disaster-aware path information dictionaries
        """
        if (
            src in self.caminhos_internos_isp_durante_desastre
            and dst in self.caminhos_internos_isp_durante_desastre[src]
        ):
            return self.caminhos_internos_isp_durante_desastre[src][dst]
        return []

    def tem_caminho_interno_durante_desastre(self, src: int, dst: int) -> bool:
        """Check if there are precomputed disaster-aware paths between two nodes.

        Args:
            src: Source node
            dst: Destination node

        Returns:
            bool: True if disaster-aware paths exist, False otherwise
        """
        return (
            src in self.caminhos_internos_isp_durante_desastre
            and dst in self.caminhos_internos_isp_durante_desastre[src]
            and len(self.caminhos_internos_isp_durante_desastre[src][dst]) > 0
        )
