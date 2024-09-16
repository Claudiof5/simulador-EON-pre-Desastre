
import simpy
import networkx as nx
import random
from Topologia import Topologia
from ISP.GeradorDeISPs import GeradorDeISPs
from Desastre.GeradorDeDesastre import GeradorDeDesastre
from Requisicao.GeradorDeTrafico import GeradorDeTrafico
from Roteamento.iRoteamento import iRoteamento
from Desastre.Desastre import Desastre
from ISP.ISP import ISP
from Requisicao.Requisicao import Requisicao
from Variaveis import *

class Simulador:

    def __init__(self, env :simpy.Environment, topology: nx.Graph, numero_de_ISPs: int, rate: int, num_of_requests: int ) -> None:
        self.env = env
        self.lista_de_ISPs :list[ISP] = GeradorDeISPs.gerar_lista_ISPs_aleatorias( topology, numero_de_ISPs )
        self.desastre      :Desastre  = GeradorDeDesastre.generate_disaster( topology, self.lista_de_ISPs )
        self.topology      :Topologia = Topologia( topology, self.lista_de_ISPs, NUMERO_DE_CAMINHOS, NUMERO_DE_SLOTS )
        self.requisicoes   :list[Requisicao] = []
        self.simulacao_finalizada = False



        env.process( self.Run( rate, num_of_requests ) )
        

    def Run( self, rate :float, num_of_requests :int ):
        self.desastre.iniciar_desastre( self )
        
        for req_id in range( 1, num_of_requests + 1 ):
            
            yield self.env.timeout(random.expovariate( rate ) )
            requisicao: Requisicao = GeradorDeTrafico.gerar_requisicao( self.topology, req_id )
            self.requisicoes.append( requisicao )
            id_ISP_origem = requisicao.src_ISP_index
            roteador :iRoteamento = self.lista_de_ISPs[id_ISP_origem].roteamento
            roteador.rotear_requisicao( self, requisicao, self.topology )
