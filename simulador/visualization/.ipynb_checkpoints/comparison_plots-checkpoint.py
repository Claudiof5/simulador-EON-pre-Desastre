"""Comparison visualization plots for scenario analysis.

This module provides functions for creating comparative visualizations
between two simulation scenarios.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from simulador.core.topology import Topology
    from simulador.entities.isp import ISP

from simulador.analysis.scenario_comparison import (
    calculate_availability_per_bucket,
    calculate_blocking_probability_over_time,
)
from simulador.config.settings import NUMERO_DE_SLOTS
from simulador.visualization.traffic_plots import plot_network_usage


def add_timing_markers(
    ax: Axes,
    disaster_start: float,
    disaster_end: float,
    migration_times: dict[int, float],
    show_migration: bool,
    show_disaster: bool,
) -> None:
    """Add timing markers to plot.

    Args:
        ax: Matplotlib axis
        disaster_start: Disaster start time
        disaster_end: Disaster end time
        migration_times: Dict mapping ISP ID to migration start time
        show_migration: Whether to show migration start lines
        show_disaster: Whether to show disaster period shading
    """
    if show_disaster:
        # Shaded region for disaster period
        ax.axvspan(
            disaster_start, disaster_end, alpha=0.2, color="red", label="Disaster Period"
        )

    if show_migration and migration_times:
        # Vertical lines for migration start times
        migration_values = list(migration_times.values())
        for i, migration_time in enumerate(migration_values):
            if i == 0:
                ax.axvline(
                    migration_time,
                    color="orange",
                    linestyle="--",
                    alpha=0.6,
                    linewidth=1.5,
                    label="ISP Migration Start",
                )
            else:
                ax.axvline(
                    migration_time,
                    color="orange",
                    linestyle="--",
                    alpha=0.6,
                    linewidth=1.5,
                )


def plot_blocking_probability_comparison(
    ax: Axes,
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    bucket_size: float,
    scenario1_name: str,
    scenario2_name: str,
    disaster_start: float,
    disaster_end: float,
    migration_times: dict[int, float],
    show_migration: bool,
    show_disaster: bool,
) -> None:
    """Plot blocking probability comparison between two scenarios.

    Args:
        ax: Matplotlib axis
        df1: First scenario dataframe
        df2: Second scenario dataframe
        bucket_size: Time bucket size
        scenario1_name: Name of first scenario
        scenario2_name: Name of second scenario
        disaster_start: Disaster start time
        disaster_end: Disaster end time
        migration_times: Dict mapping ISP ID to migration start time
        show_migration: Whether to show migration markers
        show_disaster: Whether to show disaster period
    """
    # Calculate blocking probabilities
    times1, rates1 = calculate_blocking_probability_over_time(df1, bucket_size)
    times2, rates2 = calculate_blocking_probability_over_time(df2, bucket_size)

    # Plot
    if len(times1) > 0:
        ax.plot(
            times1,
            rates1 * 100,
            label=scenario1_name,
            marker="o",
            linewidth=2,
            markersize=4,
        )
    if len(times2) > 0:
        ax.plot(
            times2,
            rates2 * 100,
            label=scenario2_name,
            marker="s",
            linewidth=2,
            markersize=4,
        )

    # Add timing markers
    add_timing_markers(
        ax, disaster_start, disaster_end, migration_times, show_migration, show_disaster
    )

    ax.set_xlabel("Time", fontsize=12, fontweight="bold")
    ax.set_ylabel("Blocking Probability (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Blocking Probability Over Time (Bucket Size: {bucket_size})",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(loc="best", fontsize=10)
    ax.grid(alpha=0.3)


def plot_availability_comparison(
    ax: Axes,
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    bucket_size: float,
    scenario1_name: str,
    scenario2_name: str,
    disaster_start: float,
    disaster_end: float,
    migration_times: dict[int, float],
    show_migration: bool,
    show_disaster: bool,
) -> None:
    """Plot availability comparison between two scenarios.

    Args:
        ax: Matplotlib axis
        df1: First scenario dataframe
        df2: Second scenario dataframe
        bucket_size: Time bucket size
        scenario1_name: Name of first scenario
        scenario2_name: Name of second scenario
        disaster_start: Disaster start time
        disaster_end: Disaster end time
        migration_times: Dict mapping ISP ID to migration start time
        show_migration: Whether to show migration markers
        show_disaster: Whether to show disaster period
    """
    # Calculate availability
    times1, avail1 = calculate_availability_per_bucket(df1, bucket_size)
    times2, avail2 = calculate_availability_per_bucket(df2, bucket_size)

    # Plot
    if len(times1) > 0:
        ax.plot(
            times1,
            avail1 * 100,
            label=scenario1_name,
            marker="o",
            linewidth=2,
            markersize=4,
        )
    if len(times2) > 0:
        ax.plot(
            times2,
            avail2 * 100,
            label=scenario2_name,
            marker="s",
            linewidth=2,
            markersize=4,
        )

    # Add timing markers
    add_timing_markers(
        ax, disaster_start, disaster_end, migration_times, show_migration, show_disaster
    )

    ax.set_xlabel("Time", fontsize=12, fontweight="bold")
    ax.set_ylabel("Availability (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Availability Per Time Bucket (Bucket Size: {bucket_size})",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(loc="best", fontsize=10)
    ax.grid(alpha=0.3)


def plot_request_distribution_comparison(
    ax: Axes,
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    scenario1_name: str,
    scenario2_name: str,
) -> None:
    """Plot request distribution comparison by bandwidth.

    Args:
        ax: Matplotlib axis
        df1: First scenario dataframe
        df2: Second scenario dataframe
        scenario1_name: Name of first scenario
        scenario2_name: Name of second scenario
    """
    # Calculate distributions
    bandwidth_counts1 = df1["bandwidth"].value_counts().sort_index()
    bandwidth_counts2 = df2["bandwidth"].value_counts().sort_index()

    # Align indices
    all_bandwidths = sorted(set(bandwidth_counts1.index) | set(bandwidth_counts2.index))
    counts1 = [bandwidth_counts1.get(bw, 0) for bw in all_bandwidths]
    counts2 = [bandwidth_counts2.get(bw, 0) for bw in all_bandwidths]

    # Plot
    x = np.arange(len(all_bandwidths))
    width = 0.35

    ax.bar(x - width / 2, counts1, width, label=scenario1_name, alpha=0.8)
    ax.bar(x + width / 2, counts2, width, label=scenario2_name, alpha=0.8)

    ax.set_xlabel("Bandwidth (Gbps)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Number of Requests", fontsize=12, fontweight="bold")
    ax.set_title("Request Distribution by Bandwidth", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([int(bw) for bw in all_bandwidths])
    ax.legend(loc="best", fontsize=10)
    ax.grid(axis="y", alpha=0.3)


def plot_link_utilization_comparison(
    ax: Axes,
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    scenario1_name: str,
    scenario2_name: str,
    top_n: int = 15,
) -> None:
    """Plot link utilization comparison.

    Args:
        ax: Matplotlib axis
        df1: First scenario dataframe
        df2: Second scenario dataframe
        scenario1_name: Name of first scenario
        scenario2_name: Name of second scenario
        top_n: Number of top links to display
    """

    # Parse paths and count link usage
    def count_link_usage(df: pd.DataFrame) -> dict[tuple[int, int], int]:
        link_counts = defaultdict(int)
        for _, row in df.iterrows():
            if pd.notna(row["caminho"]) and row["caminho"] != "":
                try:
                    path = ast.literal_eval(row["caminho"])
                    for i in range(len(path) - 1):
                        link = tuple(sorted([path[i], path[i + 1]]))
                        link_counts[link] += 1
                except Exception:
                    continue
        return dict(link_counts)

    links1 = count_link_usage(df1)
    links2 = count_link_usage(df2)

    # Get top N links from scenario 1
    top_links = sorted(links1.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_link_keys = [link for link, _ in top_links]

    # Get counts for both scenarios
    counts1 = [links1.get(link, 0) for link in top_link_keys]
    counts2 = [links2.get(link, 0) for link in top_link_keys]

    # Plot
    x = np.arange(len(top_link_keys))
    width = 0.35

    ax.bar(x - width / 2, counts1, width, label=scenario1_name, alpha=0.8)
    ax.bar(x + width / 2, counts2, width, label=scenario2_name, alpha=0.8)

    ax.set_xlabel("Link", fontsize=12, fontweight="bold")
    ax.set_ylabel("Usage Count", fontsize=12, fontweight="bold")
    ax.set_title(f"Top {top_n} Most Utilized Links", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{u}↔{v}" for u, v in top_link_keys], rotation=45, ha="right")
    ax.legend(loc="best", fontsize=10)
    ax.grid(axis="y", alpha=0.3)


def visualize_isp_topology_comparison(
    isp1: ISP,
    isp2: ISP,
    topology: Topology,
    disaster_node: int,
    scenario1_name: str,
    scenario2_name: str,
    remove_disaster: bool = True,
    figsize: tuple[int, int] = (18, 8),
) -> None:
    """Visualize ISP topology comparison side-by-side.

    Note: Both scenarios share the same topology and ISP subgraphs.
    The comparison shows how different routing strategies affect the same network.

    Args:
        isp1: ISP from first scenario
        isp2: ISP from second scenario (same structure as isp1)
        topology: Shared topology for both scenarios
        disaster_node: Node affected by disaster
        scenario1_name: Name of first scenario
        scenario2_name: Name of second scenario
        remove_disaster: Whether to remove disaster node from visualization
        figsize: Figure size tuple
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Both scenarios share the same topology
    topology_graph = topology.topology

    # Plot ISP 1
    plot_single_isp_topology(
        ax1,
        isp1,
        topology_graph,
        disaster_node,
        f"{scenario1_name} - ISP {isp1.isp_id}",
        remove_disaster,
    )

    # Plot ISP 2 (same structure, potentially different routing)
    plot_single_isp_topology(
        ax2,
        isp2,
        topology_graph,
        disaster_node,
        f"{scenario2_name} - ISP {isp2.isp_id}",
        remove_disaster,
    )

    plt.tight_layout()
    plt.show()


def plot_single_isp_topology(
    ax: Axes,
    isp: ISP,
    topology_graph: nx.Graph,
    disaster_node: int,
    title: str,
    remove_disaster: bool,
) -> None:
    """Plot a single ISP topology.

    Args:
        ax: Matplotlib axis
        isp: ISP to visualize
        topology_graph: Network topology graph
        disaster_node: Node affected by disaster
        title: Plot title
        remove_disaster: Whether to remove disaster node
    """
    # Get ISP nodes
    isp_nodes_set = set(isp.nodes)
    isp_nodes_active = isp_nodes_set - {disaster_node} if remove_disaster else isp_nodes_set

    # Build ISP subgraph
    isp_graph = topology_graph.subgraph(isp_nodes_active).copy()
    for edge in isp.edges:
        if (
            edge[0] in isp_nodes_active
            and edge[1] in isp_nodes_active
            and not isp_graph.has_edge(edge[0], edge[1])
            and topology_graph.has_edge(edge[0], edge[1])
        ):
            edge_data = topology_graph[edge[0]][edge[1]].copy()
            isp_graph.add_edge(edge[0], edge[1], **edge_data)

    is_connected = nx.is_connected(isp_graph)

    # Layout
    pos = nx.spring_layout(topology_graph, seed=7)

    # Title
    mode_str = "Disaster Mode" if remove_disaster else "Normal Mode"
    title_full = f"{title} [{mode_str}]"
    if not is_connected:
        title_full += " - DISCONNECTED"
    ax.set_title(title_full, fontsize=14, fontweight="bold")

    # Background nodes (other ISPs)
    all_nodes = list(topology_graph.nodes())
    background_nodes = [
        n for n in all_nodes if n not in isp_nodes_set and n != disaster_node
    ]

    if background_nodes:
        nx.draw_networkx_nodes(
            topology_graph,
            pos,
            nodelist=background_nodes,
            node_color="lightgray",
            node_size=300,
            alpha=0.3,
            ax=ax,
        )

    # Background edges
    all_edges = list(topology_graph.edges())
    nx.draw_networkx_edges(
        topology_graph,
        pos,
        edgelist=all_edges,
        edge_color="lightgray",
        width=1,
        alpha=0.2,
        ax=ax,
    )

    # ISP nodes
    isp_nodes_list = list(isp_nodes_active)
    if isp_nodes_list:
        nx.draw_networkx_nodes(
            topology_graph,
            pos,
            nodelist=isp_nodes_list,
            node_color="lightblue",
            node_size=500,
            edgecolors="black",
            linewidths=2,
            ax=ax,
        )

    # Datacenter nodes
    if isp.datacenter is not None:
        if isp.datacenter.source in isp_nodes_active:
            nx.draw_networkx_nodes(
                topology_graph,
                pos,
                nodelist=[isp.datacenter.source],
                node_color="orange",
                node_size=600,
                edgecolors="darkorange",
                linewidths=3,
                ax=ax,
                label="Datacenter Source",
            )

        if isp.datacenter.destination in isp_nodes_active:
            nx.draw_networkx_nodes(
                topology_graph,
                pos,
                nodelist=[isp.datacenter.destination],
                node_color="limegreen",
                node_size=600,
                edgecolors="darkgreen",
                linewidths=3,
                ax=ax,
                label="Datacenter Destination",
            )

    # Disaster node (if in disaster mode)
    if remove_disaster and disaster_node in isp_nodes_set:
        nx.draw_networkx_nodes(
            topology_graph,
            pos,
            nodelist=[disaster_node],
            node_color="red",
            node_size=700,
            node_shape="X",
            edgecolors="darkred",
            linewidths=3,
            ax=ax,
            label="Disaster Node",
        )

    # ISP edges
    edges = list(isp_graph.edges())
    nx.draw_networkx_edges(
        topology_graph, pos, edgelist=edges, edge_color="steelblue", width=2, alpha=0.7, ax=ax
    )

    # Node labels
    nx.draw_networkx_labels(topology_graph, pos, font_size=8, font_weight="bold", ax=ax)

    ax.axis("off")
    ax.legend(loc="upper right", fontsize=9)


def plot_network_usage_comparison(
    ax: Axes,
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    topology,
    scenario1_name: str,
    scenario2_name: str,
    disaster_start: float,
    disaster_end: float,
    migration_times: dict[int, float],
    show_migration: bool,
    show_disaster: bool,
    time_step: float = 0.1,
    window_size: float = 10,
    numero_de_slots: int = NUMERO_DE_SLOTS,
) -> None:
    """Plot network usage comparison between two scenarios.

    Args:
        ax: Matplotlib axis
        df1: First scenario dataframe
        df2: Second scenario dataframe
        topology: Network topology (NetworkX graph)
        scenario1_name: Name of first scenario
        scenario2_name: Name of second scenario
        disaster_start: Disaster start time
        disaster_end: Disaster end time
        migration_times: Dict mapping ISP IDs to migration start times
        show_migration: Whether to show migration markers
        show_disaster: Whether to show disaster period
        time_step: Time step for sampling (default 0.1)
        window_size: Window size for moving average (default 10)
        numero_de_slots: Total number of slots per link
    """
    # Filter for non-blocked paths for both scenarios
    df1_filtered = df1[~df1["bloqueada"]].copy()
    df2_filtered = df2[~df2["bloqueada"]].copy()

    # Calculate slots used
    df1_filtered["slots_used"] = (
        df1_filtered["numero_de_slots"] * df1_filtered["tamanho_do_caminho"]
    )
    df2_filtered["slots_used"] = (
        df2_filtered["numero_de_slots"] * df2_filtered["tamanho_do_caminho"]
    )

    # Get max time across both scenarios
    max_time = max(
        df1_filtered["tempo_desalocacao"].max(),
        df1_filtered["tempo_criacao"].max(),
        df2_filtered["tempo_desalocacao"].max(),
        df2_filtered["tempo_criacao"].max(),
    )

    # Calculate total network capacity
    numero_total_de_slots = len(topology.edges()) * numero_de_slots

    # Time points for sampling
    time_points = np.arange(10, max_time + time_step, time_step)
    window_points = np.arange(10, max_time + window_size, window_size)

    # Calculate usage for each scenario
    usage1 = _calculate_usage_at_time_points(
        df1_filtered, time_points, numero_total_de_slots
    )
    usage2 = _calculate_usage_at_time_points(
        df2_filtered, time_points, numero_total_de_slots
    )

    # Apply moving average
    usage1_smooth = _moving_average(usage1, window_points, time_points)
    usage2_smooth = _moving_average(usage2, window_points, time_points)

    # Plot
    ax.plot(
        window_points,
        usage1_smooth * 100,
        label=scenario1_name,
        linewidth=2,
        alpha=0.8,
    )
    ax.plot(
        window_points,
        usage2_smooth * 100,
        label=scenario2_name,
        linewidth=2,
        alpha=0.8,
    )

    # Add timing markers
    add_timing_markers(
        ax, disaster_start, disaster_end, migration_times, show_migration, show_disaster
    )

    ax.set_xlabel("Time", fontsize=12, fontweight="bold")
    ax.set_ylabel("Network Usage (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Network Slot Usage Comparison (Window Size: {window_size})",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(loc="best", fontsize=10)
    ax.grid(alpha=0.3)


def _calculate_usage_at_time_points(
    dataframe: pd.DataFrame,
    time_points: np.ndarray,
    total_slots: int,
) -> np.ndarray:
    """Calculate network usage at specific time points.

    Args:
        dataframe: Filtered dataframe with slots_used, tempo_criacao, tempo_desalocacao
        time_points: Array of time points to calculate usage at
        total_slots: Total network capacity

    Returns:
        Array of usage values (as fraction of total capacity)
    """
    usage = np.zeros(len(time_points))

    for idx, t in enumerate(time_points):
        # Find all connections active at time t
        active_mask = (dataframe["tempo_criacao"] <= t) & (dataframe["tempo_desalocacao"] > t)
        total_slots_used = dataframe.loc[active_mask, "slots_used"].sum()
        usage[idx] = total_slots_used / total_slots

    return usage


def _moving_average(
    usage: np.ndarray,
    window_points: np.ndarray,
    time_points: np.ndarray,
) -> np.ndarray:
    """Calculate moving average of usage over window points.

    Args:
        usage: Usage values at time_points
        window_points: Window center points
        time_points: Original time points

    Returns:
        Smoothed usage values at window_points
    """
    smoothed = np.zeros(len(window_points))

    for idx, wp in enumerate(window_points):
        # Find indices within window
        mask = np.abs(time_points - wp) <= (window_points[1] - window_points[0]) / 2
        if mask.any():
            smoothed[idx] = usage[mask].mean()

    return smoothed

