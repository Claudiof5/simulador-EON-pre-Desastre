from typing import TYPE_CHECKING

import networkx as nx
import numpy as np
from Datacenter.Datacenter import Datacenter
from variaveis import (
    TAMANHO_DATACENTER,
    TEMPO_DE_REACAO,
    THROUGHPUT,
    VARIANCIA_TAMANHO_DATACENTER,
    VARIANCIA_TEMPO_DE_REACAO,
    VARIANCIA_THROUGPUT,
)

if TYPE_CHECKING:
    from Desastre.Desastre import Desastre


class GeradorDeDatacenter:
    @staticmethod
    def gerar_datacenter(
        disaster: "Desastre", topology: nx.Graph, nodes_isp: list, specific_values=None
    ) -> "Datacenter":
        if not specific_values:
            datacenter_source = np.random.choice(
                disaster.list_of_dict_node_per_start_time
            )["node"]
            all_distances: dict = nx.shortest_path_length(topology, datacenter_source)

            node_distances: dict[str, list] = {}
            for node, distancia in all_distances.items():
                if node in nodes_isp:
                    node_distances[node] = distancia

            # Find the node in nodes_isp with the maximum distance
            datacenter_destination = max(node_distances, key=node_distances.get)

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
            specific_values["source"],
            specific_values["destination"],
            specific_values["tempoDeReacao"],
            specific_values["tamanho_datacenter"],
        )
