"""Accumulated traffic visualization for comparing scenarios.

This module provides functions to plot and compare accumulated accepted traffic
between different scenarios over time.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def plot_accumulated_accepted_traffic(
    dataframe1: pd.DataFrame,
    dataframe2: pd.DataFrame,
    label1: str = "Scenario 1",
    label2: str = "Scenario 2",
    traffic_type: str = "all",
    metric: str = "bandwidth",
    scenario1=None,
    figsize: tuple[int, int] = (14, 8),
) -> plt.Figure:
    """Plot accumulated accepted traffic over time comparing two datasets.

    The plot ends at disaster start time and shows ISP migration start times as vertical lines.

    Args:
        dataframe1: First simulation results dataframe
        dataframe2: Second simulation results dataframe
        label1: Label for first dataset (default "Scenario 1")
        label2: Label for second dataset (default "Scenario 2")
        traffic_type: Type of traffic to analyze:
            - "all": All traffic
            - "migration": Only migration traffic
            - "normal": Only non-migration traffic
        metric: What to accumulate:
            - "bandwidth": Accumulated bandwidth (Gbps)
            - "requests": Accumulated number of requests
        scenario1: Optional Scenario object for disaster start time and ISP migration times
        figsize: Figure size (width, height)

    Returns:
        plt.Figure: The created figure

    Example:
        >>> fig = plot_accumulated_accepted_traffic(
        ...     dataframe1, dataframe2,
        ...     label1="FirstFitSubnet",
        ...     label2="WeightedDisasterAware",
        ...     traffic_type="migration",
        ...     metric="bandwidth",
        ...     scenario1=cenario1
        ... )
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Determine disaster start time
    disaster_start = None
    if scenario1 is not None:
        disaster_start = scenario1.desastre.start

    # Filter traffic type
    def filter_traffic(df: pd.DataFrame) -> pd.DataFrame:
        # Only accepted traffic
        df_filtered = df[df["bloqueada"] == False].copy()

        if traffic_type == "migration":
            df_filtered = df_filtered[df_filtered["requisicao_de_migracao"] == True]
        elif traffic_type == "normal":
            df_filtered = df_filtered[df_filtered["requisicao_de_migracao"] == False]

        return df_filtered

    # Process first dataset - limit to disaster start if available
    df1_filtered = filter_traffic(dataframe1)
    if disaster_start is not None:
        df1_filtered = df1_filtered[df1_filtered["tempo_criacao"] <= disaster_start]
    df1_sorted = df1_filtered.sort_values("tempo_criacao")

    if metric == "bandwidth":
        df1_sorted["accumulated"] = df1_sorted["bandwidth"].cumsum()
        ylabel = "Accumulated Bandwidth (Gbps)"
    else:  # requests
        df1_sorted["accumulated"] = range(1, len(df1_sorted) + 1)
        ylabel = "Accumulated Accepted Requests"

    # Process second dataset - limit to disaster start if available
    df2_filtered = filter_traffic(dataframe2)
    if disaster_start is not None:
        df2_filtered = df2_filtered[df2_filtered["tempo_criacao"] <= disaster_start]
    df2_sorted = df2_filtered.sort_values("tempo_criacao")

    if metric == "bandwidth":
        df2_sorted["accumulated"] = df2_sorted["bandwidth"].cumsum()
    else:  # requests
        df2_sorted["accumulated"] = range(1, len(df2_sorted) + 1)

    # Plot accumulated traffic
    ax.plot(
        df1_sorted["tempo_criacao"],
        df1_sorted["accumulated"],
        label=label1,
        linewidth=2,
        alpha=0.8,
    )
    ax.plot(
        df2_sorted["tempo_criacao"],
        df2_sorted["accumulated"],
        label=label2,
        linewidth=2,
        alpha=0.8,
    )

    # Title based on traffic type
    traffic_type_label = {
        "all": "All",
        "migration": "Migration",
        "normal": "Normal",
    }[traffic_type]
    title_suffix = f"Accumulated Accepted {traffic_type_label} Traffic Comparison"

    # Add disaster and ISP migration markers if scenario provided
    if scenario1 is not None:
        # Always show disaster start (plot ends here)
        ax.axvline(
            disaster_start,
            color="red",
            linestyle="--",
            linewidth=1.5,
            alpha=0.7,
            label="Disaster Start",
        )

        # Always show ISP migration start lines
        if hasattr(scenario1, "lista_de_isps"):
            # Use different colors for each ISP
            colors = ["green", "purple", "brown", "pink", "olive", "cyan"]
            for idx, isp in enumerate(scenario1.lista_de_isps):
                has_datacenter = (
                    hasattr(isp, "datacenter") and isp.datacenter is not None
                )
                has_reaction_time = has_datacenter and hasattr(
                    isp.datacenter, "tempo_de_reacao"
                )
                if has_reaction_time:
                    migration_time = isp.datacenter.tempo_de_reacao
                    color = colors[idx % len(colors)]
                    ax.axvline(
                        migration_time,
                        color=color,
                        linestyle=":",
                        linewidth=1.2,
                        alpha=0.6,
                        label=f"ISP {isp.isp_id} Migration",
                    )

    # Formatting
    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)

    # Title
    ax.set_title(
        title_suffix,
        fontsize=14,
        fontweight="bold",
    )

    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    # Add summary statistics
    final_value1 = df1_sorted["accumulated"].iloc[-1] if len(df1_sorted) > 0 else 0
    final_value2 = df2_sorted["accumulated"].iloc[-1] if len(df2_sorted) > 0 else 0

    if metric == "bandwidth":
        textstr = (
            f"{label1}: {final_value1:,.0f} Gbps\n{label2}: {final_value2:,.0f} Gbps"
        )
        diff = final_value2 - final_value1
        diff_pct = (diff / final_value1 * 100) if final_value1 > 0 else 0
        textstr += f"\nDifference: {diff:+,.0f} Gbps ({diff_pct:+.1f}%)"
    else:
        textstr = (
            f"{label1}: {final_value1:,} requests\n{label2}: {final_value2:,} requests"
        )
        diff = final_value2 - final_value1
        diff_pct = (diff / final_value1 * 100) if final_value1 > 0 else 0
        textstr += f"\nDifference: {diff:+,} requests ({diff_pct:+.1f}%)"

    # Add text box with statistics
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
    ax.text(
        0.02,
        0.98,
        textstr,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=props,
    )

    plt.tight_layout()
    return fig


def plot_accumulated_traffic_grid(
    dataframe1: pd.DataFrame,
    dataframe2: pd.DataFrame,
    label1: str = "Scenario 1",
    label2: str = "Scenario 2",
    scenario1=None,
    scenario2=None,
    figsize: tuple[int, int] = (16, 10),
) -> plt.Figure:
    """Plot a grid comparing accumulated traffic across different categories.

    Creates a 2x2 grid showing:
    - Top left: All traffic (bandwidth)
    - Top right: Migration traffic (bandwidth)
    - Bottom left: Normal traffic (bandwidth)
    - Bottom right: All traffic (request count)

    Args:
        dataframe1: First simulation results dataframe
        dataframe2: Second simulation results dataframe
        label1: Label for first dataset
        label2: Label for second dataset
        scenario1: Optional Scenario object for disaster markers
        scenario2: Optional Scenario object (unused, for compatibility)
        figsize: Figure size (width, height)

    Returns:
        plt.Figure: The created figure with 4 subplots

    Example:
        >>> fig = plot_accumulated_traffic_grid(
        ...     dataframe1, dataframe2,
        ...     label1="FirstFitSubnet",
        ...     label2="WeightedDisasterAware",
        ...     scenario1=cenario1
        ... )
    """
    fig, axes = plt.subplots(2, 2, figsize=figsize)

    # Configuration for each subplot
    configs = [
        ("all", "bandwidth", "All Traffic - Bandwidth"),
        ("migration", "bandwidth", "Migration Traffic - Bandwidth"),
        ("normal", "bandwidth", "Normal Traffic - Bandwidth"),
        ("all", "requests", "All Traffic - Request Count"),
    ]

    for idx, (traffic_type, metric, title) in enumerate(configs):
        row = idx // 2
        col = idx % 2
        ax = axes[row, col]

        # Filter traffic
        def filter_traffic(df: pd.DataFrame) -> pd.DataFrame:
            df_filtered = df[df["bloqueada"] == False].copy()
            if traffic_type == "migration":
                df_filtered = df_filtered[df_filtered["requisicao_de_migracao"] == True]
            elif traffic_type == "normal":
                df_filtered = df_filtered[
                    df_filtered["requisicao_de_migracao"] == False
                ]
            return df_filtered

        # Process datasets
        df1_filtered = filter_traffic(dataframe1)
        df1_sorted = df1_filtered.sort_values("tempo_criacao")

        df2_filtered = filter_traffic(dataframe2)
        df2_sorted = df2_filtered.sort_values("tempo_criacao")

        if metric == "bandwidth":
            df1_sorted["accumulated"] = df1_sorted["bandwidth"].cumsum()
            df2_sorted["accumulated"] = df2_sorted["bandwidth"].cumsum()
            ylabel = "Accumulated Bandwidth (Gbps)"
        else:
            df1_sorted["accumulated"] = range(1, len(df1_sorted) + 1)
            df2_sorted["accumulated"] = range(1, len(df2_sorted) + 1)
            ylabel = "Accumulated Requests"

        # Plot
        ax.plot(
            df1_sorted["tempo_criacao"],
            df1_sorted["accumulated"],
            label=label1,
            linewidth=2,
            alpha=0.8,
        )
        ax.plot(
            df2_sorted["tempo_criacao"],
            df2_sorted["accumulated"],
            label=label2,
            linewidth=2,
            alpha=0.8,
        )

        # Add disaster markers (only for first subplot to avoid legend clutter)
        if idx == 0 and scenario1 is not None:
            disaster_start = scenario1.desastre.start
            disaster_end = scenario1.desastre.start + scenario1.desastre.duration
            ax.axvline(
                disaster_start,
                color="red",
                linestyle="--",
                linewidth=1,
                alpha=0.5,
                label="Disaster",
            )
            ax.axvline(
                disaster_end, color="orange", linestyle="--", linewidth=1, alpha=0.5
            )
        elif scenario1 is not None:
            disaster_start = scenario1.desastre.start
            disaster_end = scenario1.desastre.start + scenario1.desastre.duration
            ax.axvline(
                disaster_start, color="red", linestyle="--", linewidth=1, alpha=0.5
            )
            ax.axvline(
                disaster_end, color="orange", linestyle="--", linewidth=1, alpha=0.5
            )

        # Formatting
        ax.set_xlabel("Time (seconds)", fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.suptitle(
        "Accumulated Accepted Traffic Comparison",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )
    plt.tight_layout()

    return fig
