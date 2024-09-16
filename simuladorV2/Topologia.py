import networkx as nx
from itertools import islice
from ISP.ISP import ISP
import simpy
class Topologia:


    def __init__(self, topology: nx.Graph, list_of_ISP: list[ISP], numero_de_caminhos: int, numero_de_slots: int, enviromment :simpy.Environment):
        self.topology: nx.Graph = topology
        self.numero_de_slots = numero_de_slots
        self.enviromment :simpy.Environment = enviromment

        self.inicia_topologia(list_of_ISP, numero_de_caminhos, numero_de_slots)


    def inicia_topologia(self, list_of_ISP: list[ISP], numero_de_caminhos: int, numero_de_slots: int):
        self.inicia_slots( numero_de_slots)
        self.inicia_lista_de_ISPs_por_link_e_node( list_of_ISP )
        self.inicia_caminhos_mais_curtos(numero_de_caminhos)

    def inicia_slots(self, numero_de_slots: int):
        for edge in self.topology.edges():
            self.topology[edge[0]][edge[1]]["slots"] = [0] * numero_de_slots

    def inicia_lista_de_ISPs_por_link_e_node( self, list_of_ISP: list[ISP]):

        for edge in self.topology.edges():
            self.topology[edge[0]][edge[1]]["ISPs"] = []
        for node in self.topology.nodes():
            self.topology.nodes[node]["ISPs"] = []

        for isp in list_of_ISP:

            for node in isp.nodes:
                 self.topology.nodes[node]["ISPs"].append(isp.id)

            for edge in isp.edges:
                self.topology[edge[0]][edge[1]]["ISPs"].append(isp.id)

    def inicia_caminhos_mais_curtos(self, numero_de_caminhos: int):
        for i in list(self.topology.nodes()):
                for j in list(self.topology.nodes()):
                    if i!= j:
                        self.topology[i][j]["caminhos"] = self.k_shortest_paths(self.topology, i, j, numero_de_caminhos, weight='weight')
        
    def k_shortest_paths( G, source, target, k, weight='weight'):
        return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))
    
    def _desalocate(self, path, spectro):
        for i in range(0, (len(path)-1)):
                for slot in range(spectro[0],spectro[1]+1):
                    self.topology[path[i]][path[i+1]]['capacity'][slot] = 0
    def _desaloca_janela(self, path, spectro, holding_time):
        try:
            yield self.enviromment.timeout(holding_time)
            self._desalocate( path, spectro)
        except simpy.Interrupt as interrupt:
            self._desalocate( path, spectro)


    def desaloca_janela(self, path, spectro, holding_time):
        return self.enviromment.process(self._desaloca_janela(path, spectro, holding_time))

    def aloca_janela(self, path, spectro):
        inicio = spectro[0]
        fim = spectro[1]
        for i in range(0,len(path)-1):
            for slot in range(inicio,fim+1):
                self.topology[path[i]][path[i+1]]['capacity'][slot] = 1
        
    def distancia_caminho(self, path):
        soma = 0
        for i in range(0, (len(path)-1)):
            soma += self.topology[path[i]][path[i+1]]['weight']
        return (soma)
    
    def caminho_passa_por_link( ponto_a, ponto_b, caminho):
        
        return (any( caminho[index] == ponto_a and caminho[index+1] == ponto_b for index in range(len(caminho))) or
                any( caminho[index] == ponto_b and caminho[index+1] == ponto_a for index in range(len(caminho)))
                )