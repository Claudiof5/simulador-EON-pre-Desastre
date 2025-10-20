"""Availability visualization functions.

This module provides plotting utilities for visualizing availability metrics
across different dimensions (time, distance, nodes, etc.).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from simulador.analysis import metrics_calculator


def plot_availability_before_during_after(
    dataframes: dict[str, pd.DataFrame],
    disaster_start: float,
    disaster_end: float,
    figsize: tuple[int, int] = (12, 6),
) -> plt.Figure:
    """Bar chart comparing availability across disaster phases.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        disaster_start: Disaster start time
        disaster_end: Disaster end time
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    scenarios = list(dataframes.keys())
    x = np.arange(3)  # Before, During, After
    width = 0.8 / len(scenarios)

    for i, (name, df) in enumerate(dataframes.items()):
        before, during, after = (
            metrics_calculator.calculate_availability_before_during_after(
                df, disaster_start, disaster_end
            )
        )

        offset = (i - len(scenarios) / 2) * width + width / 2
        ax.bar(x + offset, [before, during, after], width, label=name)

    ax.set_ylabel("Availability")
    ax.set_title("Availability: Before, During, and After Disaster")
    ax.set_xticks(x)
    ax.set_xticklabels(["Before", "During Disaster", "After"])
    ax.set_ylim([0, 1.1])
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    return fig


def plot_availability_by_distance(
    dataframes: dict[str, pd.DataFrame], topology, figsize: tuple[int, int] = (14, 6)
) -> plt.Figure:
    """Plot availability as a function of inter-node distance.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        topology: Network topology
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    for name, df in dataframes.items():
        avail_by_dist = metrics_calculator.calculate_availability_by_distance(
            df, topology
        )

        distances = sorted(avail_by_dist.keys())
        availabilities = [avail_by_dist[d] for d in distances]

        ax.plot(distances, availabilities, marker="o", label=name, linewidth=2)

    ax.set_xlabel("Distance (hops)")
    ax.set_ylabel("Availability")
    ax.set_title("Availability by Inter-Node Distance")
    ax.set_ylim([0, 1.1])
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def plot_availability_by_node(
    dataframes: dict[str, pd.DataFrame],
    figsize: tuple[int, int] = (14, 6),
    top_n: int | None = None,
) -> plt.Figure:
    """Bar chart of availability per network node.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        figsize: Figure size
        top_n: Optional limit to show only top N nodes

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Get all nodes from first dataframe
    first_df = list(dataframes.values())[0]
    avail_by_node = metrics_calculator.calculate_availability_by_node(first_df)
    nodes = sorted(avail_by_node.keys())

    if top_n is not None:
        # Sort by availability and take top N
        sorted_nodes = sorted(
            nodes, key=lambda n: avail_by_node.get(n, 0), reverse=True
        )
        nodes = sorted_nodes[:top_n]

    x = np.arange(len(nodes))
    width = 0.8 / len(dataframes)

    for i, (name, df) in enumerate(dataframes.items()):
        avail = metrics_calculator.calculate_availability_by_node(df)
        availabilities = [avail.get(node, 0.0) for node in nodes]

        offset = (i - len(dataframes) / 2) * width + width / 2
        ax.bar(x + offset, availabilities, width, label=name)

    ax.set_xlabel("Node ID")
    ax.set_ylabel("Availability")
    ax.set_title("Availability by Node")
    ax.set_xticks(x)
    ax.set_xticklabels([str(n) for n in nodes], rotation=45)
    ax.set_ylim([0, 1.1])
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    return fig


def plot_delta_availability(
    dataframes: dict[str, pd.DataFrame],
    disaster_start: float,
    disaster_end: float,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """Plot availability degradation by node.

    Shows the change in availability (during - before) for each node.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        disaster_start: Disaster start time
        disaster_end: Disaster end time
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    for name, df in dataframes.items():
        delta = metrics_calculator.calculate_delta_availability(
            df, disaster_start, disaster_end
        )

        nodes = sorted(delta.keys())
        deltas = [delta[n] for n in nodes]

        ax.plot(nodes, deltas, marker="o", label=name, alpha=0.7)

    ax.axhline(y=0, color="k", linestyle="--", alpha=0.3)
    ax.set_xlabel("Node ID")
    ax.set_ylabel("Δ Availability (During - Before)")
    ax.set_title("Availability Degradation by Node")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def plot_availability_ratio(
    dataframes: dict[str, pd.DataFrame],
    disaster_start: float,
    disaster_end: float,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """Plot availability ratio (during/before disaster).

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        disaster_start: Disaster start time
        disaster_end: Disaster end time
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    for name, df in dataframes.items():
        ratio = metrics_calculator.calculate_availability_ratio(
            df, disaster_start, disaster_end
        )

        nodes = sorted(ratio.keys())
        ratios = [ratio[n] for n in nodes]

        ax.plot(nodes, ratios, marker="o", label=name, alpha=0.7)

    ax.axhline(y=1.0, color="k", linestyle="--", alpha=0.3, label="No change")
    ax.set_xlabel("Node ID")
    ax.set_ylabel("Availability Ratio (During / Before)")
    ax.set_title("Availability Ratio by Node")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def plot_availability_heatmap(
    dataframe: pd.DataFrame, topology, figsize: tuple[int, int] = (12, 10)
) -> plt.Figure:
    """Create heatmap of availability between all node pairs.

    Args:
        dataframe: Simulation results
        topology: Network topology
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    nodes = sorted(topology.nodes())
    n = len(nodes)
    heatmap_data = np.zeros((n, n))

    # Group by src-dst pairs
    for (src, dst), group in dataframe.groupby(["src", "dst"]):
        if src in nodes and dst in nodes:
            i = nodes.index(src)
            j = nodes.index(dst)
            heatmap_data[i, j] = 1.0 - group["bloqueada"].mean()

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(heatmap_data, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(nodes, rotation=90)
    ax.set_yticklabels(nodes)
    ax.set_xlabel("Destination Node")
    ax.set_ylabel("Source Node")
    ax.set_title("Availability Heatmap (Source → Destination)")

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Availability")

    plt.tight_layout()
    return fig


def plot_availability_comparison_summary(
    dataframes: dict[str, pd.DataFrame], figsize: tuple[int, int] = (14, 5)
) -> plt.Figure:
    """Create summary comparison of availability metrics.

    Shows overall, min, max, and std dev of availability for each scenario.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    scenarios = list(dataframes.keys())
    metrics_overall = []
    metrics_std = []

    for _, df in dataframes.items():
        overall = metrics_calculator.calculate_availability(df)
        avail_by_node = metrics_calculator.calculate_availability_by_node(df)
        std = float(np.std(list(avail_by_node.values())))

        metrics_overall.append(overall)
        metrics_std.append(std)

    # Overall availability
    axes[0].bar(scenarios, metrics_overall, color=["#3498db", "#e74c3c"])
    axes[0].set_ylabel("Overall Availability")
    axes[0].set_title("Overall Availability")
    axes[0].set_ylim([0, 1.1])
    axes[0].grid(axis="y", alpha=0.3)

    # Add percentage labels
    for i, v in enumerate(metrics_overall):
        axes[0].text(i, v + 0.02, f"{v:.1%}", ha="center", va="bottom")

    # Standard deviation
    axes[1].bar(scenarios, metrics_std, color=["#3498db", "#e74c3c"])
    axes[1].set_ylabel("Standard Deviation")
    axes[1].set_title("Availability Variability (Std Dev)")
    axes[1].grid(axis="y", alpha=0.3)

    plt.tight_layout()
    return fig


def plot_availability_by_isp(
    dataframe: pd.DataFrame,
    isp_data: dict[int, dict] | object,
    disaster_start: float | None = None,
    disaster_end: float | None = None,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """Plot availability metrics separated by source ISP.

    Args:
        dataframe: Simulation results with 'src_isp_index', 'bloqueada', 'tempo_criacao' columns
        isp_data: Either ISP dict {isp_id: {...}} OR Scenario object
        disaster_start: Optional disaster start time for phase analysis
        disaster_end: Optional disaster end time for phase analysis
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    # Extract ISP IDs from Scenario if needed
    if hasattr(isp_data, "lista_de_isps"):
        isp_dict = {}
        for isp in isp_data.lista_de_isps:
            isp_dict[isp.isp_id] = {}
    else:
        isp_dict = isp_data

    # Calculate availability per ISP
    isp_stats = {}
    for isp_id in isp_dict:
        # Filter dataframe for this ISP's traffic using src_isp_index
        isp_traffic = dataframe[dataframe["src_isp_index"] == isp_id]

        if len(isp_traffic) > 0:
            overall_avail = 1.0 - isp_traffic["bloqueada"].mean()

            stats = {"overall": overall_avail, "total_requests": len(isp_traffic)}

            # Phase-wise if disaster times provided
            if disaster_start is not None and disaster_end is not None:
                before = isp_traffic[isp_traffic["tempo_criacao"] < disaster_start]
                during = isp_traffic[
                    (isp_traffic["tempo_criacao"] >= disaster_start)
                    & (isp_traffic["tempo_criacao"] < disaster_end)
                ]
                after = isp_traffic[isp_traffic["tempo_criacao"] >= disaster_end]

                stats["before"] = (
                    1.0 - before["bloqueada"].mean() if len(before) > 0 else 0
                )
                stats["during"] = (
                    1.0 - during["bloqueada"].mean() if len(during) > 0 else 0
                )
                stats["after"] = (
                    1.0 - after["bloqueada"].mean() if len(after) > 0 else 0
                )

            isp_stats[isp_id] = stats

    # Plot
    if disaster_start is not None and disaster_end is not None:
        # Phase-wise comparison
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        isp_ids = list(isp_stats.keys())
        x = np.arange(len(isp_ids))
        width = 0.25

        before_vals = [isp_stats[isp]["before"] for isp in isp_ids]
        during_vals = [isp_stats[isp]["during"] for isp in isp_ids]
        after_vals = [isp_stats[isp]["after"] for isp in isp_ids]

        ax1.bar(x - width, before_vals, width, label="Before", color="#2ecc71")
        ax1.bar(x, during_vals, width, label="During", color="#e74c3c")
        ax1.bar(x + width, after_vals, width, label="After", color="#3498db")

        ax1.set_ylabel("Availability")
        ax1.set_title("Availability by ISP (Phase-wise)")
        ax1.set_xticks(x)
        ax1.set_xticklabels([f"ISP {isp}" for isp in isp_ids])
        ax1.set_ylim([0, 1.1])
        ax1.legend()
        ax1.grid(axis="y", alpha=0.3)

        # Overall availability
        overall_vals = [isp_stats[isp]["overall"] for isp in isp_ids]
        bars = ax2.bar(isp_ids, overall_vals, color="#3498db")
        ax2.set_ylabel("Overall Availability")
        ax2.set_title("Overall Availability by ISP")
        ax2.set_xlabel("ISP ID")
        ax2.set_ylim([0, 1.1])
        ax2.grid(axis="y", alpha=0.3)

        # Add value labels
        for bar, val in zip(bars, overall_vals, strict=False):
            height = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.02,
                f"{val:.1%}",
                ha="center",
                va="bottom",
            )

    else:
        # Overall only
        fig, ax = plt.subplots(figsize=figsize)

        isp_ids = list(isp_stats.keys())
        overall_vals = [isp_stats[isp]["overall"] for isp in isp_ids]

        bars = ax.bar(isp_ids, overall_vals, color="#3498db")
        ax.set_ylabel("Availability")
        ax.set_title("Availability by ISP")
        ax.set_xlabel("ISP ID")
        ax.set_ylim([0, 1.1])
        ax.grid(axis="y", alpha=0.3)

        # Add value labels
        for bar, val in zip(bars, overall_vals, strict=False):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.02,
                f"{val:.1%}",
                ha="center",
                va="bottom",
            )

    plt.tight_layout()


def plot_availability_by_distance_per_isp(
    dataframe: pd.DataFrame,
    topology,
    isp_data: dict[int, dict] | object,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """Plot availability by distance, separated by source ISP.

    Args:
        dataframe: Simulation results
        topology: Network topology
        isp_data: Either ISP dict OR Scenario object
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    # Extract ISP IDs
    if hasattr(isp_data, "lista_de_isps"):
        isp_dict = {}
        for isp in isp_data.lista_de_isps:
            isp_dict[isp.isp_id] = {}
    else:
        isp_dict = isp_data

    fig, ax = plt.subplots(figsize=figsize)

    colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]

    for idx, isp_id in enumerate(isp_dict):
        # Filter for this ISP's traffic using src_isp_index
        isp_traffic = dataframe[dataframe["src_isp_index"] == isp_id]

        if len(isp_traffic) == 0:
            continue

        # Calculate availability by distance for this ISP
        avail_by_dist = metrics_calculator.calculate_availability_by_distance(
            isp_traffic, topology
        )

        distances = sorted(avail_by_dist.keys())
        availabilities = [avail_by_dist[d] for d in distances]

        color = colors[idx % len(colors)]
        ax.plot(
            distances,
            availabilities,
            marker="o",
            label=f"ISP {isp_id}",
            linewidth=2,
            color=color,
        )

    ax.set_xlabel("Distance (hops)")
    ax.set_ylabel("Availability")
    ax.set_title("Availability by Distance - Per ISP")
    ax.set_ylim([0, 1.1])
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()


def plot_isp_traffic_comparison(
    dataframe: pd.DataFrame,
    isp_data: dict[int, dict] | object,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """Compare traffic volume and blocking rates across ISPs.

    Args:
        dataframe: Simulation results
        isp_data: Either ISP dict OR Scenario object
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    # Extract ISP IDs
    if hasattr(isp_data, "lista_de_isps"):
        isp_dict = {}
        for isp in isp_data.lista_de_isps:
            isp_dict[isp.isp_id] = {}
    else:
        isp_dict = isp_data

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    isp_ids = []
    total_requests = []
    blocked_requests = []
    blocking_rates = []

    for isp_id in isp_dict:
        # Filter for this ISP's traffic using src_isp_index
        isp_traffic = dataframe[dataframe["src_isp_index"] == isp_id]

        if len(isp_traffic) > 0:
            isp_ids.append(isp_id)
            total = len(isp_traffic)
            blocked = isp_traffic["bloqueada"].sum()

            total_requests.append(total)
            blocked_requests.append(blocked)
            blocking_rates.append(blocked / total if total > 0 else 0)

    # Traffic volume
    x = np.arange(len(isp_ids))
    width = 0.35

    ax1.bar(x - width / 2, total_requests, width, label="Total", color="#3498db")
    ax1.bar(x + width / 2, blocked_requests, width, label="Blocked", color="#e74c3c")

    ax1.set_ylabel("Number of Requests")
    ax1.set_title("Traffic Volume by ISP")
    ax1.set_xlabel("ISP ID")
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"ISP {isp}" for isp in isp_ids])
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)

    # Blocking rate
    bars = ax2.bar(isp_ids, blocking_rates, color="#e74c3c")
    ax2.set_ylabel("Blocking Rate")
    ax2.set_title("Blocking Rate by ISP")
    ax2.set_xlabel("ISP ID")
    ax2.set_ylim([0, max(blocking_rates) * 1.2 if blocking_rates else 1])
    ax2.grid(axis="y", alpha=0.3)

    # Add percentage labels
    for bar, rate in zip(bars, blocking_rates, strict=False):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.01,
            f"{rate:.1%}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
