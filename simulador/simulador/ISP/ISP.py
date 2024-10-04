
import numpy as np
import networkx as nx
from Variaveis import *

from Roteamento.Roteamento import Roteamento
from Roteamento.iRoteamento import iRoteamento
from Roteamento.RoteamentoDesastre import RoteamentoDesastre
from Datacenter.Datacenter import Datacenter
from Datacenter.GeradorDeDatacenter import GeradorDeDatacenter

from typing import TYPE_CHECKING, Generator
if TYPE_CHECKING:
    from Simulador import Simulador
    from Desastre.Desastre import Desastre

    

class ISP:
    def __init__(self, id: int, nodes: list[int], edges:list[tuple[int,int]], roteamento_de_desastre: 'iRoteamento' = Roteamento) -> None:
        self.id: int = id
        self.nodes: list[int] = nodes
        self.edges: list[tuple[ int, int ]]  = edges
        self.roteamento_atual :'iRoteamento' = Roteamento
        self.roteamento_primario :'iRoteamento' = Roteamento
        self.roteamento_desastre :'iRoteamento' = roteamento_de_desastre
        self.datacenter :Datacenter = None


    def define_datacenter(self, disaster: 'Desastre', topology: nx.Graph, specific_values = None) -> None:
        self.datacenter = GeradorDeDatacenter.gerar_datacenter(disaster, topology, self.nodes, specific_values)

    def iniciar_migracao(self, simulador :'Simulador') -> Generator:
        while(True):
            if simulador.env.now >= self.datacenter.tempo_de_reacao:
                self.roteamento_atual = self.roteamento_desastre
                self.datacenter.iniciar_migracao(simulador, self)
                break
            yield simulador.env.timeout(1)
    
    def imprime_ISP(self) -> None:
        print("ID: ", self.id)
        print("Nós: ", self.nodes)
        print("Arestas: ", self.edges)
        print("Datacenter source: ", self.datacenter.source)
        print("Datacenter destination: ", self.datacenter.destination)



    def troca_roteamento_desastre(self, roteamento: 'iRoteamento') -> None:
        self.roteamento_desastre = roteamento
