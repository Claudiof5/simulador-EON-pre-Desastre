import pickle
from Topologia import Topologia
from Desastre.Desastre import Desastre
from Requisicao.Requisicao import Requisicao
from ISP.ISP import ISP
from copy import deepcopy
from Variaveis import *
from Roteamento.iRoteamento import iRoteamento


class Cenario:

    def __init__(self, topology: Topologia, lista_de_ISPs: list[ISP], desastre: Desastre, lista_de_requisicoes: list[Requisicao] = None) -> None:
        self.topology: Topologia = topology
        self.lista_de_ISPs: list[ISP] = lista_de_ISPs
        self.desastre: Desastre = desastre
        self.lista_de_requisicoes: list[Requisicao] = lista_de_requisicoes

    def retorna_atributos(self) -> tuple[Topologia, list[ISP], Desastre, list[Requisicao]]:
        return deepcopy((self.topology, self.lista_de_ISPs, self.desastre, self.lista_de_requisicoes))
    
    def imprime_atributos(self) -> None:
        self.topology.imprime_topologia()
        print("")
        self.desastre.imprime_desastre()
        print("")
        for isp in self.lista_de_ISPs:
            isp.imprime_ISP()
            print("")
        
    def troca_roteamento_lista_de_desastre( self, roteamento: 'iRoteamento') -> None:
        for isp in self.lista_de_ISPs:
            isp.troca_roteamento_desastre( roteamento )
    
    def salva_cenario(self, nome: str ) -> None:
        with open(f'cenario/cenarios/{nome}.pkl', 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def carrega_cenario(nome: str) -> 'Cenario':
        with open(f'cenario/cenarios/{nome}.pkl', 'rb') as f:
            return pickle.load(f)