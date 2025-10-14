import networkx as nx
import numpy as np
from simulador.Desastre.Desastre import Desastre
from simulador.ISP.ISP import ISP
from simulador.variaveis import (
    DURACAO_DESASTRE,
    INICIO_DESASTRE,
    VARIANCIA_DURACAO_DESASTRE,
    VARIANCIA_INICIO_DESASTRE,
)


class GeradorDeDesastre:
    @staticmethod
    def generate_disaster(topology: nx.Graph, list_of_isp: list[ISP]) -> Desastre:
        list_of_isp = [ISP.nodes for ISP in list_of_isp]
        intersection = list(set(list_of_isp[0]).intersection(*list_of_isp[1:]))

        disaster_center = np.random.choice(intersection, 1)
        disaster_center = [int(num) for num in disaster_center]
        edges = list(topology.edges(disaster_center))
        index_list = [i for i in range(len(edges))]

        random_index = np.random.choice(index_list, len(index_list), replace=False)
        random_index = random_index[: max(random_index[0], 3)]

        random_edges = [edges[i] for i in random_index]

        tempos = [
            np.random.normal(INICIO_DESASTRE, VARIANCIA_INICIO_DESASTRE)
            for _ in range(len(random_edges) + len(disaster_center))
        ]
        min_value = min(tempos)
        max_value = max(tempos)
        tempos_finais = [x - min_value for x in tempos]

        duration = max(
            np.random.normal(DURACAO_DESASTRE, VARIANCIA_DURACAO_DESASTRE),
            max_value - min_value,
        )

        node_points: list[list[int]] = [
            [element, tempos_finais[i]] for i, element in enumerate(disaster_center)
        ]
        link_points: list[list[int]] = [
            [x, y, tempos_finais[i + len(disaster_center)]]
            for i, (x, y) in enumerate(random_edges)
        ]

        sorted_node_points: list[list[int]] = sorted(
            node_points, key=lambda x: int(x[1])
        )
        list_of_dict_node_per_start_time = [
            {"tipo": "node", "node": int(x[0]), "start_time": int(x[1])}
            for x in sorted_node_points
        ]
        sorted_link_points: list[list[int]] = sorted(
            link_points, key=lambda x: int(x[2])
        )
        list_of_dict_link_per_start_time = [
            {
                "tipo": "link",
                "src": int(x[0]),
                "dst": int(x[1]),
                "start_time": int(x[2]),
            }
            for x in sorted_link_points
        ]
        eventos: list[dict] = (
            list_of_dict_node_per_start_time + list_of_dict_link_per_start_time
        )

        eventos.sort(key=lambda x: x["start_time"])
        return Desastre(
            min_value,
            duration,
            list_of_dict_node_per_start_time,
            list_of_dict_link_per_start_time,
            eventos,
        )
