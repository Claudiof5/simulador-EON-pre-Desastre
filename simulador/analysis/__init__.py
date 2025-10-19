"""Analysis utilities for network simulation results.

This package provides comprehensive analysis tools:

Modules:
    - topology_analysis: Network structure, critical nodes, partitions
    - metrics_calculator: Availability, blocking rates, degradation metrics
    - dataframe_filters: Filter and slice data by time, node, distance
    - reporters: Formatted console output and reports
"""

from __future__ import annotations

from simulador.analysis import (
    dataframe_filters,
    metrics_calculator,
    reporters,
    topology_analysis,
)

__all__ = [
    "dataframe_filters",
    "metrics_calculator",
    "reporters",
    "topology_analysis",
]
