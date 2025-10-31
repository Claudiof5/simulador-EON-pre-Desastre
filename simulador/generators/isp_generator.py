from __future__ import annotations

from itertools import combinations

import networkx as nx
import numpy as np

from simulador.entities.isp import ISP
from simulador.routing.base import RoutingBase


class ISPGenerator:
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
            number_of_edges_with_nodes = ISPGenerator.__count_edges_with_any(
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
            and ISPGenerator.__has_edge_with_any(topology, element, isp_nodes)
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
        node_intersec_dic: dict[int, list] = {x: [] for x in range(len(isp_dict) + 1)}
        edge_intersec_dic: dict[int, list] = {x: [] for x in range(len(isp_dict) + 1)}

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
        topology: nx.Graph,
        numero_de_isps: int,
        roteamento_de_desastre: type[RoutingBase],
        computar_caminhos_internos: bool = True,
        numero_de_caminhos: int = 3,
        node_desastre: int | None = None,
    ) -> list[ISP]:
        """Generate a list of random ISPs.

        Args:
            topology: Network topology
            numero_de_isps: Number of ISPs to generate
            roteamento_de_desastre: Disaster routing method
            computar_caminhos_internos: Whether to compute internal paths for each ISP
            numero_de_caminhos: Number of alternative paths to compute per node pair
            node_desastre: Node that will fail during disaster (for disaster path computation)

        Returns:
            list[ISP]: List of generated ISPs with precomputed internal paths
        """
        while True:
            centers: list[int] = [
                int(node)
                for node in np.random.choice(
                    list(topology.nodes), numero_de_isps, replace=False
                )
            ]

            isps_dict: dict[int, dict[str, list]] = {}
            for i, source in enumerate(centers):
                isp_nodes = [source]
                distance_from_each_node = nx.shortest_path_length(topology, source)
                nodes_from_each_distance: dict[int, list[int]] = {
                    x: [] for x in range(0, max(distance_from_each_node.values()) + 1)
                }

                for node, distance in distance_from_each_node.items():
                    nodes_from_each_distance[distance].append(node)

                # nodes_from_each_distance = dict(nodes_from_each_distance)

                if 1 in nodes_from_each_distance:
                    isp_nodes.extend(nodes_from_each_distance[1])
                if 2 in nodes_from_each_distance:
                    isp_nodes.extend(nodes_from_each_distance[2])

                # Only try to process distance 3 nodes if they exist
                distance_3_nodes = nodes_from_each_distance.get(3, [])
                aux = ISPGenerator.__randomly_exclude_elements(
                    topology, distance_3_nodes, 0.70, isp_nodes
                )

                isp_nodes.extend(aux)

                isp_edges = ISPGenerator.__edges_between_nodes(topology, isp_nodes)

                isps_dict[i] = {"nodes": isp_nodes, "edges": isp_edges}

            intercessoes = ISPGenerator.__determine_interssection(topology, isps_dict)
            if (
                len(intercessoes[numero_de_isps]["nodes"]) > 0
                and len(intercessoes[0]["nodes"]) == 0
            ):
                break

        # First pass: Create ISPs and compute basic paths
        lista_de_isps = []
        for isp_id, isp_dict in isps_dict.items():
            isp = ISP(
                isp_id,
                isp_dict["nodes"],
                isp_dict["edges"],
                roteamento_de_desastre=roteamento_de_desastre,
            )

            # Compute internal paths if requested
            if computar_caminhos_internos:
                isp.computar_caminhos_internos(topology, numero_de_caminhos)

            lista_de_isps.append(isp)

        # Second pass: Compute disaster-aware weighted paths (needs full ISP list)
        if computar_caminhos_internos and node_desastre is not None:
            for isp in lista_de_isps:
                isp.computar_caminhos_internos_durante_desastre(
                    topology,
                    node_desastre,
                    numero_de_caminhos,
                    lista_de_isps=lista_de_isps,
                )

        return lista_de_isps
