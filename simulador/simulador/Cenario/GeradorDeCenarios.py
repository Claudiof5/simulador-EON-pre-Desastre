import simpy
import networkx as nx
from Topology.Topologia import Topologia
from ISP.GeradorDeISPs import GeradorDeISPs
from Desastre.GeradorDeDesastre import GeradorDeDesastre
from Desastre.Desastre import Desastre
from Requisicao.Requisicao import Requisicao
from Requisicao.GeradorDeTrafego import GeradorDeTrafego
from ISP.ISP import ISP
from Variaveis import *
from Cenario.Cenario import Cenario
from Roteamento.iRoteamento import iRoteamento
from Roteamento.Roteamento import Roteamento
from copy import deepcopy

class GeradorDeCenarios:

    @staticmethod
    def gerar_cenario( 
            topology: nx.Graph, retornar_objetos: bool = False, retorna_lista_de_requisicoes: bool = False,
            numero_de_requisicoes: int = 0, roteamento_de_desastre: 'iRoteamento' = Roteamento 
                        ) -> tuple[Topologia, list[ISP], Desastre, list[Requisicao]] | Cenario:
        
        datacenter_destinations = ()
        while len(datacenter_destinations) < NUMERO_DE_ISPS:
            lista_de_ISPs :list[ISP] = GeradorDeISPs.gerar_lista_ISPs_aleatorias( topology=topology, numero_de_ISPs=NUMERO_DE_ISPS , roteamento_de_desastre=roteamento_de_desastre)
            desastre      :Desastre  = GeradorDeDesastre.generate_disaster( topology, lista_de_ISPs )

            topologia      :Topologia = Topologia( topology, lista_de_ISPs, NUMERO_DE_CAMINHOS, NUMERO_DE_SLOTS )
            lista_de_requisicoes : list[Requisicao] = None

            for isp in lista_de_ISPs:
                isp.define_datacenter( desastre, topologia.topology )
            datacenter_destinations = set( isp.datacenter.destination for isp in lista_de_ISPs )

        if retorna_lista_de_requisicoes:
            lista_de_requisicoes = GeradorDeTrafego.gerar_lista_de_requisicoes( topologia, numero_de_requisicoes )

            for isp in lista_de_ISPs:
                GeradorDeTrafego.gerar_lista_de_requisicoes_datacenter( isp.datacenter, desastre, topologia, isp.id )

        if retornar_objetos:
            return Cenario(topologia, lista_de_ISPs, desastre, lista_de_requisicoes)
        else:
            return topologia, lista_de_ISPs, desastre, lista_de_requisicoes
    
    @staticmethod
    def gerar_cenarios( 
            topology: nx.Graph, retorna_lista_de_requisicoes: bool = False,
            numero_de_requisicoes: int = 0, lista_de_roteamentos_de_desastre: list['iRoteamento'] = [Roteamento] 
            ) -> tuple[Cenario, ...]:
        
        cenario = GeradorDeCenarios.gerar_cenario(topology, retornar_objetos=True, retorna_lista_de_requisicoes=retorna_lista_de_requisicoes, numero_de_requisicoes=numero_de_requisicoes,
                                                   roteamento_de_desastre=lista_de_roteamentos_de_desastre.pop(0))
        lista_de_cenarios: list[Cenario] = [cenario]
        for roteamento in lista_de_roteamentos_de_desastre:
            novo_cenario = deepcopy(cenario)
            novo_cenario.troca_roteamento_lista_de_desastre( roteamento )
            lista_de_cenarios.append(novo_cenario)
        
        return tuple(lista_de_cenarios)

       
    