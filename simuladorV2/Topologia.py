import networkx as nx
from itertools import islice
from ISP.ISP import ISP
import simpy
from typing import Generator

class Topologia:


    def __init__(self, topology: nx.Graph, list_of_ISP: list[ISP], numero_de_caminhos: int, numero_de_slots: int) -> None:
        self.topology: nx.Graph = topology
        self.numero_de_slots = numero_de_slots
        self.caminhos_mais_curtos_entre_links = {}

        self.inicia_topologia(list_of_ISP, numero_de_caminhos, numero_de_slots)

    def imprime_topologia(self) -> None:
        print("Nós: ", self.topology.nodes())
        print("Arestas: ", self.topology.edges())
        print("Arestas com atributos: ", self.topology.edges(data=True))
        print("Nós com atributos: ", self.topology.nodes(data=True))
    
    def inicia_topologia(self, list_of_ISP: list[ISP], numero_de_caminhos: int, numero_de_slots: int) -> None:
        self.inicia_status( numero_de_slots)
        self.inicia_lista_de_ISPs_por_link_e_node( list_of_ISP )
        self.inicia_caminhos_mais_curtos(numero_de_caminhos)

    def inicia_status(self, numero_de_slots: int) -> None:
        for edge in self.topology.edges():
            self.topology[edge[0]][edge[1]]["slots"] = [0] * numero_de_slots
            self.topology[edge[0]][edge[1]]["failed"] = False

    def inicia_lista_de_ISPs_por_link_e_node( self, list_of_ISP: list[ISP]) -> None:

        for edge in self.topology.edges():
            self.topology[edge[0]][edge[1]]["ISPs"] = []
        for node in self.topology.nodes():
            self.topology.nodes[node]["ISPs"] = []

        for isp in list_of_ISP:

            for node in isp.nodes:
                 self.topology.nodes[node]["ISPs"].append(isp.id)

            for edge in isp.edges:
                self.topology[edge[0]][edge[1]]["ISPs"].append(isp.id)

    def inicia_caminhos_mais_curtos(self, numero_de_caminhos: int) -> None:
        nodes = list(self.topology.nodes())
        for i in nodes:
                self.caminhos_mais_curtos_entre_links[int(i)] = {}
                for j in nodes:
                    if i != j:
                        self.caminhos_mais_curtos_entre_links[int(i)][int(j)] = self.k_shortest_paths(self.topology, i, j, numero_de_caminhos, weight='weight')

        
    def k_shortest_paths(self, G, source, target, k, weight='weight') -> None:
        return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))
    
    def _desalocate(self, path, spectro) -> None:
        for i in range(0, (len(path)-1)):
                for slot in range(spectro[0],spectro[1]+1):
                    self.topology[path[i]][path[i+1]]['slots'][slot] = 0

    def desaloca_janela(self, path, spectro, holding_time, env: simpy.Environment) -> Generator[None, None, None]:
        try:
            yield env.timeout(holding_time)
            self._desalocate( path, spectro)

        except simpy.Interrupt as interrupt:
            self._desalocate( path, spectro)


    def aloca_janela(self, path, spectro)  -> None:
        inicio = spectro[0]
        fim = spectro[1]
        for i in range(0,len(path)-1):
            for slot in range(inicio,fim+1):
                self.topology[path[i]][path[i+1]]['slots'][slot] = 1
        
    def distancia_caminho(self, path)  -> None:
        soma = 0
        for i in range(0, (len(path)-1)):
            soma += self.topology[path[i]][path[i+1]]['weight']
        return (soma)
    
    def caminho_passa_por_link(self, ponto_a, ponto_b, caminho) -> bool:
        
        return any( (caminho[index] == ponto_a and caminho[index+1] or caminho[index] == ponto_b and caminho[index+1]== ponto_b ) for index in range(len(caminho)-1))
    
    def caminho_em_funcionamento(self, caminho) -> bool:
        return not any( self.topology[caminho[i]][caminho[i+1]]['failed'] for i in range(len(caminho)-1) )