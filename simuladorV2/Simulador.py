
import simpy
import networkx as nx
import random
from Topologia import Topologia
from Requisicao.GeradorDeTrafico import GeradorDeTrafico
from Roteamento.iRoteamento import iRoteamento
from Desastre.Desastre import Desastre
from ISP.ISP import ISP
from Requisicao.Requisicao import Requisicao
from Variaveis import *
from Logger import Logger
from cenario.GeradorCenarioSimulacao import GeradorCenarioSimulacao, Cenario
from Registrador import Registrador

class Simulador:

    def __init__(self, env: simpy.Environment, topology: nx.Graph, status_logger: bool = False, cenario:Cenario = None ) -> None:
        Logger(status_logger)
        self.inicia_atributos( topology, env, cenario )
        self.simulacao_finalizada = False

    def inicia_atributos( self, topology: nx.Graph, env: simpy.Environment, cenario :Cenario = None ):
        if cenario == None:
            topology, lista_de_ISPs, desastre = GeradorCenarioSimulacao.gerar_cenario( topology, env )
            
        else:
            topology, lista_de_ISPs, desastre = cenario.retorna_atributos()

        self.env           :simpy.Environment = env
        self.lista_de_ISPs :list[ISP] = lista_de_ISPs
        self.desastre      :Desastre  = desastre
        self.topology      :Topologia = topology

    def run( self ):
        self.env.process( self._run() )
        self.env.run()

    def _run( self):
        self.desastre.iniciar_desastre( self )
        
        for req_id in range( 1, NUMERO_DE_REQUISICOES + 1 ):
            
            yield self.env.timeout(random.expovariate( REQUISICOES_POR_SEGUNDO ) )
            requisicao: Requisicao = GeradorDeTrafico.gerar_requisicao( self.topology, req_id )
            Registrador.adiciona_requisicao( requisicao )
            id_ISP_origem = requisicao.src_ISP_index
            roteador: iRoteamento = self.lista_de_ISPs[id_ISP_origem].roteamento
            roteador.rotear_requisicao( requisicao, self.topology )
            Logger.mensagem_acompanha_requisicoes( req_id, self.env.now, 10000 )

        self.simulacao_finalizada = True

    def salvar_dataframe(self):
        return Registrador.criar_dataframe()