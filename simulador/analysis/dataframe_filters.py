"""DataFrame filtering utilities for traffic analysis.

This module provides utilities for filtering and slicing simulation result
DataFrames by various criteria such as time periods, nodes, links, and components.
"""

from __future__ import annotations

import networkx as nx
import pandas as pd


def filter_by_node(dataframe: pd.DataFrame, node: int) -> pd.DataFrame:
    """Filter requests involving specific node (as source or destination).

    Args:
        dataframe: Simulation results
        node: Node ID to filter by

    Returns:
        Filtered dataframe
    """
    return dataframe[(dataframe["src"] == node) | (dataframe["dst"] == node)].copy()


def filter_by_link(dataframe: pd.DataFrame, link: tuple[int, int]) -> pd.DataFrame:
    """Filter requests using specific link.

    Note: This requires the dataframe to have path information.

    Args:
        dataframe: Simulation results with path information
        link: Tuple of (src, dst) for the link

    Returns:
        Filtered dataframe
    """
    # Simple filter based on src/dst if path info not available
    src, dst = link
    return dataframe[
        ((dataframe["src"] == src) & (dataframe["dst"] == dst))
        | ((dataframe["src"] == dst) & (dataframe["dst"] == src))
    ].copy()


def filter_during_disaster(
    dataframe: pd.DataFrame, disaster_start: float, disaster_end: float
) -> pd.DataFrame:
    """Filter requests active during disaster period.

    Args:
        dataframe: Simulation results with 'tempo_criacao' column
        disaster_start: Disaster start time
        disaster_end: Disaster end time

    Returns:
        Filtered dataframe
    """
    return dataframe[
        (dataframe["tempo_criacao"] >= disaster_start)
        & (dataframe["tempo_criacao"] < disaster_end)
    ].copy()


def filter_before_disaster(
    dataframe: pd.DataFrame, disaster_start: float
) -> pd.DataFrame:
    """Filter requests before disaster starts.

    Args:
        dataframe: Simulation results with 'tempo_criacao' column
        disaster_start: Disaster start time

    Returns:
        Filtered dataframe
    """
    return dataframe[dataframe["tempo_criacao"] < disaster_start].copy()


def filter_after_disaster(dataframe: pd.DataFrame, disaster_end: float) -> pd.DataFrame:
    """Filter requests after disaster ends.

    Args:
        dataframe: Simulation results with 'tempo_criacao' column
        disaster_end: Disaster end time

    Returns:
        Filtered dataframe
    """
    return dataframe[dataframe["tempo_criacao"] >= disaster_end].copy()


def filter_extra_component_traffic(
    dataframe: pd.DataFrame, component1: set[int], component2: set[int]
) -> pd.DataFrame:
    """Filter traffic crossing between network components.

    Returns requests where source is in one component and destination
    is in the other component.

    Args:
        dataframe: Simulation results with 'src' and 'dst' columns
        component1: First set of nodes
        component2: Second set of nodes

    Returns:
        Filtered dataframe
    """
    comp1_set = set(component1)
    comp2_set = set(component2)

    def is_cross_component(row):
        src_in_1 = row["src"] in comp1_set
        dst_in_1 = row["dst"] in comp1_set
        src_in_2 = row["src"] in comp2_set
        dst_in_2 = row["dst"] in comp2_set

        # Cross-component: src in one, dst in other
        return (src_in_1 and dst_in_2) or (src_in_2 and dst_in_1)

    mask = dataframe.apply(is_cross_component, axis=1)
    return dataframe[mask].copy()


def filter_intra_component_traffic(
    dataframe: pd.DataFrame, component: set[int]
) -> pd.DataFrame:
    """Filter traffic within a single network component.

    Args:
        dataframe: Simulation results with 'src' and 'dst' columns
        component: Set of nodes in the component

    Returns:
        Filtered dataframe
    """
    comp_set = set(component)

    mask = dataframe.apply(
        lambda row: row["src"] in comp_set and row["dst"] in comp_set, axis=1
    )
    return dataframe[mask].copy()


def split_by_distance(
    dataframe: pd.DataFrame, topology: nx.Graph
) -> dict[int, pd.DataFrame]:
    """Split dataframe into groups by inter-node distance.

    Args:
        dataframe: Simulation results with 'src' and 'dst' columns
        topology: Network topology for distance calculation

    Returns:
        Dictionary mapping distance to filtered dataframe
    """
    groups: dict[int, list[int]] = {}

    for idx, row in dataframe.iterrows():
        try:
            distance = nx.shortest_path_length(
                topology, source=int(row["src"]), target=int(row["dst"])
            )
            if distance not in groups:
                groups[distance] = []
            groups[distance].append(idx)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue

    return {dist: dataframe.loc[indices].copy() for dist, indices in groups.items()}


def split_by_node(dataframe: pd.DataFrame) -> dict[int, pd.DataFrame]:
    """Split dataframe by nodes (src or dst).

    Args:
        dataframe: Simulation results with 'src' and 'dst' columns

    Returns:
        Dictionary mapping node ID to filtered dataframe
    """
    node_groups: dict[int, list[int]] = {}

    for idx, row in dataframe.iterrows():
        src = int(row["src"])
        dst = int(row["dst"])

        if src not in node_groups:
            node_groups[src] = []
        if dst not in node_groups:
            node_groups[dst] = []

        node_groups[src].append(idx)
        node_groups[dst].append(idx)

    return {
        node: dataframe.loc[list(set(indices))].copy()
        for node, indices in node_groups.items()
    }


def split_by_neighbor_count(
    dataframe: pd.DataFrame, topology: nx.Graph
) -> dict[int, pd.DataFrame]:
    """Split dataframe by number of node neighbors.

    Groups requests by the minimum neighbor count between source and destination.

    Args:
        dataframe: Simulation results with 'src' and 'dst' columns
        topology: Network topology

    Returns:
        Dictionary mapping neighbor count to filtered dataframe
    """
    neighbor_groups: dict[int, list[int]] = {}

    for idx, row in dataframe.iterrows():
        src = int(row["src"])
        dst = int(row["dst"])

        try:
            src_neighbors = topology.degree(src)
            dst_neighbors = topology.degree(dst)
            min_neighbors = min(src_neighbors, dst_neighbors)

            if min_neighbors not in neighbor_groups:
                neighbor_groups[min_neighbors] = []
            neighbor_groups[min_neighbors].append(idx)
        except nx.NodeNotFound:
            continue

    return {
        count: dataframe.loc[indices].copy()
        for count, indices in neighbor_groups.items()
    }


def filter_blocked_only(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Filter to only blocked requests.

    Args:
        dataframe: Simulation results with 'bloqueada' column

    Returns:
        Filtered dataframe containing only blocked requests
    """
    return dataframe[dataframe["bloqueada"]].copy()


def filter_accepted_only(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Filter to only accepted (non-blocked) requests.

    Args:
        dataframe: Simulation results with 'bloqueada' column

    Returns:
        Filtered dataframe containing only accepted requests
    """
    return dataframe[~dataframe["bloqueada"]].copy()


def create_time_windows(
    dataframe: pd.DataFrame,
    window_size: float,
    start_time: float | None = None,
    end_time: float | None = None,
) -> dict[int, pd.DataFrame]:
    """Split dataframe into time windows.

    Args:
        dataframe: Simulation results with 'tempo_criacao' column
        window_size: Size of each time window
        start_time: Optional start time (default: min time in dataframe)
        end_time: Optional end time (default: max time in dataframe)

    Returns:
        Dictionary mapping window index to filtered dataframe
    """
    if len(dataframe) == 0:
        return {}

    if start_time is None:
        start_time = dataframe["tempo_criacao"].min()
    if end_time is None:
        end_time = dataframe["tempo_criacao"].max()

    windows: dict[int, pd.DataFrame] = {}
    window_idx = 0
    current_time = start_time

    while current_time < end_time:
        window_end = current_time + window_size
        window_data = dataframe[
            (dataframe["tempo_criacao"] >= current_time)
            & (dataframe["tempo_criacao"] < window_end)
        ].copy()

        if len(window_data) > 0:
            windows[window_idx] = window_data

        window_idx += 1
        current_time = window_end

    return windows
