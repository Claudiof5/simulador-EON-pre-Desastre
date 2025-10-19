"""Performance metrics calculation for simulation analysis.

This module provides utilities for calculating various performance metrics
from simulation results, including availability, blocking rates, and degradation.
"""

from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd


def calculate_availability(dataframe: pd.DataFrame) -> float:
    """Calculate overall network availability percentage.

    Args:
        dataframe: Simulation results dataframe with 'bloqueada' column

    Returns:
        Availability as a float between 0 and 1
    """
    if len(dataframe) == 0:
        return 0.0
    return 1.0 - dataframe["bloqueada"].mean()


def calculate_availability_before_during_after(
    dataframe: pd.DataFrame, disaster_start: float, disaster_end: float
) -> tuple[float, float, float]:
    """Calculate availability in three disaster phases.

    Args:
        dataframe: Simulation results with 'tempo_criacao' and 'bloqueada' columns
        disaster_start: Disaster start time
        disaster_end: Disaster end time

    Returns:
        Tuple of (before_availability, during_availability, after_availability)
    """
    before = dataframe[dataframe["tempo_criacao"] < disaster_start]
    during = dataframe[
        (dataframe["tempo_criacao"] >= disaster_start)
        & (dataframe["tempo_criacao"] < disaster_end)
    ]
    after = dataframe[dataframe["tempo_criacao"] >= disaster_end]

    before_avail = calculate_availability(before) if len(before) > 0 else 0.0
    during_avail = calculate_availability(during) if len(during) > 0 else 0.0
    after_avail = calculate_availability(after) if len(after) > 0 else 0.0

    return before_avail, during_avail, after_avail


def calculate_availability_by_distance(
    dataframe: pd.DataFrame, topology: nx.Graph
) -> dict[int, float]:
    """Calculate availability grouped by inter-node distance.

    Args:
        dataframe: Simulation results with 'src' and 'dst' columns
        topology: Network topology for distance calculation

    Returns:
        Dictionary mapping distance to availability
    """
    availability_by_distance: dict[int, list[bool]] = {}

    for _, row in dataframe.iterrows():
        try:
            distance = nx.shortest_path_length(
                topology, source=int(row["src"]), target=int(row["dst"])
            )
            if distance not in availability_by_distance:
                availability_by_distance[distance] = []
            availability_by_distance[distance].append(not row["bloqueada"])
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue

    return {
        dist: sum(avails) / len(avails) if avails else 0.0
        for dist, avails in availability_by_distance.items()
    }


def calculate_availability_by_node(dataframe: pd.DataFrame) -> dict[int, float]:
    """Calculate availability for each network node.

    Calculates availability for traffic involving each node (as source or destination).

    Args:
        dataframe: Simulation results with 'src', 'dst', and 'bloqueada' columns

    Returns:
        Dictionary mapping node ID to availability
    """
    availability_by_node: dict[int, list[bool]] = {}

    for _, row in dataframe.iterrows():
        src = int(row["src"])
        dst = int(row["dst"])
        not_blocked = not row["bloqueada"]

        if src not in availability_by_node:
            availability_by_node[src] = []
        if dst not in availability_by_node:
            availability_by_node[dst] = []

        availability_by_node[src].append(not_blocked)
        availability_by_node[dst].append(not_blocked)

    return {
        node: sum(avails) / len(avails) if avails else 0.0
        for node, avails in availability_by_node.items()
    }


def calculate_delta_availability(
    dataframe: pd.DataFrame, disaster_start: float, disaster_end: float
) -> dict[int, float]:
    """Calculate availability degradation per node (before vs. during disaster).

    Args:
        dataframe: Simulation results
        disaster_start: Disaster start time
        disaster_end: Disaster end time

    Returns:
        Dictionary mapping node ID to availability degradation (negative = worse)
    """
    before = dataframe[dataframe["tempo_criacao"] < disaster_start]
    during = dataframe[
        (dataframe["tempo_criacao"] >= disaster_start)
        & (dataframe["tempo_criacao"] < disaster_end)
    ]

    avail_before = calculate_availability_by_node(before)
    avail_during = calculate_availability_by_node(during)

    all_nodes = set(avail_before.keys()) | set(avail_during.keys())

    return {
        node: avail_during.get(node, 0.0) - avail_before.get(node, 0.0)
        for node in all_nodes
    }


def calculate_availability_ratio(
    dataframe: pd.DataFrame, disaster_start: float, disaster_end: float
) -> dict[int, float]:
    """Calculate availability ratio (during/before disaster) per node.

    Args:
        dataframe: Simulation results
        disaster_start: Disaster start time
        disaster_end: Disaster end time

    Returns:
        Dictionary mapping node ID to availability ratio (1.0 = no change)
    """
    before = dataframe[dataframe["tempo_criacao"] < disaster_start]
    during = dataframe[
        (dataframe["tempo_criacao"] >= disaster_start)
        & (dataframe["tempo_criacao"] < disaster_end)
    ]

    avail_before = calculate_availability_by_node(before)
    avail_during = calculate_availability_by_node(during)

    all_nodes = set(avail_before.keys()) | set(avail_during.keys())

    return {
        node: (
            avail_during.get(node, 0.0) / avail_before.get(node, 1.0)
            if avail_before.get(node, 0.0) > 0
            else 0.0
        )
        for node in all_nodes
    }


def calculate_standard_deviation_by_distance(
    dataframe: pd.DataFrame, topology: nx.Graph
) -> dict[int, float]:
    """Calculate availability standard deviation grouped by distance.

    Args:
        dataframe: Simulation results
        topology: Network topology

    Returns:
        Dictionary mapping distance to std dev of availability
    """
    availability_by_distance: dict[int, list[float]] = {}

    for _, row in dataframe.iterrows():
        try:
            distance = nx.shortest_path_length(
                topology, source=int(row["src"]), target=int(row["dst"])
            )
            if distance not in availability_by_distance:
                availability_by_distance[distance] = []
            availability_by_distance[distance].append(0.0 if row["bloqueada"] else 1.0)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue

    return {
        dist: float(np.std(avails)) if avails else 0.0
        for dist, avails in availability_by_distance.items()
    }


def get_slots_allocated_during_disaster(
    dataframe: pd.DataFrame, disaster_start: float, disaster_end: float
) -> dict[int, int]:
    """Count total slots allocated per node during disaster period.

    Args:
        dataframe: Simulation results with 'numero_de_slots', 'src', 'dst' columns
        disaster_start: Disaster start time
        disaster_end: Disaster end time

    Returns:
        Dictionary mapping node ID to total slots allocated
    """
    during_disaster = dataframe[
        (dataframe["tempo_criacao"] >= disaster_start)
        & (dataframe["tempo_criacao"] < disaster_end)
        & (~dataframe["bloqueada"])
    ]

    slots_by_node: dict[int, int] = {}

    for _, row in during_disaster.iterrows():
        src = int(row["src"])
        dst = int(row["dst"])
        slots = int(row.get("numero_de_slots", 0))

        slots_by_node[src] = slots_by_node.get(src, 0) + slots
        slots_by_node[dst] = slots_by_node.get(dst, 0) + slots

    return slots_by_node


def calculate_blocking_rate(dataframe: pd.DataFrame) -> float:
    """Calculate overall blocking rate.

    Args:
        dataframe: Simulation results with 'bloqueada' column

    Returns:
        Blocking rate as a float between 0 and 1
    """
    if len(dataframe) == 0:
        return 0.0
    return dataframe["bloqueada"].mean()


def calculate_blocking_rate_by_time_bucket(
    dataframe: pd.DataFrame, bucket_size: float = 10.0
) -> dict[int, float]:
    """Calculate blocking rate in time buckets.

    Args:
        dataframe: Simulation results with 'tempo_criacao' column
        bucket_size: Size of each time bucket

    Returns:
        Dictionary mapping bucket number to blocking rate
    """
    if len(dataframe) == 0:
        return {}

    dataframe = dataframe.copy()
    dataframe["bucket"] = (dataframe["tempo_criacao"] // bucket_size).astype(int)

    blocking_by_bucket = {}
    for bucket, group in dataframe.groupby("bucket"):
        blocking_by_bucket[int(bucket)] = group["bloqueada"].mean()

    return blocking_by_bucket


def calculate_average_distance_between_groups(
    topology: nx.Graph, group1: set[int], group2: set[int]
) -> float:
    """Calculate average shortest path distance between two node groups.

    Args:
        topology: Network topology
        group1: First set of nodes
        group2: Second set of nodes

    Returns:
        Average distance as a float
    """
    distances = []

    for node1 in group1:
        for node2 in group2:
            try:
                dist = nx.shortest_path_length(topology, node1, node2)
                distances.append(dist)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

    return sum(distances) / len(distances) if distances else 0.0


def get_neighbor_count_per_node(topology: nx.Graph) -> dict[int, int]:
    """Count number of neighbors for each node.

    Args:
        topology: Network topology

    Returns:
        Dictionary mapping node ID to neighbor count
    """
    return {node: topology.degree(node) for node in topology.nodes()}
