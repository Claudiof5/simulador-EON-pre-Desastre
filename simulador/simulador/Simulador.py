
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


class Simulador:

    def __init__(self, env: simpy.Environment, topology: nx.Graph, status_logger: bool = False, cenario: Cenario = None ) -> None:
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
        
        numero_de_requisicao = len(self.lista_de_requisicoes) if self.lista_de_requisicoes != None else NUMERO_DE_REQUISICOES 
        for index_requisicao in range( 1, numero_de_requisicao + 1 ):

            yield from self.cria_e_roteia_requisicao( index_requisicao )

        self.simulacao_finalizada = True

    def cria_e_roteia_requisicao(self, index_requisicao) -> Generator:
        requisicao: Requisicao = self.pegar_requisicao( self.topology, index_requisicao )
        yield self.espera_requisicao( requisicao )
        self.roteia_requisicao( requisicao )

        Logger.mensagem_acompanha_requisicoes( index_requisicao, self.env.now, 10000 )

    def espera_requisicao(self, requisicao: Requisicao) -> simpy.events.Event:
        if self.lista_de_requisicoes:
            return self.env.timeout( requisicao.tempo_criacao - self.env.now )
        else:
            return self.env.timeout(random.expovariate( REQUISICOES_POR_SEGUNDO ) )

    def pegar_requisicao(self, topology: Topologia, req_id: int) -> Requisicao:
        
        if self.lista_de_requisicoes:
            requisicao = self.lista_de_requisicoes.pop(0)
            Registrador.adiciona_requisicao( requisicao )
            return requisicao
        else:
            requisicao = GeradorDeTrafego.gerar_requisicao( topology, req_id )
            Registrador.adiciona_requisicao( requisicao )
            return requisicao
    
    def pega_roteador(self, requisicao: Requisicao) -> iRoteamento:
        return self.lista_de_ISPs[ requisicao.src_ISP_index ].roteamento_atual
    
    def roteia_requisicao(self, requisicao: Requisicao ) -> None:
        
        roteador: iRoteamento = self.pega_roteador( requisicao )

        roteador.rotear_requisicao( requisicao, self.topology, self.env )

    def salvar_dataframe( self, nome: str ) -> None:
        return Registrador.criar_dataframe( nome )
    
    