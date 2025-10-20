"""Traffic and blocking visualization functions.

This module provides plotting utilities for visualizing traffic patterns,
blocking rates, and network utilization over time.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from simulador.analysis import metrics_calculator


def add_disaster_and_migration_markers(
    ax: plt.Axes,
    scenario: object | None = None,
    disaster_start: float | None = None,
    disaster_end: float | None = None,
    migration_times: list[tuple[float, int]] | None = None,
    show_legend: bool = True,
) -> None:
    """Add vertical lines marking disaster and migration events to a plot.

    Args:
        ax: Matplotlib axes to add markers to
        scenario: Optional Scenario object to auto-extract timing info
        disaster_start: Manual disaster start time (overrides scenario)
        disaster_end: Manual disaster end time (overrides scenario)
        migration_times: List of (time, isp_id) tuples for migration events
        show_legend: Whether to show legend for markers
    """
    # Extract disaster timing from scenario if needed
    if scenario is not None and hasattr(scenario, "desastre"):
        if disaster_start is None and hasattr(scenario.desastre, "start"):
            disaster_start = scenario.desastre.start

        if disaster_end is None and hasattr(scenario.desastre, "duration"):
            disaster_end = scenario.desastre.start + scenario.desastre.duration

    # Extract migration times from scenario if needed
    if (
        migration_times is None
        and scenario is not None
        and hasattr(scenario, "lista_de_isps")
    ):
        migration_times = _extract_migration_times(scenario.lista_de_isps)

    # Add disaster markers
    if disaster_start is not None:
        ax.axvline(
            disaster_start,
            color="black",
            linestyle="--",
            linewidth=1,
            alpha=0.7,
            label="Disaster Start",
        )

    if disaster_end is not None:
        ax.axvline(
            disaster_end,
            color="black",
            linestyle="--",
            linewidth=1,
            alpha=0.7,
            label="Disaster End",
        )

    # Add migration markers
    if migration_times:
        for idx, (time, _) in enumerate(migration_times):
            label = "Migration Start" if idx == 0 else None
            ax.axvline(
                time,
                color="red",
                linestyle="--",
                linewidth=1,
                alpha=0.5,
                label=label,
            )

    # Add legend if markers were added and legend doesn't exist
    has_markers = disaster_start or disaster_end or migration_times
    if show_legend and has_markers and ax.get_legend() is None:
        ax.legend()


def _extract_migration_times(lista_de_isps) -> list[tuple[float, int]]:
    """Extract migration times from list of ISPs."""
    migration_times = []
    for isp in lista_de_isps:
        has_datacenter = hasattr(isp, "datacenter") and isp.datacenter is not None
        has_reaction_time = has_datacenter and hasattr(
            isp.datacenter, "tempo_de_reacao"
        )
        if has_reaction_time:
            migration_times.append((isp.datacenter.tempo_de_reacao, isp.isp_id))
    return migration_times


def _calculate_usage_at_time_points(
    filtered_df: pd.DataFrame,
    time_points: np.ndarray,
    total_slots: int,
    isp_id: int | None = None,
) -> list[float]:
    """Calculate network usage at each time point.

    Args:
        filtered_df: DataFrame with slots_used, tempo_criacao, tempo_desalocacao columns
        time_points: Array of time points to sample
        total_slots: Total number of slots in the network
        isp_id: If provided, only count requests from this ISP (uses src_isp_index column)

    Returns:
        List of usage values (fraction of total slots)
    """
    usage = []
    for t in time_points:
        mask = (filtered_df["tempo_criacao"] <= t) & (
            filtered_df["tempo_desalocacao"] > t
        )

        if isp_id is not None:
            # Use src_isp_index column to filter by ISP
            mask = mask & (filtered_df["src_isp_index"] == isp_id)

        current_requisitions = filtered_df[mask]
        usage.append(current_requisitions["slots_used"].sum() / total_slots)

    return usage


def _apply_sliding_window(
    usage_data: list[float],
    time_points: np.ndarray,
    window_points: np.ndarray,
    window_size: float,
) -> list[float]:
    """Apply sliding window averaging to usage data.

    Args:
        usage_data: Usage values at each time point
        time_points: Time points corresponding to usage data
        window_points: Window center points
        window_size: Size of averaging window

    Returns:
        Averaged usage values at window points
    """
    avg_usage = []
    for t in window_points:
        start_time = max(10, t - window_size)
        end_time = t
        indices_in_window = (time_points >= start_time) & (time_points <= end_time)
        avg = np.mean(np.array(usage_data)[indices_in_window])
        avg_usage.append(avg)
    return avg_usage


def _extract_isp_dict(isp_data: dict | object | None) -> dict[int, dict] | None:
    """Extract ISP dictionary from various input formats.

    Args:
        isp_data: Either an ISP dict or a Scenario object

    Returns:
        ISP dictionary {isp_id: {}} or None (only ISP IDs needed, data uses src_isp_index)
    """
    if isp_data is None:
        return None

    if hasattr(isp_data, "lista_de_isps"):
        # Extract ISP IDs from Scenario
        # We don't need node info since we use src_isp_index from dataframe
        isp_dict = {}
        for isp in isp_data.lista_de_isps:
            isp_dict[isp.isp_id] = {}
        return isp_dict

    # Assume it's already a dict with ISP IDs as keys
    return isp_data


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


def plot_blocking_percentage_over_time(
    dataframe: pd.DataFrame,
    time_window: float = 5.0,
    scenario: object | None = None,
    disaster_start: float | None = None,
    disaster_end: float | None = None,
    migration_times: list[tuple[float, int]] | None = None,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """Plot blocking percentage over time with disaster and migration markers.

    Args:
        dataframe: Simulation results with 'bloqueada' and 'tempo_criacao' columns
        time_window: Size of time window for averaging (default 30.0 seconds)
        scenario: Optional Scenario object to auto-extract disaster and migration times
        disaster_start: Manual disaster start time (overrides scenario)
        disaster_end: Manual disaster end time (overrides scenario)
        migration_times: List of (time, isp_id) tuples for migration events
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    # Sort by creation time
    df_sorted = dataframe.sort_values("tempo_criacao").copy()

    # Create time buckets
    min_time = df_sorted["tempo_criacao"].min()
    df_sorted["time_bucket"] = (
        (df_sorted["tempo_criacao"] - min_time) // time_window
    ).astype(int)

    # Calculate blocking percentage per bucket
    bucket_stats = df_sorted.groupby("time_bucket").agg(
        {"bloqueada": ["sum", "count"], "tempo_criacao": "mean"}
    )

    bucket_times = bucket_stats[("tempo_criacao", "mean")].values
    blocked_count = bucket_stats[("bloqueada", "sum")].values
    total_count = bucket_stats[("bloqueada", "count")].values
    blocking_percentage = (blocked_count / total_count) * 100

    # Create plot
    fig, ax = plt.subplots(figsize=figsize)

    # Add disaster and migration timing markers
    add_disaster_and_migration_markers(
        ax,
        scenario=scenario,
        disaster_start=disaster_start,
        disaster_end=disaster_end,
        migration_times=migration_times,
        show_legend=True,
    )

    # Plot blocking percentage line
    ax.plot(
        bucket_times,
        blocking_percentage,
        linewidth=2.5,
        color="#e74c3c",
        label="Blocking Rate",
        marker="o",
        markersize=4,
    )

    ax.set_xlabel("Tempo (segundos)")
    ax.set_ylabel("Taxa de Bloqueio (%)")
    ax.set_title(
        f"Porcentagem de Requisições Bloqueadas ao Longo do Tempo (janela de {time_window}s)"
    )
    ax.set_ylim([0, max(105, blocking_percentage.max() * 1.1)])
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    plt.tight_layout()


def plot_network_usage(
    dataframe: pd.DataFrame,
    topology,
    numero_de_slots: int,
    time_step: float = 0.1,
    window_size: float = 10,
    scenario: object | None = None,
    isp_data: dict[int, dict] | object | None = None,
    show_per_isp: bool = False,
    disaster_start: float | None = None,
    disaster_end: float | None = None,
    migration_times: list[tuple[float, int]] | None = None,
    figsize: tuple[int, int] = (14, 6),
) -> plt.Figure:
    """Plot average network slot usage over time with sliding window.

    When show_per_isp=True, displays one line per ISP showing their contribution
    to total network usage. The sum of all ISP lines equals the total line at each
    time point, since each request is attributed to exactly one ISP based on the
    'src_isp_index' column.

    Args:
        dataframe: Simulation results with 'bloqueada', 'numero_de_slots',
                   'tamanho_do_caminho', 'tempo_criacao', 'tempo_desalocacao',
                   'src_isp_index' columns
        topology: Network topology (NetworkX graph)
        numero_de_slots: Total number of slots per link
        time_step: Time step for sampling (default 0.1)
        window_size: Window size for moving average (default 10)
        scenario: Optional Scenario object to auto-extract disaster and migration times
        isp_data: ISP dict or Scenario for per-ISP breakdown (required if show_per_isp=True)
        show_per_isp: If True, show separate lines for each ISP's slot usage
        disaster_start: Manual disaster start time (overrides scenario)
        disaster_end: Manual disaster end time (overrides scenario)
        migration_times: List of (time, isp_id) tuples for migration events
        figsize: Figure size

    Returns:
        Matplotlib figure

    Note:
        All usage values (total and per-ISP) are normalized by the total network
        capacity (num_links × num_slots). This means:
        - Total line shows: (sum of all allocated slots) / (total network slots)
        - ISP k line shows: (sum of ISP k's allocated slots) / (total network slots)
        - Mathematical property: sum(all ISP lines) = total line at each time point
    """
    # Extract ISP data if needed for per-ISP breakdown
    isp_dict = None
    if show_per_isp:
        isp_dict = _extract_isp_dict(isp_data if isp_data is not None else scenario)

    # Filter for non-blocked paths
    filtered_dataframe = dataframe[~dataframe["bloqueada"]].copy()
    filtered_dataframe["slots_used"] = (
        filtered_dataframe["numero_de_slots"] * filtered_dataframe["tamanho_do_caminho"]
    )

    # Keep src_isp_index column if doing per-ISP analysis
    if show_per_isp and isp_dict:
        filtered_dataframe = filtered_dataframe[
            ["slots_used", "tempo_criacao", "tempo_desalocacao", "src_isp_index"]
        ]
    else:
        filtered_dataframe = filtered_dataframe[
            ["slots_used", "tempo_criacao", "tempo_desalocacao"]
        ]

    max_time = max(
        filtered_dataframe["tempo_desalocacao"].max(),
        filtered_dataframe["tempo_criacao"].max(),
    )
    numero_total_de_slots = len(topology.edges()) * numero_de_slots
    time_points = np.arange(10, max_time + time_step, time_step)
    window_points = np.arange(10, max_time + window_size, window_size)

    # Calculate overall network usage
    # Note: This is the sum of ALL allocated slots / total network capacity
    network_usage = _calculate_usage_at_time_points(
        filtered_dataframe, time_points, numero_total_de_slots
    )
    avg_network_usage = _apply_sliding_window(
        network_usage, time_points, window_points, window_size
    )

    # Calculate per-ISP usage if requested
    # Important: Each ISP's usage is also normalized by total_network_capacity,
    # so sum(all ISP usages) = total usage at each time point
    # This allows comparing ISP contributions on the same scale
    # Uses src_isp_index column to correctly attribute requests to ISPs
    isp_avg_usage = {}
    if show_per_isp and isp_dict:
        for isp_id in isp_dict:
            isp_usage = _calculate_usage_at_time_points(
                filtered_dataframe, time_points, numero_total_de_slots, isp_id
            )
            isp_avg_usage[isp_id] = _apply_sliding_window(
                isp_usage, time_points, window_points, window_size
            )

    # Create plot
    fig, ax = plt.subplots(figsize=figsize)

    # Add disaster and migration timing markers
    add_disaster_and_migration_markers(
        ax,
        scenario=scenario,
        disaster_start=disaster_start,
        disaster_end=disaster_end,
        migration_times=migration_times,
        show_legend=True,
    )

    # Plot overall usage
    if show_per_isp and isp_dict:
        # Show total as dashed line for comparison
        ax.plot(
            window_points,
            avg_network_usage,
            label="Total (All ISPs)",
            linewidth=2.5,
            linestyle="--",
            color="black",
            alpha=0.7,
        )
    else:
        # Show total as main line
        ax.plot(
            window_points, avg_network_usage, label="Uso médio de rede", linewidth=2
        )

    # Plot per-ISP usage
    if show_per_isp and isp_dict:
        colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]
        for idx, (isp_id, avg_usage) in enumerate(isp_avg_usage.items()):
            color = colors[idx % len(colors)]
            ax.plot(
                window_points,
                avg_usage,
                label=f"ISP {isp_id}",
                linewidth=2,
                color=color,
                alpha=0.8,
            )

    ax.set_title("Porcentagem média de slots de frequência alocados na rede pelo tempo")
    ax.set_xlabel("Tempo (segundos)")
    ax.set_ylabel("Porcentagem média de slots de frequência alocados")
    ax.set_ylim([0, 1.0])
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    plt.tight_layout()


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
