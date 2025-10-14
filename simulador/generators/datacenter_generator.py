from typing import TYPE_CHECKING

import networkx as nx
import numpy as np

from simulador.config.settings import (
    TAMANHO_DATACENTER,
    TEMPO_DE_REACAO,
    THROUGHPUT,
    VARIANCIA_TAMANHO_DATACENTER,
    VARIANCIA_TEMPO_DE_REACAO,
    VARIANCIA_THROUGPUT,
)
from simulador.entities.datacenter import Datacenter

if TYPE_CHECKING:
    from simulador.entities.disaster import Disaster


class DatacenterGenerator:
    @staticmethod
    def gerar_datacenter(
        disaster: "Disaster", topology: nx.Graph, nodes_isp: list, specific_values=None
    ) -> "Datacenter":
        if not specific_values:
            datacenter_source = int(
                np.random.choice(
                    [d["node"] for d in disaster.list_of_dict_node_per_start_time]
                )
            )
            all_distances: dict = nx.shortest_path_length(topology, datacenter_source)

            node_distances: dict[int, int] = {}
            for node, distancia in all_distances.items():
                if node in nodes_isp:
                    node_distances[int(node)] = int(distancia)

            # Find the node in nodes_isp with the maximum distance
            datacenter_destination = int(
                max(node_distances, key=lambda x: node_distances[x])
            )

            tempo_de_inicio = disaster.start - np.random.normal(
                TEMPO_DE_REACAO, VARIANCIA_TEMPO_DE_REACAO
            )
            tamanho_datacenter = np.random.normal(
                TAMANHO_DATACENTER, VARIANCIA_TAMANHO_DATACENTER
            )
            througput_datacenter = np.random.normal(THROUGHPUT, VARIANCIA_THROUGPUT)
            return Datacenter(
                datacenter_source,
                datacenter_destination,
                tempo_de_inicio,
                tamanho_datacenter,
                througput_datacenter,
            )
        return Datacenter(
            int(specific_values["source"]),
            int(specific_values["destination"]),
            specific_values["tempoDeReacao"],
            specific_values["tamanho_datacenter"],
            specific_values.get("throughput_por_segundo", THROUGHPUT),
        )
