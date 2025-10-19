"""Traffic and blocking visualization functions.

This module provides plotting utilities for visualizing traffic patterns,
blocking rates, and network utilization over time.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from simulador.analysis import metrics_calculator


def plot_accumulated_blocked_requests(
    dataframes: dict[str, pd.DataFrame], figsize: tuple[int, int] = (14, 6)
) -> plt.Figure:
    """Plot cumulative blocked requests over time.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    for name, df in dataframes.items():
        df_sorted = df.sort_values("tempo_criacao")
        blocked = df_sorted[df_sorted["bloqueada"]]

        times = blocked["tempo_criacao"].values
        cumulative = np.arange(1, len(times) + 1)

        ax.plot(times, cumulative, label=name, linewidth=2)

    ax.set_xlabel("Time")
    ax.set_ylabel("Cumulative Blocked Requests")
    ax.set_title("Accumulated Blocked Requests Over Time")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def plot_blocked_count_by_bucket(
    dataframes: dict[str, pd.DataFrame],
    bucket_size: float = 10.0,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """Histogram of blocked requests in time buckets.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        bucket_size: Size of each time bucket
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    for name, df in dataframes.items():
        df_copy = df.copy()
        df_copy["bucket"] = (df_copy["tempo_criacao"] // bucket_size).astype(int)

        blocked_counts = df_copy[df_copy["bloqueada"]].groupby("bucket").size()
        buckets = sorted(blocked_counts.index)
        counts = [blocked_counts[b] for b in buckets]

        ax.bar(buckets, counts, width=0.8, alpha=0.6, label=name)

    ax.set_xlabel(f"Time Bucket ({bucket_size}s intervals)")
    ax.set_ylabel("Number of Blocked Requests")
    ax.set_title("Blocked Requests by Time Period")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    return fig


def plot_blocking_ratio_by_bucket(
    dataframes: dict[str, pd.DataFrame],
    bucket_size: float = 30.0,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """Plot blocking ratio over time buckets.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        bucket_size: Size of each time bucket
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    for name, df in dataframes.items():
        df_copy = df.copy()
        df_copy["bucket"] = (df_copy["tempo_criacao"] // bucket_size).astype(int)

        blocking_by_bucket = df_copy.groupby("bucket")["bloqueada"].mean()
        buckets = sorted(blocking_by_bucket.index)
        ratios = [blocking_by_bucket[b] for b in buckets]

        ax.plot(buckets, ratios, marker="o", label=name, linewidth=2)

    ax.set_xlabel(f"Time Bucket ({bucket_size}s intervals)")
    ax.set_ylabel("Blocking Ratio")
    ax.set_title("Blocking Ratio Over Time")
    ax.set_ylim([0, max(1.0, ax.get_ylim()[1])])
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def plot_blocking_ratio_sliding_window(
    dataframes: dict[str, pd.DataFrame],
    window_size: int = 100,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """Plot blocking ratio with sliding time window.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        window_size: Number of requests in sliding window
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    for name, df in dataframes.items():
        df_sorted = df.sort_values("tempo_criacao").reset_index(drop=True)

        times = []
        ratios = []

        for i in range(window_size, len(df_sorted)):
            window = df_sorted.iloc[i - window_size : i]
            times.append(window["tempo_criacao"].iloc[-1])
            ratios.append(window["bloqueada"].mean())

        ax.plot(times, ratios, label=name, linewidth=2, alpha=0.7)

    ax.set_xlabel("Time")
    ax.set_ylabel("Blocking Ratio")
    ax.set_title(f"Blocking Ratio (Sliding Window: {window_size} requests)")
    ax.set_ylim([0, 1.0])
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def plot_network_usage(
    dataframe: pd.DataFrame,
    disaster_start: float | None = None,
    disaster_end: float | None = None,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """Plot overall network utilization over time.

    Args:
        dataframe: Simulation results
        disaster_start: Optional disaster start time for vertical line
        disaster_end: Optional disaster end time for vertical line
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)

    # Group by time
    df_sorted = dataframe.sort_values("tempo_criacao")

    # Plot 1: Request rate
    times = df_sorted["tempo_criacao"].values
    request_rate = np.ones(len(times))
    for i in range(1, len(times)):
        dt = times[i] - times[i - 1]
        request_rate[i] = 1.0 / dt if dt > 0 else 0.0

    axes[0].plot(times, request_rate, linewidth=1, alpha=0.7)
    axes[0].set_ylabel("Request Rate")
    axes[0].set_title("Network Activity Over Time")
    axes[0].grid(alpha=0.3)

    # Plot 2: Blocking rate (cumulative)
    blocked = df_sorted["bloqueada"].values
    cumulative_blocking = np.cumsum(blocked) / np.arange(1, len(blocked) + 1)

    axes[1].plot(times, cumulative_blocking, linewidth=2, color="red")
    axes[1].set_xlabel("Time")
    axes[1].set_ylabel("Cumulative Blocking Rate")
    axes[1].set_ylim([0, 1.0])
    axes[1].grid(alpha=0.3)

    # Add disaster markers
    if disaster_start is not None:
        for ax in axes:
            ax.axvline(
                disaster_start,
                color="orange",
                linestyle="--",
                alpha=0.5,
                label="Disaster Start",
            )
    if disaster_end is not None:
        for ax in axes:
            ax.axvline(
                disaster_end,
                color="green",
                linestyle="--",
                alpha=0.5,
                label="Disaster End",
            )

    if disaster_start is not None or disaster_end is not None:
        axes[0].legend()

    plt.tight_layout()
    return fig


def plot_slots_per_node_during_disaster(
    dataframe: pd.DataFrame,
    disaster_start: float,
    disaster_end: float,
    figsize: tuple[int, int] = (14, 6),
    top_n: int = 20,
) -> plt.Figure:
    """Plot slot allocation per node during disaster.

    Args:
        dataframe: Simulation results
        disaster_start: Disaster start time
        disaster_end: Disaster end time
        figsize: Figure size
        top_n: Number of top nodes to display

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    slots_by_node = metrics_calculator.get_slots_allocated_during_disaster(
        dataframe, disaster_start, disaster_end
    )

    # Sort and take top N
    sorted_nodes = sorted(slots_by_node.items(), key=lambda x: x[1], reverse=True)[
        :top_n
    ]

    nodes = [n for n, _ in sorted_nodes]
    slots = [s for _, s in sorted_nodes]

    ax.bar(range(len(nodes)), slots, color="steelblue")
    ax.set_xticks(range(len(nodes)))
    ax.set_xticklabels([str(n) for n in nodes], rotation=45)
    ax.set_xlabel("Node ID")
    ax.set_ylabel("Total Slots Allocated")
    ax.set_title(f"Top {top_n} Nodes by Slot Usage During Disaster")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    return fig


def plot_disaster_timeline(
    disaster, lista_de_isps, figsize: tuple[int, int] = (14, 6)
) -> plt.Figure:
    """Timeline showing disaster events and datacenter migrations.

    Args:
        disaster: Disaster object
        lista_de_isps: List of ISP objects
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot disaster events
    node_events = [e for e in disaster.eventos if e.get("tipo") == "node"]
    link_events = [e for e in disaster.eventos if e.get("tipo") == "link"]

    if node_events:
        node_times = [e["start_time"] for e in node_events]
        ax.scatter(
            node_times,
            [1] * len(node_times),
            s=100,
            marker="x",
            color="red",
            label="Node Failure",
            zorder=3,
        )

    if link_events:
        link_times = [e["start_time"] for e in link_events]
        ax.scatter(
            link_times,
            [0.9] * len(link_times),
            s=100,
            marker="s",
            color="orange",
            label="Link Failure",
            zorder=3,
        )

    # Plot datacenter migrations
    for isp in lista_de_isps:
        if isp.datacenter is not None:
            migration_time = isp.datacenter.tempo_de_reacao
            ax.scatter(
                [migration_time],
                [0.8],
                s=150,
                marker="^",
                color="blue",
                alpha=0.7,
                label=f"ISP {isp.isp_id} Migration",
            )

    # Disaster duration
    ax.axvspan(
        disaster.start,
        disaster.start + disaster.duration,
        alpha=0.2,
        color="red",
        label="Disaster Period",
    )

    ax.set_xlabel("Time")
    ax.set_ylabel("Event Type")
    ax.set_title("Disaster and Migration Timeline")
    ax.set_yticks([0.8, 0.9, 1.0])
    ax.set_yticklabels(["Migration", "Link Failure", "Node Failure"])
    ax.set_ylim([0.7, 1.1])
    ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1))
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    return fig


def plot_traffic_comparison_summary(
    dataframes: dict[str, pd.DataFrame], figsize: tuple[int, int] = (14, 5)
) -> plt.Figure:
    """Create summary comparison of traffic metrics.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)

    scenarios = list(dataframes.keys())

    total_requests = [len(df) for df in dataframes.values()]
    blocked_requests = [df["bloqueada"].sum() for df in dataframes.values()]
    blocking_rates = [df["bloqueada"].mean() for df in dataframes.values()]

    # Total requests
    axes[0].bar(scenarios, total_requests, color=["#3498db", "#e74c3c"])
    axes[0].set_ylabel("Count")
    axes[0].set_title("Total Requests")
    axes[0].grid(axis="y", alpha=0.3)

    # Blocked requests
    axes[1].bar(scenarios, blocked_requests, color=["#e67e22", "#c0392b"])
    axes[1].set_ylabel("Count")
    axes[1].set_title("Blocked Requests")
    axes[1].grid(axis="y", alpha=0.3)

    # Blocking rate
    axes[2].bar(scenarios, blocking_rates, color=["#e74c3c", "#c0392b"])
    axes[2].set_ylabel("Rate")
    axes[2].set_title("Blocking Rate")
    axes[2].set_ylim([0, max(1.0, max(blocking_rates) * 1.2)])
    axes[2].grid(axis="y", alpha=0.3)

    # Add percentage labels
    for i, v in enumerate(blocking_rates):
        axes[2].text(i, v + 0.02, f"{v:.1%}", ha="center", va="bottom")

    plt.tight_layout()
    return fig


def plot_request_distribution(
    dataframes: dict[str, pd.DataFrame], figsize: tuple[int, int] = (12, 6)
) -> plt.Figure:
    """Plot stacked bar chart of accepted vs blocked requests.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    scenarios = list(dataframes.keys())
    accepted = [(~df["bloqueada"]).sum() for df in dataframes.values()]
    blocked = [df["bloqueada"].sum() for df in dataframes.values()]

    x = np.arange(len(scenarios))

    ax.bar(x, accepted, label="Accepted", color="#2ecc71")
    ax.bar(x, blocked, bottom=accepted, label="Blocked", color="#e74c3c")

    ax.set_ylabel("Number of Requests")
    ax.set_title("Request Distribution")
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    return fig
