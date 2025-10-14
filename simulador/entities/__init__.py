"""Network entities (ISP, Datacenter, Disaster, Scenario)."""

from simulador.entities.datacenter import Datacenter
from simulador.entities.disaster import Disaster
from simulador.entities.isp import ISP
from simulador.entities.scenario import Scenario

__all__ = ["ISP", "Datacenter", "Disaster", "Scenario"]
