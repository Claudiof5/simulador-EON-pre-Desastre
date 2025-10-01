from typing import TYPE_CHECKING

from Requisicao import Requisicao
from Roteamento.IRoteamento import IRoteamento

if TYPE_CHECKING:
    from Topology.Topologia import Topologia


class RoteamentoDesastre(IRoteamento):
    def __init__(self, topology):
        self.topology = topology

    def rotear_requisicao(self, requisicao: Requisicao, topology: "Topologia") -> bool:
        pass

    def rerotear_requisicao(
        self, requisicao: Requisicao, topology: "Topologia"
    ) -> bool:
        pass
