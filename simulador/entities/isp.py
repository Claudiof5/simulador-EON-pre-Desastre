"""ISP (Internet Service Provider) management for EON simulation.

This module contains the ISP class that represents an Internet Service Provider
with its own nodes, edges, datacenters, and routing strategies.
"""

from __future__ import annotations

from collections.abc import Generator
from itertools import islice
from typing import TYPE_CHECKING

import networkx as nx

from simulador.config.settings import (
    ALPHA,
    DISTANCIA_MODULACAO_2,
    DISTANCIA_MODULACAO_3,
    DISTANCIA_MODULACAO_4,
    FATOR_MODULACAO_1,
    FATOR_MODULACAO_2,
    FATOR_MODULACAO_3,
    FATOR_MODULACAO_4,
)
from simulador.routing import weights
from simulador.routing.base import RoutingBase
from simulador.routing.subnet import FirstFitSubnet

if TYPE_CHECKING:
    from simulador.entities.datacenter import Datacenter
    from simulador.entities.disaster import Disaster
    from simulador.main import Simulator


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
        roteamento_de_desastre: type[RoutingBase] | None = None,
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
        # In subnet architecture, primary routing is subnet-based
        self.roteamento_atual: type[RoutingBase] = FirstFitSubnet
        self.roteamento_primario: type[RoutingBase] = FirstFitSubnet
        # If no disaster routing specified, use subnet routing
        self.roteamento_desastre: type[RoutingBase] = (
            roteamento_de_desastre
            if roteamento_de_desastre is not None
            else FirstFitSubnet
        )
        self.datacenter: Datacenter | None = None

        # Precomputed paths within the ISP
        self.caminhos_internos_isp: dict[int, dict[int, list[dict]]] = {}

        # Disaster-aware paths within the ISP
        self.caminhos_internos_isp_durante_desastre: dict[
            int, dict[int, list[dict]]
        ] = {}
        self.weighted_caminhos_internos_isp_durante_desastre: dict[
            int, dict[int, list[dict]]
        ] = {}

    def define_datacenter(
        self, disaster: Disaster, topology: nx.Graph, specific_values=None
    ) -> None:
        from simulador.generators.datacenter_generator import DatacenterGenerator

        self.datacenter = DatacenterGenerator.gerar_datacenter(
            disaster, topology, self.nodes, specific_values
        )

    def iniciar_migracao(self, simulador: Simulator) -> Generator:
        """Start migration process and switch ISP routing at appropriate times.

        This manages:
        1. Switching to disaster routing at migration reaction time
        2. Starting datacenter migration (only if runtime migration is enabled)
        3. Switching back to primary routing after disaster ends
        """
        if self.datacenter is None:
            return

        # Wait until reaction time, then switch to disaster routing
        yield simulador.env.timeout(self.datacenter.tempo_de_reacao - simulador.env.now)
        self.roteamento_atual = self.roteamento_desastre

        # Only start datacenter migration if using runtime mode (no pre-generated requests)
        # When lista_de_requisicoes is provided, migration requests are pre-generated
        if simulador.lista_de_requisicoes is None:
            self.datacenter.iniciar_migracao(simulador, self)

        # After disaster ends, switch back to primary routing
        yield simulador.env.timeout(
            (simulador.desastre.start + simulador.desastre.duration) - simulador.env.now
        )
        self.roteamento_atual = self.roteamento_primario

    def imprime_isp(self) -> None:
        print("ISP: ", self.isp_id)
        print("Nós: ", self.nodes)
        print("Arestas: ", self.edges)
        if self.datacenter is not None:
            print("Datacenter source: ", self.datacenter.source)
            print("Datacenter destination: ", self.datacenter.destination)

    def troca_roteamento_desastre(self, roteamento: type[RoutingBase]) -> None:
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
        self,
        topology: nx.Graph,
        node_desastre: int,
        numero_de_caminhos: int = 10,
        lista_de_isps: list[ISP] | None = None,
        weights_by_link_by_isp: dict | None = None,
    ) -> None:
        """Compute disaster-aware shortest paths between all ISP nodes.

        For traffic from/to the disaster node itself, use regular paths (no avoidance).
        For traffic between other nodes (migration traffic), avoid the disaster node.

        Args:
            topology: Network topology graph
            node_desastre: Node that will fail during disaster
            numero_de_caminhos: Number of alternative paths to compute per node pair
            lista_de_isps: Optional list of all ISPs (for weight calculation)
            weights_by_link_by_isp: Optional precomputed weights by ISP
        """
        # Create two subgraphs:
        # 1. Full ISP subgraph (for traffic from/to disaster node)
        isp_subgraph_full = self._criar_subgrafo_isp(topology)

        # 2. Disaster-aware ISP subgraph (for migration traffic avoiding disaster node)
        isp_subgraph_disaster_aware = isp_subgraph_full.copy()
        if node_desastre in self.nodes and isp_subgraph_disaster_aware.has_node(
            node_desastre
        ):
            isp_subgraph_disaster_aware.remove_node(node_desastre)

        # Initialize the disaster paths dictionary
        self.caminhos_internos_isp_durante_desastre = {}
        self.weighted_caminhos_internos_isp_durante_desastre = {}

        # Create weighted graphs if weights are provided
        weighted_isp_subgraph_full = None
        weighted_isp_subgraph_disaster_aware = None

        if weights_by_link_by_isp is not None:
            weighted_isp_subgraph_full = weights.create_weighted_graph(
                isp_subgraph_full, self.isp_id, weights_by_link_by_isp
            )
            weighted_isp_subgraph_disaster_aware = weights.create_weighted_graph(
                isp_subgraph_disaster_aware, self.isp_id, weights_by_link_by_isp
            )
        elif lista_de_isps is not None:
            # Calculate weights if list of ISPs is provided
            weights_by_link_by_isp = weights.calculate_isp_usage_weights(
                lista_de_isps, ALPHA
            )
            weighted_isp_subgraph_full = weights.create_weighted_graph(
                isp_subgraph_full, self.isp_id, weights_by_link_by_isp
            )
            weighted_isp_subgraph_disaster_aware = weights.create_weighted_graph(
                isp_subgraph_disaster_aware, self.isp_id, weights_by_link_by_isp
            )

        # Compute paths for all node pairs
        for src_node in self.nodes:
            self.caminhos_internos_isp_durante_desastre[src_node] = {}
            self.weighted_caminhos_internos_isp_durante_desastre[src_node] = {}

            for dst_node in self.nodes:
                if src_node == dst_node:
                    continue

                # Determine which graph to use:
                # - If traffic is from/to disaster node, use full graph (no avoidance)
                # - Otherwise, use disaster-aware graph (avoid disaster node)
                is_disaster_traffic = node_desastre in (src_node, dst_node)

                if is_disaster_traffic:
                    # Traffic from/to disaster node: use full graph
                    subgraph_to_use = isp_subgraph_full
                    weighted_subgraph_to_use = weighted_isp_subgraph_full
                else:
                    # Migration traffic: avoid disaster node
                    subgraph_to_use = isp_subgraph_disaster_aware
                    weighted_subgraph_to_use = weighted_isp_subgraph_disaster_aware

                # Compute k shortest paths
                caminhos = self._k_shortest_paths_isp(
                    subgraph_to_use, src_node, dst_node, numero_de_caminhos
                )

                # Compute weighted paths if weighted graph is available
                if weighted_subgraph_to_use is not None:
                    weighted_caminhos = self._k_shortest_paths_isp(
                        weighted_subgraph_to_use, src_node, dst_node, numero_de_caminhos
                    )
                else:
                    # Use same paths as unweighted if no weights available
                    weighted_caminhos = caminhos

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

                informacoes_caminhos_weighted = []
                for caminho in weighted_caminhos:
                    distancia = self._calcular_distancia_caminho(topology, caminho)
                    fator_modulacao = self._calcular_fator_modulacao(distancia)
                    informacoes_caminhos_weighted.append(
                        {
                            "caminho": caminho,
                            "distancia": distancia,
                            "fator_de_modulacao": fator_modulacao,
                        }
                    )
                self.weighted_caminhos_internos_isp_durante_desastre[src_node][
                    dst_node
                ] = informacoes_caminhos_weighted

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
        self,
        src: int,
        dst: int,
        is_weighted: bool = False,
    ) -> list[dict]:
        """Get precomputed disaster-aware paths between two nodes within the ISP.

        Args:
            src: Source node
            dst: Destination node
            is_weighted: If True, return weighted paths

        Returns:
            list[dict]: List of disaster-aware path information dictionaries
        """
        if is_weighted:
            return self.weighted_caminhos_internos_isp_durante_desastre[src][dst]

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
