
from abc import ABC, abstractmethod
from Requisicao.Requisicao import Requisicao
from simpy import Environment
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Topologia import Topologia

class iRoteamento(ABC):

    
    @abstractmethod
    def rotear_requisicao(self, requisicao: Requisicao, topology: 'Topologia', env: Environment):
        pass

    def rerotear_requisicao(self, requisicao: Requisicao, topology: 'Topologia', env: Environment):
        pass