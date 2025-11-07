from typing import TYPE_CHECKING

import networkx as nx
import numpy as np

from simulador.config.settings import (
    DURACAO_DESASTRE,
    INICIO_DESASTRE,
    VARIANCIA_DURACAO_DESASTRE,
    VARIANCIA_INICIO_DESASTRE,
)
from simulador.entities.disaster import Disaster
from simulador.entities.isp import ISP

if TYPE_CHECKING:
    from simulador.config.simulation_settings import ScenarioConfig


class DisasterGenerator:
    @staticmethod
    def generate_disaster(
        topology: nx.Graph,
        list_of_isp: list[ISP],
        config: "ScenarioConfig | None" = None,
    ) -> Disaster:
        """Generate a disaster scenario.
        
        Args:
            topology: Network topology graph
            list_of_isp: List of ISPs
            config: Optional ScenarioConfig with disaster timing parameters
            
        Returns:
            Disaster object with timing and affected nodes/links
        """
        # Use config if provided
        if config is None:
            from simulador.config.simulation_settings import ScenarioConfig
            config = ScenarioConfig()
        
        inicio_desastre = config.disaster_start
        variancia_inicio = config.disaster_start_variance
        duracao_desastre = config.disaster_duration
        variancia_duracao = config.disaster_duration_variance
        list_of_isp_nodes: list[list[int]] = [isp.nodes for isp in list_of_isp]
        intersection = list(
            set(list_of_isp_nodes[0]).intersection(*list_of_isp_nodes[1:])
        )

        disaster_center_arr = np.random.choice(intersection, 1)
        disaster_center: list[int] = [int(num) for num in disaster_center_arr]
        edges = list(topology.edges(disaster_center))
        index_list = [i for i in range(len(edges))]

        random_index = np.random.choice(index_list, len(index_list), replace=False)
        random_index = random_index[: max(random_index[0], 3)]

        random_edges = [edges[i] for i in random_index]

        tempos = [
            np.random.normal(inicio_desastre, variancia_inicio)
            for _ in range(len(random_edges) + len(disaster_center))
        ]
        min_value = min(tempos)
        max_value = max(tempos)
        tempos_finais = [x - min_value for x in tempos]

        duration = max(
            np.random.normal(duracao_desastre, variancia_duracao),
            max_value - min_value,
        )

        node_points: list[list] = [
            [element, int(tempos_finais[i])]
            for i, element in enumerate(disaster_center)
        ]
        link_points: list[list] = [
            [x, y, int(tempos_finais[i + len(disaster_center)])]
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
        return Disaster(
            min_value,
            duration,
            list_of_dict_node_per_start_time,
            list_of_dict_link_per_start_time,
            eventos,
        )
