"""Visualization utilities for simulation analysis.

This package provides plotting and visualization tools:

Modules:
    - availability_plots: Availability metrics across time, distance, nodes
    - traffic_plots: Traffic patterns, blocking rates, network utilization
    - topology_plots: Network topology visualization, ISPs, disasters, paths
"""

from __future__ import annotations

from simulador.visualization import availability_plots, topology_plots, traffic_plots

__all__ = [
    "availability_plots",
    "topology_plots",
    "traffic_plots",
]
