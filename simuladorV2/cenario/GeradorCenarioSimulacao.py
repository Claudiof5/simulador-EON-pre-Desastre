
import simpy
import networkx as nx
from Topologia import Topologia
from ISP.GeradorDeISPs import GeradorDeISPs
from Desastre.GeradorDeDesastre import GeradorDeDesastre
from Desastre.Desastre import Desastre
from ISP.ISP import ISP
from copy import deepcopy
from Variaveis import *

class GeradorCenarioSimulacao:

    def gerar_cenario( topology: nx.Graph, env: simpy.Environment, retornar_objetos = False ) -> tuple[Topologia, list[ISP], Desastre]:
        lista_de_ISPs :list[ISP] = GeradorDeISPs.gerar_lista_ISPs_aleatorias( topology=topology, numero_de_ISPs=NUMERO_DE_ISPS )
        desastre      :Desastre  = GeradorDeDesastre.generate_disaster( topology, lista_de_ISPs )
        topology      :Topologia = Topologia( topology, lista_de_ISPs, NUMERO_DE_CAMINHOS, NUMERO_DE_SLOTS, env )

        for isp in lista_de_ISPs:
            isp.define_datacenter( desastre, topology.topology )

        if retornar_objetos:
            return Cenario(topology, lista_de_ISPs, desastre)
        else:
            return topology, lista_de_ISPs, desastre
        
class Cenario:

    def __init__(self, topology: Topologia, lista_de_ISPs: list[ISP], desastre: Desastre) -> None:
        self.topology: Topologia = topology
        self.lista_de_ISPs: list[ISP] = lista_de_ISPs
        self.desastre: Desastre = desastre

    def retorna_atributos(self) -> tuple[Topologia, list[ISP], Desastre]:
        return deepcopy((self.topology, self.lista_de_ISPs, self.desastre))