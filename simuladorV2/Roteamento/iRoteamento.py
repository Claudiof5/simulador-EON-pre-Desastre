
from abc import ABC, abstractmethod
from Requisicao.Requisicao import Requisicao
from Topologia import Topologia

class iRoteamento(ABC):

    
    @abstractmethod
    def rotear_requisicao(self, requisicao: Requisicao, topology: Topologia):
        pass