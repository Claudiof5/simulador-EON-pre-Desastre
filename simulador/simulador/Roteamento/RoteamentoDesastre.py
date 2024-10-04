
from Roteamento.iRoteamento import iRoteamento
from Requisicao import Requisicao

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Topology.Topologia import Topologia
    
class RoteamentoDesastre(iRoteamento):
    def __init__(self, topology):
        self.topology = topology

    def rotear_requisicao(self, requisicao: Requisicao, topology: 'Topologia') -> bool:
        pass

    def rerotear_requisicao(self, requisicao: Requisicao, topology: 'Topologia') -> bool:
        pass