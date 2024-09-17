from Desastre.Desastre import Desastre
import numpy as np
import networkx as nx
from Roteamento.Roteamento import Roteamento
from Roteamento.iRoteamento import iRoteamento
from Roteamento.RoteamentoDesastre import RoteamentoDesastre
from Simulador import Simulador
from Variaveis import *
from ISP.Datacenter import Datacenter

class ISP:
    def __init__(self, id, nodes, edges):
        self.id = id
        self.nodes = nodes
        self.edges = edges
        self.roteamento :iRoteamento = Roteamento
        self.roteamento_desastre :iRoteamento = RoteamentoDesastre
        self.datacenter = None


    def define_datacenter(self, disaster: Desastre, topology: nx.Graph, specific_values = None):

        if specific_values == None:
            datacenterSource = np.random.choice(disaster.list_of_dict_node_per_start_time)["node"]
            all_distances: dict = nx.shortest_path_length(topology, datacenterSource)
            node_distances = { distance:node for node, distance in all_distances.items() if node in self.nodes}
            datacenterDestination = node_distances[max(node_distances.keys())]
            tempoDeReacao = disaster.start - np.random.normal(TEMPO_DE_REACAO, VARIANCIA_TEMPO_DE_REACAO)
            tamanhoDatacenter = np.random.normal(TAMANHO_DATACENTER, VARIANCIA_TAMANHO_DATACENTER)
            througput_datacenter = np.random.normal(THROUGHPUT, VARIANCIA_THROUGPUT)
            self.datacenter = Datacenter(datacenterSource, datacenterDestination, tempoDeReacao, tamanhoDatacenter,througput_datacenter )
        else:
            self.datacenter = Datacenter(specific_values["source"], specific_values["destination"], specific_values["tempoDeReacao"], specific_values["tamanhoDatacenter"])

    def iniciar_migracao(self, simulador :Simulador):

        while(True):
            if simulador.env.now >= self.datacenter.tempo_de_reacao:
                self.roteamento = self.roteamento_desastre
                self.datacenter.iniciar_migracao(simulador)
                break
            yield simulador.env.timeout(1)
