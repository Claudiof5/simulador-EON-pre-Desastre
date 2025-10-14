from typing import TYPE_CHECKING

from simpy import Environment

from simulador.core.request import Request
from simulador.routing.base import RoutingBase

if TYPE_CHECKING:
    from simulador import Topology


class FirstFitDisaster(RoutingBase):
    @staticmethod
    def rotear_requisicao(
        requisicao: Request, topology: "Topology", env: Environment
    ) -> bool:
        # TODO: Implement disaster routing logic
        return False

    @staticmethod
    def rerotear_requisicao(
        requisicao: Request, topology: "Topology", env: Environment
    ) -> bool:
        # TODO: Implement disaster rerouting logic
        return False

    @staticmethod
    def __str__() -> str:
        return "FirstFitDisaster"
