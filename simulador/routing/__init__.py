"""Routing algorithms for network traffic."""

from simulador.routing.base import RoutingBase
from simulador.routing.best_fit import FirstFitBestFit
from simulador.routing.best_fit_disaster_aware import FirstFitBestFitDisasterAware
from simulador.routing.first_fit import FirstFit
from simulador.routing.first_fit_disaster_aware import FirstFitDisasterAware
from simulador.routing.subnet import FirstFitSubnet
from simulador.routing.subnet_disaster_aware import FirstFitSubnetDisasterAware
from simulador.routing.subnet_weighted_disaster_aware import (
    FirstFitWeightedSubnetDisasterAware,
)

__all__ = [
    "RoutingBase",
    "FirstFit",
    "FirstFitBestFit",
    "FirstFitBestFitDisasterAware",
    "FirstFitDisasterAware",
    "FirstFitSubnet",
    "FirstFitSubnetDisasterAware",
    "FirstFitWeightedSubnetDisasterAware",
]
