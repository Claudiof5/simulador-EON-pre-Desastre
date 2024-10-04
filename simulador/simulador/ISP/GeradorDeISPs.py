import networkx as nx
import numpy as np
from itertools import combinations
from collections import defaultdict
from ISP.ISP import ISP
from Roteamento.iRoteamento import iRoteamento

class GeradorDeISPs:

    @staticmethod
    def __has_edge_with_any( G:nx.Graph, node: int, node_list: list[int]) -> bool:
        return any(G.has_edge(node, other_node) for other_node in node_list)

    @staticmethod
    def __count_edges_with_any(G: nx.Graph, node: int, node_list: list[int]) -> int:
        return sum(1 for other_node in node_list if G.has_edge(node, other_node))

    @staticmethod
    def __randomly_exclude_elements( topology: nx.Graph, elements, exclusion_rate, ISP_nodes) -> list[int]:
        
        ISP_nodes :list  = ISP_nodes
        for element in elements:
            number_of_edges_with_nodes = GeradorDeISPs.__count_edges_with_any(topology, element, ISP_nodes)
            if number_of_edges_with_nodes >= 1 and np.random.rand() > exclusion_rate-((number_of_edges_with_nodes-1)*0.1):
                ISP_nodes.append(element)

        return [element for element in elements if np.random.rand() > exclusion_rate and GeradorDeISPs.__has_edge_with_any(topology, element, ISP_nodes) ]

    @staticmethod
    def __edges_between_nodes(  G: nx.Graph, node_list: list) -> list[tuple[ int, int]]:
        existing_edges = []

        for node1, node2 in combinations(node_list, 2):
            if G.has_edge(node1, node2):
                existing_edges.append((node1, node2))
        
        return existing_edges
    
    @staticmethod
    def __determine_interssection(  topology: nx.Graph, ISP_dict: dict) -> dict[int, dict[str, list]]:
        node_intersec_dic = { x:[] for x in range(len(ISP_dict)+1)}
        edge_intersec_dic = { x:[] for x in range(len(ISP_dict)+1)}

        for node in topology.nodes():
            count = 0
            for i, key in enumerate(ISP_dict.keys()):
                if node in ISP_dict[key]["nodes"]:
                    count += 1
            node_intersec_dic[count].append(node)

        
        for edge in topology.edges():
            count = 0
            for i, key in enumerate(ISP_dict.keys()):
                if edge in ISP_dict[key]["edges"] or (edge[1], edge[0]) in ISP_dict[key]["edges"]:
                    count += 1
            edge_intersec_dic[count].append(edge)

        returndict = {}
        for i in range(len(ISP_dict)+1):
            returndict[i] = {"nodes":node_intersec_dic[i], "edges":edge_intersec_dic[i]}
        
        
        return returndict
    
    @staticmethod
    def gerar_lista_ISPs_aleatorias( topology: nx.Graph, numero_de_ISPs: int, roteamento_de_desastre: 'iRoteamento') -> list[ISP]:
        
        while True:
            centers = np.random.choice(list(topology.nodes), numero_de_ISPs, replace=False)
            centers = [int(node) for node in np.random.choice(list(topology.nodes), numero_de_ISPs, replace=False)]

            ISPS_dict = {}
            for i, source in enumerate(centers):
                ISP_nodes = [source]
                distance_from_each_node = nx.shortest_path_length(topology, source)
                nodes_from_each_distance = { x:[] for x in range(0, max(distance_from_each_node.values())+1)}
                
                for node, distance in distance_from_each_node.items():
                    nodes_from_each_distance[distance].append(node)

                #nodes_from_each_distance = dict(nodes_from_each_distance)

                ISP_nodes.extend(nodes_from_each_distance[1])
                ISP_nodes.extend(nodes_from_each_distance[2])

                aux = GeradorDeISPs.__randomly_exclude_elements( topology, nodes_from_each_distance[3], 0.70, ISP_nodes )
                
                ISP_nodes.extend(aux)

                ISP_edges = GeradorDeISPs.__edges_between_nodes(topology, ISP_nodes)

                ISPS_dict[i] = ({"nodes": ISP_nodes, "edges": ISP_edges})

            intercessoes = GeradorDeISPs.__determine_interssection(topology, ISPS_dict)
            if len(intercessoes[numero_de_ISPs]["nodes"]) > 0 and len(intercessoes[0]["nodes"]) == 0 :
                break
        
        lista_de_ISPs = []
        for id, dict in ISPS_dict.items():
            lista_de_ISPs.append(ISP(id, dict["nodes"], dict["edges"], roteamento_de_desastre=roteamento_de_desastre))

        return lista_de_ISPs


