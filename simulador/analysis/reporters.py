"""Reporting utilities for console output.

This module provides formatted console output for simulation results,
statistics, and comparisons.
"""

from __future__ import annotations

import networkx as nx
import pandas as pd

from simulador.analysis import metrics_calculator


def print_simulation_summary(
    dataframe: pd.DataFrame, scenario_name: str = "Scenario"
) -> None:
    """Print high-level summary of simulation results.

    Args:
        dataframe: Simulation results
        scenario_name: Name of the scenario for display
    """
    total = len(dataframe)
    blocked = dataframe["bloqueada"].sum()
    accepted = total - blocked
    blocking_rate = dataframe["bloqueada"].mean()
    availability = 1.0 - blocking_rate

    print(f"\n{'=' * 60}")
    print(f"  {scenario_name} - Simulation Summary")
    print(f"{'=' * 60}")
    print(f"  Total Requests:    {total:,}")
    print(f"  Accepted:          {accepted:,} ({accepted / total * 100:.1f}%)")
    print(f"  Blocked:           {blocked:,} ({blocked / total * 100:.1f}%)")
    print(f"  Blocking Rate:     {blocking_rate:.4f}")
    print(f"  Availability:      {availability:.4f} ({availability * 100:.2f}%)")
    print(f"{'=' * 60}\n")


def print_disaster_phase_report(
    dataframe: pd.DataFrame,
    disaster_start: float,
    disaster_end: float,
    scenario_name: str = "Scenario",
) -> None:
    """Print detailed report for before/during/after disaster phases.

    Args:
        dataframe: Simulation results
        disaster_start: Disaster start time
        disaster_end: Disaster end time
        scenario_name: Name of the scenario
    """
    before, during, after = (
        metrics_calculator.calculate_availability_before_during_after(
            dataframe, disaster_start, disaster_end
        )
    )

    before_df = dataframe[dataframe["tempo_criacao"] < disaster_start]
    during_df = dataframe[
        (dataframe["tempo_criacao"] >= disaster_start)
        & (dataframe["tempo_criacao"] < disaster_end)
    ]
    after_df = dataframe[dataframe["tempo_criacao"] >= disaster_end]

    print(f"\n{'=' * 70}")
    print(f"  {scenario_name} - Disaster Phase Analysis")
    print(f"{'=' * 70}")
    print(f"  Disaster Period: {disaster_start:.1f}s - {disaster_end:.1f}s")
    print(f"{'=' * 70}")

    # Before phase
    print("\n  BEFORE DISASTER:")
    print(f"    Time Range:     0s - {disaster_start:.1f}s")
    print(f"    Requests:       {len(before_df):,}")
    print(f"    Availability:   {before:.4f} ({before * 100:.2f}%)")
    print(f"    Blocking Rate:  {1 - before:.4f}")

    # During phase
    print("\n  DURING DISASTER:")
    print(f"    Time Range:     {disaster_start:.1f}s - {disaster_end:.1f}s")
    print(f"    Requests:       {len(during_df):,}")
    print(f"    Availability:   {during:.4f} ({during * 100:.2f}%)")
    print(f"    Blocking Rate:  {1 - during:.4f}")

    if before > 0:
        degradation = ((during - before) / before) * 100
        print(f"    Degradation:    {degradation:+.1f}% vs. before")

    # After phase
    print("\n  AFTER DISASTER:")
    print(f"    Time Range:     {disaster_end:.1f}s - end")
    print(f"    Requests:       {len(after_df):,}")
    print(f"    Availability:   {after:.4f} ({after * 100:.2f}%)")
    print(f"    Blocking Rate:  {1 - after:.4f}")

    if before > 0:
        recovery = ((after - before) / before) * 100
        print(f"    Recovery:       {recovery:+.1f}% vs. before")

    print(f"{'=' * 70}\n")


def print_scenario_comparison(dataframes: dict[str, pd.DataFrame]) -> None:
    """Print side-by-side comparison of multiple scenarios.

    Args:
        dataframes: Dictionary mapping scenario names to result dataframes
    """
    print(f"\n{'=' * 80}")
    print("  Scenario Comparison")
    print(f"{'=' * 80}")

    # Header
    scenarios = list(dataframes.keys())
    header = f"  {'Metric':<30}"
    for name in scenarios:
        header += f" {name:>20}"
    print(header)
    print(f"  {'-' * 78}")

    # Metrics
    metrics = {}
    for name, df in dataframes.items():
        total = len(df)
        blocked = df["bloqueada"].sum()
        availability = 1.0 - df["bloqueada"].mean()

        metrics[name] = {
            "Total Requests": total,
            "Blocked": blocked,
            "Accepted": total - blocked,
            "Blocking Rate": df["bloqueada"].mean(),
            "Availability": availability,
        }

    # Print rows
    for metric_name in [
        "Total Requests",
        "Accepted",
        "Blocked",
        "Blocking Rate",
        "Availability",
    ]:
        row = f"  {metric_name:<30}"
        for scenario in scenarios:
            value = metrics[scenario][metric_name]
            if metric_name in ["Blocking Rate", "Availability"]:
                row += f" {value:>19.4f}"
            else:
                row += f" {value:>20,}"
        print(row)

    print(f"{'=' * 80}\n")


def print_topology_summary(topology) -> None:
    """Print network topology statistics.

    Args:
        topology: NetworkX graph
    """
    print(f"\n{'=' * 60}")
    print("  Network Topology Summary")
    print(f"{'=' * 60}")
    print(f"  Nodes:              {topology.number_of_nodes()}")
    print(f"  Edges:              {topology.number_of_edges()}")

    degrees = [d for _, d in topology.degree()]
    print(f"  Average Degree:     {sum(degrees) / len(degrees):.2f}")
    print(f"  Min Degree:         {min(degrees)}")
    print(f"  Max Degree:         {max(degrees)}")

    try:
        diameter = nx.diameter(topology)
        print(f"  Diameter:           {diameter}")
    except nx.NetworkXError:
        print("  Diameter:           N/A (graph not connected)")

    try:
        avg_path = nx.average_shortest_path_length(topology)
        print(f"  Avg Path Length:    {avg_path:.2f}")
    except nx.NetworkXError:
        print("  Avg Path Length:    N/A (graph not connected)")

    print(f"  Connected:          {nx.is_connected(topology)}")
    print(f"{'=' * 60}\n")


def print_node_statistics(dataframe: pd.DataFrame, topology, top_n: int = 10) -> None:
    """Print per-node statistics.

    Args:
        dataframe: Simulation results
        topology: Network topology
        top_n: Number of top nodes to display
    """
    avail_by_node = metrics_calculator.calculate_availability_by_node(dataframe)

    # Get degree for each node
    degrees = dict(topology.degree())

    # Combine and sort
    node_stats = []
    for node, avail in avail_by_node.items():
        node_stats.append(
            {"node": node, "availability": avail, "degree": degrees.get(node, 0)}
        )

    # Sort by availability (lowest first for problem nodes)
    node_stats.sort(key=lambda x: x["availability"])

    print(f"\n{'=' * 70}")
    print(f"  Node Statistics (Bottom {top_n} by Availability)")
    print(f"{'=' * 70}")
    print(f"  {'Node ID':>8}  {'Availability':>15}  {'Degree':>10}")
    print(f"  {'-' * 68}")

    for stat in node_stats[:top_n]:
        print(
            f"  {stat['node']:>8}  {stat['availability']:>15.4f}  {stat['degree']:>10}"
        )

    print(f"{'=' * 70}\n")


def print_execution_time_report(start_time: float, end_time: float) -> None:
    """Print execution time report.

    Args:
        start_time: Simulation start timestamp
        end_time: Simulation end timestamp
    """
    duration = end_time - start_time

    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = duration % 60

    print(f"\n{'=' * 60}")
    print("  Execution Time")
    print(f"{'=' * 60}")

    if hours > 0:
        print(f"  Total Time: {hours}h {minutes}m {seconds:.2f}s")
    elif minutes > 0:
        print(f"  Total Time: {minutes}m {seconds:.2f}s")
    else:
        print(f"  Total Time: {seconds:.2f}s")

    print(f"  Total Seconds: {duration:.3f}s")
    print(f"{'=' * 60}\n")
