"""EON Network Simulator - Elastic Optical Network Simulator.

A comprehensive simulation framework for Elastic Optical Networks with
disaster recovery capabilities.
"""

# Core components
from simulador.core import PathManager, Request, Topology

# Entities
from simulador.entities import ISP, Datacenter, Disaster, Scenario

# Generators
from simulador.generators import (
    DatacenterGenerator,
    DisasterGenerator,
    ISPGenerator,
    ScenarioGenerator,
    TrafficGenerator,
)

# Routing
from simulador.routing import (
    FirstFit,
    FirstFitBestFit,
    FirstFitBestFitDisasterAware,
    FirstFitDisasterAware,
    FirstFitSubnet,
    FirstFitSubnetDisasterAware,
    RoutingBase,
)

# Utils
from simulador.utils import Logger, Metrics

__version__ = "0.1.0"

__all__ = [
    # Core
    "PathManager",
    "Request",
    "Topology",
    # Entities
    "ISP",
    "Datacenter",
    "Disaster",
    "Scenario",
    # Generators
    "ScenarioGenerator",
    "TrafficGenerator",
    "DisasterGenerator",
    "DatacenterGenerator",
    "ISPGenerator",
    # Routing
    "RoutingBase",
    "FirstFit",
    "FirstFitBestFit",
    "FirstFitBestFitDisasterAware",
    "FirstFitDisasterAware",
    "FirstFitSubnet",
    "FirstFitSubnetDisasterAware",
    # Utils
    "Logger",
    "Metrics",
]
