
from abc import ABC, abstractmethod
from Requisicao.Requisicao import Requisicao
from simpy import Environment
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Topology.Topologia import Topologia

class iRoteamento(ABC):

    
    @abstractmethod
    def rotear_requisicao(self, requisicao: Requisicao, topology: 'Topologia', env: Environment) -> bool:
        pass

    @abstractmethod
    def rerotear_requisicao(self, requisicao: Requisicao, topology: 'Topologia', env: Environment) -> bool:
        pass

    @abstractmethod
    def __str__(self):
        pass