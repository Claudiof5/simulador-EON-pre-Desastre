from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from simpy import Environment

from simulador.core.request import Request

if TYPE_CHECKING:
    from simulador import Topology


class RoutingBase(ABC):
    """Interface for router classes that route network requests.

    This abstract base class defines the methods that must be implemented by any
    class that provides routing functionality.
    """

    @staticmethod
    @abstractmethod
    def rotear_requisicao(
        requisicao: Request, topology: "Topology", env: Environment
    ) -> bool:
        """Route a request using the appropriate ISP router.

        Args:
            requisicao: Network request to route
            topology: Network topology
            env: Simulation environment

        Returns:
            bool: True if the request was routed successfully, False otherwise
        """
        pass

    @staticmethod
    @abstractmethod
    def rerotear_requisicao(
        requisicao: Request, topology: "Topology", env: Environment
    ) -> bool:
        """Reroute a request using the appropriate ISP router.

        Args:
            requisicao: Network request to reroute
            topology: Network topology
            env: Simulation environment

        Returns:
            bool: True if the request was rerouted successfully, False otherwise
        """
        pass

    @staticmethod
    @abstractmethod
    def __str__() -> str:
        """Return a string representation of the routing method.

        Returns:
            str: String representation of the router
        """
        pass
