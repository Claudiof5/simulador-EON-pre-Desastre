
from Roteamento.iRoteamento import iRoteamento
from Requisicao import Requisicao
from Topologia import Topologia


class RoteamentoDesastre(iRoteamento):
    def __init__(self, topology):
        self.topology = topology

    def rotear_requisicao(self, requisicao: Requisicao, topology: Topologia):
        pass