from typing import TYPE_CHECKING

import networkx as nx
import numpy as np

from simulador.config.settings import (
    TAMANHO_DATACENTER,
    TEMPO_DE_REACAO,
    THROUGHPUT,
    VARIANCIA_TAMANHO_DATACENTER,
    VARIANCIA_TEMPO_DE_REACAO,
    VARIANCIA_THROUGHPUT,
)

if TYPE_CHECKING:
    from simulador.config.simulation_settings import ScenarioConfig
    from simulador.entities.datacenter import Datacenter
    from simulador.entities.disaster import Disaster


class DatacenterGenerator:
    @staticmethod
    def gerar_datacenter(
        disaster: "Disaster",
        topology: nx.Graph,
        nodes_isp: list,
        specific_values=None,
        config: "ScenarioConfig | None" = None,
    ) -> "Datacenter":
        """Generate a datacenter for ISP migration.
        
        Args:
            disaster: Disaster scenario
            topology: Network topology graph
            nodes_isp: List of nodes in the ISP
            specific_values: Optional specific values to override defaults
            config: Optional ScenarioConfig with datacenter parameters
            
        Returns:
            Datacenter object
        """
        # Import here to avoid circular dependency
        from simulador.entities.datacenter import Datacenter
        
        # Use config if provided
        if config is None:
            from simulador.config.simulation_settings import ScenarioConfig
            config = ScenarioConfig()

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
                config.datacenter_reaction_time, config.datacenter_reaction_variance
            )
            tamanho_datacenter = np.random.normal(
                config.datacenter_size, config.datacenter_size_variance
            )
            througput_datacenter = np.random.normal(
                config.datacenter_throughput, config.datacenter_throughput_variance
            )
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
