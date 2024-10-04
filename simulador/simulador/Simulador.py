
from typing import Generator
import simpy
import networkx as nx
import random
from Topology.Topologia import Topologia
from Requisicao.GeradorDeTrafego import GeradorDeTrafego
from Roteamento.iRoteamento import iRoteamento
from Desastre.Desastre import Desastre
from ISP.ISP import ISP
from Requisicao.Requisicao import Requisicao
from Variaveis import *
from Logger import Logger
from Cenario.GeradorDeCenarios import GeradorDeCenarios
from Cenario.Cenario import Cenario
from Registrador import Registrador
from copy import deepcopy
import pickle

class Simulador:

    def __init__(self, env: simpy.Environment, topology: nx.Graph, status_logger: bool = False, cenario:Cenario = None ) -> None:
        Logger(status_logger)
        self.inicia_atributos( topology, env, cenario )
        self.simulacao_finalizada = False

    def inicia_atributos( self, topology: nx.Graph, env: simpy.Environment, cenario :Cenario = None ) -> None:
        if cenario == None:
            topology, lista_de_ISPs, desastre, lista_de_requisicoes = GeradorDeCenarios.gerar_cenario( topology)
        else:
            topology, lista_de_ISPs, desastre, lista_de_requisicoes = cenario.retorna_atributos()

        self.env: simpy.Environment = env
        self.lista_de_ISPs :list[ISP] = lista_de_ISPs
        self.desastre: Desastre  = desastre
        self.topology: Topologia = topology
        self.lista_de_requisicoes: list[Requisicao] = lista_de_requisicoes

    def run( self ) -> None:
        self.env.process( self._run() )
        self.env.run()

    def _run( self) -> Generator:
        self.desastre.iniciar_desastre( self )
        
        numero_de_iteracoes = len(self.lista_de_requisicoes) if self.lista_de_requisicoes != None else NUMERO_DE_REQUISICOES 
        for req_id in range( 1, numero_de_iteracoes + 1 ):
            
            yield self.env.timeout(random.expovariate( REQUISICOES_POR_SEGUNDO ) )
            requisicao: Requisicao = self.pegar_requisicao( self.topology, req_id )
            Registrador.adiciona_requisicao( requisicao )
            id_ISP_origem = requisicao.src_ISP_index
            roteador: iRoteamento = self.lista_de_ISPs[id_ISP_origem].roteamento_atual
            roteador.rotear_requisicao( requisicao, self.topology, self.env )
            Logger.mensagem_acompanha_requisicoes( req_id, self.env.now, 10000 )

        self.simulacao_finalizada = True

    def pegar_requisicao(self, topology: Topologia, req_id: int) -> Requisicao:
        
        if self.lista_de_requisicoes:
            return self.lista_de_requisicoes.pop(0)
        else:
            return GeradorDeTrafego.gerar_requisicao( topology, req_id )
    
    def salvar_dataframe( self, nome: str ) -> None:
        return Registrador.criar_dataframe( nome )
    

