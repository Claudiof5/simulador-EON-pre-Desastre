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
