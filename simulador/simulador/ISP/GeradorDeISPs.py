from itertools import combinations

import networkx as nx
import numpy as np
from ISP.ISP import ISP
from Roteamento.IRoteamento import IRoteamento


class GeradorDeISPs:
    @staticmethod
    def __has_edge_with_any(graph: nx.Graph, node: int, node_list: list[int]) -> bool:
        return any(graph.has_edge(node, other_node) for other_node in node_list)

    @staticmethod
    def __count_edges_with_any(graph: nx.Graph, node: int, node_list: list[int]) -> int:
        return sum(1 for other_node in node_list if graph.has_edge(node, other_node))

    @staticmethod
    def __randomly_exclude_elements(
        topology: nx.Graph, elements, exclusion_rate, isp_nodes
    ) -> list[int]:
        for element in elements:
            number_of_edges_with_nodes = GeradorDeISPs.__count_edges_with_any(
                topology, element, isp_nodes
            )
            if number_of_edges_with_nodes >= 1 and np.random.rand() > exclusion_rate - (
                (number_of_edges_with_nodes - 1) * 0.1
            ):
                isp_nodes.append(element)

        return [
            element
            for element in elements
            if np.random.rand() > exclusion_rate
            and GeradorDeISPs.__has_edge_with_any(topology, element, isp_nodes)
        ]

    @staticmethod
    def __edges_between_nodes(
        graph: nx.Graph, node_list: list
    ) -> list[tuple[int, int]]:
        existing_edges = []

        for node1, node2 in combinations(node_list, 2):
            if graph.has_edge(node1, node2):
                existing_edges.append((node1, node2))

        return existing_edges

    @staticmethod
    def __determine_interssection(
        topology: nx.Graph, isp_dict: dict
    ) -> dict[int, dict[str, list]]:
        node_intersec_dic = {x: [] for x in range(len(isp_dict) + 1)}
        edge_intersec_dic = {x: [] for x in range(len(isp_dict) + 1)}

        for node in topology.nodes():
            count = 0
            for key in isp_dict:
                if node in isp_dict[key]["nodes"]:
                    count += 1
            node_intersec_dic[count].append(node)

        for edge in topology.edges():
            count = 0
            for key in isp_dict:
                if (
                    edge in isp_dict[key]["edges"]
                    or (edge[1], edge[0]) in isp_dict[key]["edges"]
                ):
                    count += 1
            edge_intersec_dic[count].append(edge)

        returndict = {}
        for i in range(len(isp_dict) + 1):
            returndict[i] = {
                "nodes": node_intersec_dic[i],
                "edges": edge_intersec_dic[i],
            }

        return returndict

    @staticmethod
    def gerar_lista_isps_aleatorias(
        topology: nx.Graph, numero_de_isps: int, roteamento_de_desastre: "IRoteamento"
    ) -> list[ISP]:
        while True:
            centers = np.random.choice(
                list(topology.nodes), numero_de_isps, replace=False
            )
            centers = [
                int(node)
                for node in np.random.choice(
                    list(topology.nodes), numero_de_isps, replace=False
                )
            ]

            isps_dict = {}
            for i, source in enumerate(centers):
                isp_nodes = [source]
                distance_from_each_node = nx.shortest_path_length(topology, source)
                nodes_from_each_distance = {
                    x: [] for x in range(0, max(distance_from_each_node.values()) + 1)
                }

                for node, distance in distance_from_each_node.items():
                    nodes_from_each_distance[distance].append(node)

                # nodes_from_each_distance = dict(nodes_from_each_distance)

                isp_nodes.extend(nodes_from_each_distance[1])
                isp_nodes.extend(nodes_from_each_distance[2])

                aux = GeradorDeISPs.__randomly_exclude_elements(
                    topology, nodes_from_each_distance[3], 0.70, isp_nodes
                )

                isp_nodes.extend(aux)

                isp_edges = GeradorDeISPs.__edges_between_nodes(topology, isp_nodes)

                isps_dict[i] = {"nodes": isp_nodes, "edges": isp_edges}

            intercessoes = GeradorDeISPs.__determine_interssection(topology, isps_dict)
            if (
                len(intercessoes[numero_de_isps]["nodes"]) > 0
                and len(intercessoes[0]["nodes"]) == 0
            ):
                break

        lista_de_isps = []
        for isp_id, isp_dict in isps_dict.items():
            lista_de_isps.append(
                ISP(
                    isp_id,
                    isp_dict["nodes"],
                    isp_dict["edges"],
                    roteamento_de_desastre=roteamento_de_desastre,
                )
            )

        return lista_de_isps
