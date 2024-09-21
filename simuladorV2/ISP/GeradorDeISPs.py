import networkx as nx
import numpy as np
from itertools import combinations
from collections import defaultdict
from ISP.ISP import ISP

class GeradorDeISPs:

    @staticmethod
    def has_edge_with_any( G:nx.Graph, node, node_list):
        return any(G.has_edge(node, other_node) for other_node in node_list)

    @staticmethod
    def count_edges_with_any(G: nx.Graph, node, node_list):
        return sum(1 for other_node in node_list if G.has_edge(node, other_node))

    @staticmethod
    def randomly_exclude_elements( topology: nx.Graph, elements, exclusion_rate, ISP_nodes):
        
        ISP_nodes :list  = ISP_nodes
        for element in elements:
            number_of_edges_with_nodes = GeradorDeISPs.count_edges_with_any(topology, element, ISP_nodes)
            if number_of_edges_with_nodes >= 1 and np.random.rand() > exclusion_rate-((number_of_edges_with_nodes-1)*0.1):
                ISP_nodes.append(element)

        return [element for element in elements if np.random.rand() > exclusion_rate and GeradorDeISPs.has_edge_with_any(topology, element, ISP_nodes) ]

    @staticmethod
    def edges_between_nodes(  G: nx.Graph, node_list:list):
        # Create an empty list to store the edges
        existing_edges = []
        
        # Iterate over all pairs of nodes in node_list
        for node1, node2 in combinations(node_list, 2):
            # Check if an edge exists between node1 and node2
            if G.has_edge(node1, node2):
                existing_edges.append((node1, node2))
        
        return existing_edges
    
    @staticmethod
    def determine_interssection(  topology:nx.Graph, ISP_dict:dict):
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
    def gerar_lista_ISPs_aleatorias( topology: nx.Graph, numero_de_ISPs:int) -> list[ISP]:
        
        while True:
            centers = np.random.choice(list(topology.nodes), numero_de_ISPs, replace=False)
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

                aux = GeradorDeISPs.randomly_exclude_elements( topology, nodes_from_each_distance[3], 0.70, ISP_nodes )
                
                ISP_nodes.extend(aux)

                ISP_edges = GeradorDeISPs.edges_between_nodes(topology, ISP_nodes)

                ISPS_dict[i] = ({"nodes": ISP_nodes, "edges": ISP_edges})

            intercessoes = GeradorDeISPs.determine_interssection(topology, ISPS_dict)
            if len(intercessoes[numero_de_ISPs]["nodes"]) > 0 and len(intercessoes[0]["nodes"]) == 0 :
                break
        
        lista_de_ISPs = []
        for id, dict in ISPS_dict.items():
            lista_de_ISPs.append(ISP(id, dict["nodes"], dict["edges"]))

        return lista_de_ISPs


