import networkx as nx
from itertools import islice
from ISP.ISP import ISP
import simpy
from typing import Generator
from Variaveis import *


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Desastre.Desastre import Desastre  

class Topologia:


    def __init__(self, topology: nx.Graph, list_of_ISP: list[ISP], numero_de_caminhos: int, numero_de_slots: int) -> None:
        self.topology: nx.Graph = topology
        self.numero_de_slots = numero_de_slots
        self.caminhos_mais_curtos_entre_links = {}
        self.caminhos_mais_curtos_entre_links_durante_desastre = {}
        self.desastre: 'Desastre' = None
        self.__inicia_topologia(list_of_ISP, numero_de_caminhos, numero_de_slots)

    def imprime_topologia(self) -> None:
        print("Nós: ", self.topology.nodes())
        print("Arestas: ", self.topology.edges())
        print("Arestas com atributos: ", self.topology.edges(data=True))
        print("Nós com atributos: ", self.topology.nodes(data=True))
    
    def __inicia_topologia(self, list_of_ISP: list[ISP], numero_de_caminhos: int, numero_de_slots: int) -> None:
        self.__inicia_status( numero_de_slots)
        self.__inicia_lista_de_ISPs_por_link_e_node( list_of_ISP )
        self.__inicia_caminhos_mais_curtos(numero_de_caminhos)

    def __inicia_status(self, numero_de_slots: int) -> None:
        for edge in self.topology.edges():
            self.topology[edge[0]][edge[1]]["slots"] = [0] * numero_de_slots
            self.topology[edge[0]][edge[1]]["failed"] = False
            self.topology[edge[0]][edge[1]]['vai falhar'] = False

    def __inicia_lista_de_ISPs_por_link_e_node( self, list_of_ISP: list[ISP]) -> None:

        for edge in self.topology.edges():
            self.topology[edge[0]][edge[1]]["ISPs"] = []
        for node in self.topology.nodes():
            self.topology.nodes[node]["ISPs"] = []

        for isp in list_of_ISP:

            for node in isp.nodes:
                 self.topology.nodes[node]["ISPs"].append(isp.id)

            for edge in isp.edges:
                self.topology[edge[0]][edge[1]]["ISPs"].append(isp.id)

    def __inicia_caminhos_mais_curtos(self, numero_de_caminhos: int) -> None:

        for node1 in self.topology.nodes():
                self.caminhos_mais_curtos_entre_links[int(node1)] = {}

                for node2 in self.topology.nodes():

                    if node1 == node2:
                        continue

                    caminhos_mais_curtos_entre_i_e_j = self.__k_shortest_paths(self.topology, node1, node2, numero_de_caminhos, weight='weight')
                    informacoes_caminhos_mais_curtos_entre_i_e_j = []

                    for caminho in caminhos_mais_curtos_entre_i_e_j:
                        distancia = self.distancia_caminho(caminho)
                        fator_de_modulacao = self.__fator_de_modulacao(distancia)
                        informacoes_caminhos_mais_curtos_entre_i_e_j.append({"caminho": caminho, "distancia": distancia, "fator_de_modulacao": fator_de_modulacao})
                    
                    self.caminhos_mais_curtos_entre_links[int(node1)][int(node2)] = informacoes_caminhos_mais_curtos_entre_i_e_j

    def inicia_caminhos_mais_curtos_durante_desastre(self, numero_de_caminhos: int) -> None:

        topologia_desastre = nx.Graph()
        for edge in self.topology.edges():
            if self.topology[edge[0]][edge[1]]['vai falhar']:
                continue
            u, v = edge
            attributes = self.topology[u][v]
            topologia_desastre.add_edge(u, v, **attributes)

        for node1 in topologia_desastre.nodes():
            self.caminhos_mais_curtos_entre_links_durante_desastre[int(node1)] = {}
            for node2 in topologia_desastre.nodes():

                if node1 == node2:
                    continue
                caminhos_mais_curtos_entre_i_e_j_desastre = self.__k_shortest_paths(topologia_desastre, node1, node2, numero_de_caminhos, weight='weight')
                informacoes_caminhos_mais_curtos_entre_i_e_j_desastre = []

                for caminho in caminhos_mais_curtos_entre_i_e_j_desastre:
                    distancia = self.distancia_caminho(caminho)
                    fator_de_modulacao = self.__fator_de_modulacao(distancia)
                    informacoes_caminhos_mais_curtos_entre_i_e_j_desastre.append({"caminho": caminho, "distancia": distancia, "fator_de_modulacao": fator_de_modulacao})
                
                self.caminhos_mais_curtos_entre_links_durante_desastre[int(node1)][int(node2)] = informacoes_caminhos_mais_curtos_entre_i_e_j_desastre
                    
        
    def __k_shortest_paths(self, G: nx.Graph, source, target, k, weight='weight') -> None:
        return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))
    
    def desalocate(self, path, spectro) -> None:
        for i in range(0, (len(path)-1)):
                for slot in range(spectro[0],spectro[1]+1):
                    self.topology[path[i]][path[i+1]]['slots'][slot] = 0

    def desaloca_janela(self, path, spectro, holding_time, env: simpy.Environment) -> Generator:
        try:
            yield env.timeout(holding_time)
            self.desalocate( path, spectro)

        except simpy.Interrupt as interrupt:
            self.desalocate( path, spectro)

    def aloca_janela(self, path, spectro)  -> None:
        inicio = spectro[0]
        fim = spectro[1]
        for i in range(0,len(path)-1):
            for slot in range(inicio,fim+1):
                self.topology[path[i]][path[i+1]]['slots'][slot] = 1
        
    def distancia_caminho(self, path)  -> int:
        soma = 0
        for i in range(0, (len(path)-1)):
            soma += self.topology[path[i]][path[i+1]]['weight']
        return soma
    
    def caminho_passa_por_link(self, ponto_a, ponto_b, caminho) -> bool:
        return any( (caminho[index] == ponto_a and caminho[index+1] or caminho[index] == ponto_b and caminho[index+1]== ponto_b ) for index in range(len(caminho)-1))
    
    def caminho_em_funcionamento(self, caminho) -> bool:
        return not any( self.topology[caminho[i]][caminho[i+1]]['failed'] for i in range(len(caminho)-1) )
    
    def pode_passar_pelo_caminho_que_vai_falhar(self, caminho) -> bool:
        caminho_inicia_ou_termina_no_node_desastre = caminho[0] == self.desastre.list_of_dict_node_per_start_time[0]['node'] or caminho[-1] == self.desastre.list_of_dict_node_per_start_time[0]['node']
        return (not any( self.topology[caminho[i]][caminho[i+1]]['vai falhar'] for i in range(len(caminho)-1) ) or caminho_inicia_ou_termina_no_node_desastre)
    
    def __fator_de_modulacao(  self, distancia) -> float:
        if distancia <= 500:
            return (float(4 * SLOT_SIZE))
        elif 500 < distancia <= 1000:
            return (float(3 * SLOT_SIZE))
        elif 1000 < distancia <= 2000:
            return (float(2 * SLOT_SIZE)) 
        else:
            return (float(1 * SLOT_SIZE))