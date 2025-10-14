"""Path management utilities for EON simulation.

This module provides centralized path computation and management functionality
that can be used across different components (Topology, ISP, etc.).
"""

from itertools import islice

import networkx as nx
from simulador.variaveis import (
    DISTANCIA_MODULACAO_2,
    DISTANCIA_MODULACAO_3,
    DISTANCIA_MODULACAO_4,
    FATOR_MODULACAO_1,
    FATOR_MODULACAO_2,
    FATOR_MODULACAO_3,
    FATOR_MODULACAO_4,
    SLOT_SIZE,
)


class PathManager:
    """Centralized path computation and management for network routing."""

    @staticmethod
    def k_shortest_paths(
        graph: nx.Graph, source: int, target: int, k: int, weight: str = "weight"
    ) -> list[list[int]]:
        """Compute k shortest paths between source and target.

        Args:
            graph: NetworkX graph
            source: Source node
            target: Target node
            k: Number of paths to find
            weight: Edge weight attribute name

        Returns:
            list[list[int]]: List of k shortest paths as node sequences
        """
        try:
            paths_generator = nx.shortest_simple_paths(
                graph, source, target, weight=weight
            )
            return list(islice(paths_generator, k))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    @staticmethod
    def calculate_path_distance(graph: nx.Graph, path: list[int]) -> float:
        """Calculate total distance of a path.

        Args:
            graph: NetworkX graph containing edge weights
            path: List of nodes representing the path

        Returns:
            float: Total distance of the path
        """
        total_distance = 0.0
        for i in range(len(path) - 1):
            if graph.has_edge(path[i], path[i + 1]):
                total_distance += graph[path[i]][path[i + 1]]["weight"]
        return total_distance

    @staticmethod
    def calculate_modulation_factor(
        distance: float, include_slot_size: bool = False
    ) -> float:
        """Calculate modulation factor based on distance.

        Args:
            distance: Path distance
            include_slot_size: If True, multiply by SLOT_SIZE for bandwidth calculations

        Returns:
            float: Modulation factor for the given distance
        """
        if distance <= DISTANCIA_MODULACAO_4:
            factor = FATOR_MODULACAO_4
        elif distance <= DISTANCIA_MODULACAO_3:
            factor = FATOR_MODULACAO_3
        elif distance <= DISTANCIA_MODULACAO_2:
            factor = FATOR_MODULACAO_2
        else:
            factor = FATOR_MODULACAO_1

        if include_slot_size:
            return float(factor * SLOT_SIZE)

        return factor

    @staticmethod
    def compute_paths_between_nodes(
        graph: nx.Graph, source: int, target: int, k: int = 3, weight: str = "weight"
    ) -> list[dict]:
        """Compute paths with full information between two nodes.

        Args:
            graph: NetworkX graph
            source: Source node
            target: Target node
            k: Number of alternative paths to compute
            weight: Edge weight attribute name

        Returns:
            list[dict]: List of path information dictionaries containing:
                - caminho: List of nodes in the path
                - distancia: Total distance of the path
                - fator_de_modulacao: Modulation factor for the path
        """
        paths = PathManager.k_shortest_paths(graph, source, target, k, weight)
        path_info_list = []

        for path in paths:
            distance = PathManager.calculate_path_distance(graph, path)
            modulation_factor = PathManager.calculate_modulation_factor(distance)

            path_info_list.append(
                {
                    "caminho": path,
                    "distancia": distance,
                    "fator_de_modulacao": modulation_factor,
                }
            )

        return path_info_list

    @staticmethod
    def precompute_all_pairs_paths(
        graph: nx.Graph,
        nodes: list[int] | None = None,
        k: int = 3,
        weight: str = "weight",
    ) -> dict[int, dict[int, list[dict]]]:
        """Precompute paths between all pairs of nodes.

        Args:
            graph: NetworkX graph
            nodes: List of nodes to compute paths for (if None, uses all graph nodes)
            k: Number of alternative paths to compute per node pair
            weight: Edge weight attribute name

        Returns:
            dict: Nested dictionary with structure [source][destination] = path_info_list
        """
        if nodes is None:
            nodes = list(graph.nodes())

        all_paths = {}

        for source in nodes:
            all_paths[source] = {}

            for target in nodes:
                if source == target:
                    continue

                all_paths[source][target] = PathManager.compute_paths_between_nodes(
                    graph, source, target, k, weight
                )

        return all_paths

    @staticmethod
    def filter_paths_by_nodes(
        paths_dict: dict[int, dict[int, list[dict]]], valid_nodes: set[int]
    ) -> dict[int, dict[int, list[dict]]]:
        """Filter precomputed paths to only include those using valid nodes.

        Args:
            paths_dict: Precomputed paths dictionary
            valid_nodes: Set of nodes that are allowed in paths

        Returns:
            dict: Filtered paths dictionary with same structure
        """
        filtered_paths = {}

        for source, target_dict in paths_dict.items():
            if source not in valid_nodes:
                continue

            filtered_paths[source] = {}

            for target, path_list in target_dict.items():
                if target not in valid_nodes:
                    continue

                # Filter paths to only include those with all nodes in valid_nodes
                valid_path_list = []
                for path_info in path_list:
                    path = path_info["caminho"]
                    if all(node in valid_nodes for node in path):
                        valid_path_list.append(path_info)

                if valid_path_list:
                    filtered_paths[source][target] = valid_path_list

        return filtered_paths

    @staticmethod
    def create_subgraph_with_nodes_and_edges(
        graph: nx.Graph, nodes: list[int], edges: list[tuple[int, int]]
    ) -> nx.Graph:
        """Create a subgraph with specified nodes and edges.

        Args:
            graph: Original graph
            nodes: List of nodes to include
            edges: List of edges to ensure are included

        Returns:
            nx.Graph: Subgraph containing specified nodes and edges
        """
        # Create subgraph with specified nodes
        subgraph = graph.subgraph(nodes).copy()

        # Ensure all specified edges are included
        for edge in edges:
            if (
                edge[0] in nodes
                and edge[1] in nodes
                and graph.has_edge(edge[0], edge[1])
                and not subgraph.has_edge(edge[0], edge[1])
            ):
                # Add edge with data from original graph
                edge_data = graph[edge[0]][edge[1]].copy()
                subgraph.add_edge(edge[0], edge[1], **edge_data)

        return subgraph

    @staticmethod
    def get_paths_between_nodes(
        paths_dict: dict[int, dict[int, list[dict]]], source: int, target: int
    ) -> list[dict]:
        """Get precomputed paths between two specific nodes.

        Args:
            paths_dict: Precomputed paths dictionary
            source: Source node
            target: Target node

        Returns:
            list[dict]: List of path information, empty if no paths exist
        """
        if source in paths_dict and target in paths_dict[source]:
            return paths_dict[source][target]
        return []

    @staticmethod
    def has_paths_between_nodes(
        paths_dict: dict[int, dict[int, list[dict]]], source: int, target: int
    ) -> bool:
        """Check if precomputed paths exist between two nodes.

        Args:
            paths_dict: Precomputed paths dictionary
            source: Source node
            target: Target node

        Returns:
            bool: True if paths exist, False otherwise
        """
        return (
            source in paths_dict
            and target in paths_dict[source]
            and len(paths_dict[source][target]) > 0
        )
