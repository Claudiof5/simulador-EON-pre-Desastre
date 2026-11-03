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
    def destino_mais_distante(
        topology: nx.Graph, source: int, nodes_isp, criterio: str = "saltos"
    ) -> int:
        """Node of the ISP farthest from ``source``.

        Args:
            topology: Network topology (link attribute "weight" = length in km)
            source: Disaster node holding the datacenter
            nodes_isp: Nodes of the ISP
            criterio: "saltos" (hops) or "distancia" (shortest-path length in km)
        """
        if criterio not in ("saltos", "distancia"):
            raise ValueError(
                f"criterio must be 'saltos' or 'distancia', got {criterio!r}"
            )
        peso = "weight" if criterio == "distancia" else None
        distancias = nx.shortest_path_length(topology, source, weight=peso)
        candidatos = {
            int(n): float(d)
            for n, d in distancias.items()
            if n in nodes_isp and int(n) != int(source)
        }
        return int(max(candidatos, key=lambda n: candidatos[n]))

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
            datacenter_destination = DatacenterGenerator.destino_mais_distante(
                topology,
                datacenter_source,
                nodes_isp,
                getattr(config, "destino_migracao", "saltos"),
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
