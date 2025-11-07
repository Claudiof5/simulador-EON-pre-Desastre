"""Weight calculation functions for network routing.

This module provides utilities for calculating various types of weights
used in network routing decisions, including ISP usage, migration, and
link criticality weights.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

import networkx as nx

if TYPE_CHECKING:
    from simulador.entities.isp import ISP


def calculate_isp_usage_weights(
    isp_list: list[ISP], alfa: float = 0.2
) -> dict[int, dict[tuple[int, int], dict[str, float]]]:
    """Calculate ISP usage weights based on shortest path frequency."""
    link_ocurrances_in_all_isps = defaultdict(int)
    for isp in isp_list:
        for edge in isp.edges:
            link_ocurrances_in_all_isps[edge] += 1
            reverse_edge = (edge[1], edge[0])
            link_ocurrances_in_all_isps[reverse_edge] += 1

    weights_per_isp = {isp.isp_id: {} for isp in isp_list}
    for isp in isp_list:
        for edge in isp.edges:
            normalized = (
                alfa * (link_ocurrances_in_all_isps[edge] - 1) / (len(isp_list) - 1)
            )
            weights_per_isp[isp.isp_id][edge] = normalized
            reverse_edge = (edge[1], edge[0])
            weights_per_isp[isp.isp_id][reverse_edge] = normalized

    return weights_per_isp


def calculate_migration_weights(
    lista_de_isps: list[ISP], beta: float = 0.2
) -> dict[tuple[int, int], dict[str, float]]:
    """Calculate migration weights based on datacenter migration paths."""
    link_count = defaultdict(int)
    total_migration_paths = 0

    for isp in lista_de_isps:
        if not hasattr(isp, "datacenter") or isp.datacenter is None:
            continue

        datacenter = isp.datacenter
        src = datacenter.source
        dst = datacenter.destination

        # Get paths from ISP's internal paths
        if (
            hasattr(isp, "caminhos_internos_isp")
            and isp.caminhos_internos_isp
            and src in isp.caminhos_internos_isp
            and dst in isp.caminhos_internos_isp[src]
        ):
            paths = isp.caminhos_internos_isp[src][dst]

            for path_info in paths:
                caminho = path_info["caminho"]
                total_migration_paths += 1

                for i in range(len(caminho) - 1):
                    link = (caminho[i], caminho[i + 1])
                    link_count[link] += 1

                    reverse = (caminho[i + 1], caminho[i])
                    link_count[reverse] += 1

    if not link_count:
        return {}

    max_count = max(link_count.values())
    migration_weights = {}

    for link, count in link_count.items():
        normalized = count / max_count if max_count > 0 else 0
        weight = normalized * beta
        migration_weights[link] = weight

    return migration_weights


def calculate_link_criticality(
    graph: Any, lista_de_isps: list, disaster_node: int, gamma: float = 0.4
) -> dict[tuple[int, int], dict[str, float]]:
    """Calculate link criticality based on bridges across all ISPs.

    Args:
        graph: NetworkX graph representing the network
        lista_de_isps: List of ISP objects
        disaster_node: Node affected by disaster
        gamma: Weight factor for link criticality (default: 0.4)

    Returns:
        Dictionary mapping links to their criticality weights
    """
    link_criticality = {}

    for isp in lista_de_isps:
        # Create ISP subgraph
        isp_graph = graph.subgraph(isp.nodes).copy()
        for edge in isp.edges:
            if (
                edge[0] in isp.nodes
                and edge[1] in isp.nodes
                and not isp_graph.has_edge(edge[0], edge[1])
                and graph.has_edge(edge[0], edge[1])
            ):
                edge_data = graph[edge[0]][edge[1]].copy()
                isp_graph.add_edge(edge[0], edge[1], **edge_data)

        # Remove disaster node
        if disaster_node in isp_graph.nodes():
            isp_graph.remove_node(disaster_node)

        # Find bridges
        bridges = list(nx.bridges(isp_graph))

        for link in bridges:
            # Forward direction
            if link not in link_criticality:
                link_criticality[link] = {
                    "bridge_count": 0,
                    "isp_list": [],
                    "weight_penalty": 0.0,
                }
            link_criticality[link]["bridge_count"] += 1
            link_criticality[link]["isp_list"].append(isp.isp_id)

            # Reverse direction
            reverse = (link[1], link[0])
            if reverse not in link_criticality:
                link_criticality[reverse] = {
                    "bridge_count": 0,
                    "isp_list": [],
                    "weight_penalty": 0.0,
                }
            link_criticality[reverse]["bridge_count"] += 1
            link_criticality[reverse]["isp_list"].append(isp.isp_id)

    link_criticality_return = {}
    for link, data in link_criticality.items():
        normalized = data["bridge_count"]
        link_criticality_return[link] = normalized / len(lista_de_isps) * gamma

    return link_criticality_return


def calculate_weights_by_isps(
    lista_de_isps: list[ISP],
    isp_usage_weights: dict,
    migration_weights: dict,
    link_criticality_weights: dict,
) -> dict[int, dict[tuple[int, int], dict[str, float]]]:
    link_weights_by_isp: dict[int, dict[tuple[int, int], dict[str, float]]] = {}
    for isp in lista_de_isps:
        isp_id = isp.isp_id
        link_weights_by_isp[isp.isp_id] = {}
        for link in isp.edges:
            reverse_link = (link[1], link[0])
            isp_weight = isp_usage_weights.get(isp_id, {}).get(link, 0.0)
            if isp_weight == 1.0:  # Try reverse
                isp_weight = isp_usage_weights.get(isp_id, {}).get(reverse_link, 0.0)

            migration_weight = migration_weights.get(link, 0.0)
            if migration_weight == 0.0:  # Try reverse
                migration_weight = migration_weights.get(reverse_link, 0.0)

            criticality_weight = link_criticality_weights.get(link, 0.0)
            if criticality_weight == 0.0:  # Try reverse
                criticality_weight = link_criticality_weights.get(reverse_link, 0.0)

            link_components = {
                "isp_usage": isp_weight,
                "migration": migration_weight,
                "criticality": criticality_weight,
                "total": 1 + isp_weight + migration_weight + criticality_weight,
            }
            link_weights_by_isp[isp.isp_id][link] = link_components
            link_weights_by_isp[isp.isp_id][reverse_link] = link_components

    return link_weights_by_isp


def create_weighted_graph(
    graph: nx.Graph,
    isp_id: int,
    weights_by_link_by_isp: dict[int, dict[tuple[int, int], float]],
) -> nx.Graph:
    """Create a weighted graph for a specific ISP.

    Args:
        graph: Original NetworkX graph
        isp_id: ID of the ISP requesting paths
        weights_by_link_by_isp: Dictionary of weights by ISP and link

    Returns:
        Graph with modified edge weights
    """
    weighted_graph = graph.copy()

    # Get weights for this ISP
    isp_weights = weights_by_link_by_isp.get(isp_id, {})

    for u, v, data in weighted_graph.edges(data=True):
        link = tuple(sorted((u, v)))

        # Get the weight penalty for this link
        weight_penalty = isp_weights.get(link, 0.0)

        # Add penalty to original weight
        original_weight = data.get("weight", 1.0)
        weighted_graph[u][v]["weight"] = original_weight + weight_penalty

    return weighted_graph
