from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from simulador.Requisicao.requisicao import Requisicao
from simpy import Environment

if TYPE_CHECKING:
    from simulador.Topology.Topologia import Topologia


class IRoteamento(ABC):
    """Interface for router classes that route network requests.

    This abstract base class defines the methods that must be implemented by any
    class that provides routing functionality.
    """

    @staticmethod
    @abstractmethod
    def rotear_requisicao(
        requisicao: Requisicao, topology: "Topologia", env: Environment
    ) -> bool:
        """Route a request using the appropriate ISP router.

        Args:
            requisicao: Network request to route

        Returns:
            bool: True if the request was routed successfully, False otherwise
        """
        pass

    @staticmethod
    @abstractmethod
    def rerotear_requisicao(
        requisicao: Requisicao, topology: "Topologia", env: Environment
    ) -> bool:
        """Reroute a request using the appropriate ISP router.

        Args:
            requisicao: Network request to reroute

        Returns:
            bool: True if the request was rerouted successfully, False otherwise
        """
        pass

    @staticmethod
    @abstractmethod
    def __str__():
        """Return a string representation of the router.

        Returns:
            str: String representation of the router
        """
        pass
