"""Network topology analysis for disaster scenario evaluation.

This module provides utilities for analyzing network topologies to identify
critical disaster points and evaluate network partitioning scenarios.
"""

from __future__ import annotations

import networkx as nx


def find_balanced_min_cut(graph: nx.Graph) -> dict:
    """Find minimum cut that creates most balanced network partitions.

    Analyzes all possible source-sink pairs to find the minimum cut that
    results in the most balanced partition of the network.

    Args:
        graph: Network topology as NetworkX graph

    Returns:
        Dictionary containing:
            - partitions: List of partition data dictionaries
            - min_cut_value: Minimum number of edges to cut
            - min_size_difference: Size difference between partitions
    """

    def _recover_partition_data(partition, graph: nx.Graph) -> dict:
        """Extract partition details from minimum cut result."""
        reachable, non_reachable = partition
        cut_edges = [
            (u, v)
            for u, v in graph.edges()
            if (u in reachable and v in non_reachable)
            or (v in reachable and u in non_reachable)
        ]
        return {
            "partition_1": (
                reachable if len(reachable) < len(non_reachable) else non_reachable
            ),
            "partition_2": (
                non_reachable if len(reachable) < len(non_reachable) else reachable
            ),
            "cut_edges": cut_edges,
        }

    # Set default capacities if missing
    for u, v in graph.edges():
        if "capacity" not in graph[u][v]:
            graph[u][v]["capacity"] = 1

    best_cut_value = float("inf")
    best_size_difference = float("inf")
    best_partitions_set = set()

    # Iterate over all pairs of nodes as source (s) and sink (t)
    for s in graph.nodes():
        for t in graph.nodes():
            if s == t:
                continue

            if not nx.has_path(graph, s, t):
                continue

            try:
                cut_value, partition = nx.minimum_cut(graph, s, t)
                reachable, non_reachable = partition

                size_difference = abs(len(reachable) - len(non_reachable))
                partition_frozen = frozenset(
                    (frozenset(reachable), frozenset(non_reachable))
                )

                if cut_value < best_cut_value or (
                    cut_value == best_cut_value
                    and size_difference < best_size_difference
                ):
                    best_cut_value = cut_value
                    best_size_difference = size_difference
                    best_partitions_set = {partition_frozen}

                elif (
                    cut_value == best_cut_value
                    and size_difference == best_size_difference
                ):
                    best_partitions_set.add(partition_frozen)

            except nx.NetworkXUnbounded:
                print(f"Unbounded flow for source {s} and sink {t}, skipping.")

    results = []
    for partition in best_partitions_set:
        partition_data = _recover_partition_data(partition, graph)
        results.append(partition_data)

    return {
        "partitions": results,
        "min_cut_value": best_cut_value,
        "min_size_difference": best_size_difference,
    }


def remove_node_from_graph(graph: nx.Graph, nodes: list[int]) -> nx.Graph:
    """Create a copy of graph with specified nodes removed.

    Args:
        graph: Original network topology
        nodes: List of node IDs to remove

    Returns:
        New graph with nodes removed
    """
    graph_copy = graph.copy()
    graph_copy.remove_nodes_from(nodes)
    return graph_copy


def find_balanced_min_cut_for_all_nodes(topology: nx.Graph) -> list[dict]:
    """Analyze impact of removing each node on network partitioning.

    For each node in the topology, removes it and calculates the resulting
    minimum balanced cut. Results are sorted by partition size difference.

    Args:
        topology: Network topology to analyze

    Returns:
        List of dictionaries, each containing:
            - node: ID of removed node
            - partitions: Resulting partition data
            - min_cut_value: Minimum cut value
            - min_size_difference: Size difference between partitions
    """
    dados = []
    for node in topology.nodes():
        copy_graph = remove_node_from_graph(topology, [node])
        dado = find_balanced_min_cut(copy_graph)
        dado["node"] = node
        dados.append(dado)

    dados.sort(key=lambda x: x["min_size_difference"])
    return dados


def find_critical_disaster_node(
    topology: nx.Graph, size_diff_threshold: int | None = None
) -> tuple[int, dict]:
    """Identify the node whose failure causes worst-case network partition.

    Args:
        topology: Network topology to analyze
        size_diff_threshold: Optional threshold to filter results

    Returns:
        Tuple of (node_id, partition_info) for the critical node
    """
    results = find_balanced_min_cut_for_all_nodes(topology)

    if size_diff_threshold is not None:
        results = [
            r for r in results if r["min_size_difference"] <= size_diff_threshold
        ]

    if not results:
        raise ValueError("No nodes found matching criteria")

    critical = results[0]
    return critical["node"], critical


def get_disaster_components(
    topology: nx.Graph, disaster_node: int
) -> tuple[set, set, list[tuple[int, int]]]:
    """Get network components and critical edges for a disaster node.

    Args:
        topology: Network topology
        disaster_node: Node that fails

    Returns:
        Tuple of (component_1, component_2, critical_edges)
    """
    _, info = find_critical_disaster_node(topology)
    if info["node"] != disaster_node:
        # Recalculate for specific node
        graph_without_node = remove_node_from_graph(topology, [disaster_node])
        info = find_balanced_min_cut(graph_without_node)
        info["node"] = disaster_node

    partition = info["partitions"][0]
    return (
        partition["partition_1"],
        partition["partition_2"],
        partition["cut_edges"],
    )


def print_topology_analysis_results(
    results: list[dict], max_size_diff: int | None = None
) -> None:
    """Print formatted topology analysis results.

    Args:
        results: List of analysis results from find_balanced_min_cut_for_all_nodes
        max_size_diff: Optional maximum size difference to display
    """
    for dado in results:
        if max_size_diff is not None and dado["min_size_difference"] > max_size_diff:
            continue

        print(
            f"Node {dado['node']} removed: "
            f"min_cut = {dado['min_cut_value']}, "
            f"size_diff = {dado['min_size_difference']}"
        )

        for particao in dado["partitions"]:
            print(f"  Cut edges: {particao['cut_edges']}")
            print(f"  Partition 1: {list(particao['partition_1'])}")
            print(f"  Partition 2: {list(particao['partition_2'])}")
        print("\n")
