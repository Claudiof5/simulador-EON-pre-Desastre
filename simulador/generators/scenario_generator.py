from __future__ import annotations

from copy import deepcopy
from typing import cast

import networkx as nx

from simulador import Topology
from simulador.config.simulation_settings import ScenarioConfig
from simulador.core.request import Request
from simulador.entities.disaster import Disaster
from simulador.entities.isp import ISP
from simulador.entities.scenario import Scenario
from simulador.generators.disaster_generator import DisasterGenerator
from simulador.generators.isp_generator import ISPGenerator
from simulador.generators.traffic_generator import TrafficGenerator
from simulador.routing import FirstFit
from simulador.routing.base import RoutingBase


class ScenarioGenerator:
    @staticmethod
    def gerar_cenario(
        topology: nx.Graph,
        disaster_node: int | None = None,
        retornar_objetos: bool = False,
        retorna_lista_de_requisicoes: bool = False,
        numero_de_requisicoes: int = 0,
        roteamento_de_desastre: type[RoutingBase] = FirstFit,
        config: ScenarioConfig | None = None,
    ) -> tuple[Topology, list[ISP], Disaster, list[Request]] | Scenario:
        """Generate a scenario with optional configuration.

        Args:
            topology: Network topology graph
            disaster_node: Specific node to fail (None = auto-select)
            retornar_objetos: Return as Scenario object vs tuple
            retorna_lista_de_requisicoes: Generate traffic requests
            numero_de_requisicoes: Number of requests (0 = use config/settings default)
            roteamento_de_desastre: Disaster routing algorithm
            config: ScenarioConfig with all parameters (None = use settings.py defaults)

        Returns:
            Scenario object or tuple of (Topology, ISPs, Disaster, Requests)
        """
        # Use provided config or create default
        if config is None:
            config = ScenarioConfig()

        # Use config values for scenario generation
        _numero_de_isps = config.numero_de_isps
        _numero_de_caminhos = config.numero_de_caminhos
        _numero_de_slots = config.numero_de_slots

        # Determine number of requests
        if numero_de_requisicoes == 0:
            numero_de_requisicoes = config.numero_de_requisicoes
        datacenter_destinations: set[int] = set()
        while len(datacenter_destinations) < _numero_de_isps:
            desastre_temp: Disaster | None = None
            while desastre_temp is None or (
                disaster_node is not None
                and desastre_temp.list_of_dict_node_per_start_time[0]["node"]
                != disaster_node
            ):
                lista_de_isps: list[ISP] = ISPGenerator.gerar_lista_isps_aleatorias(
                    topology=topology,
                    numero_de_isps=_numero_de_isps,
                    roteamento_de_desastre=roteamento_de_desastre,
                )
                desastre_temp = DisasterGenerator.generate_disaster(
                    topology, lista_de_isps, config=config
                )

            desastre: Disaster = desastre_temp

            topologia: Topology = Topology(
                topology, lista_de_isps, _numero_de_caminhos, _numero_de_slots
            )
            lista_de_requisicoes: list[Request] | None = None

            for isp in lista_de_isps:
                isp.define_datacenter(desastre, topologia.topology, config=config)
            datacenter_destinations = set(
                isp.datacenter.destination
                for isp in lista_de_isps
                if isp.datacenter is not None
            )

        topologia.desastre = desastre
        desastre.seta_links_como_prestes_a_falhar(topologia)
        topologia.inicia_caminhos_mais_curtos_durante_desastre(
            _numero_de_caminhos, desastre.list_of_dict_node_per_start_time[0]["node"]
        )

        if retorna_lista_de_requisicoes:
            lista_de_requisicoes = TrafficGenerator.gerar_lista_de_requisicoes(
                topologia, numero_de_requisicoes, lista_de_isps, desastre, config=config
            )

        if retornar_objetos:
            scenario = Scenario(
                topologia, lista_de_isps, desastre, lista_de_requisicoes or []
            )
            # Store config in scenario for later reference
            scenario.config = config
            return scenario
        return topologia, lista_de_isps, desastre, lista_de_requisicoes or []

    @staticmethod
    def gerar_cenarios(
        topology: nx.Graph,
        disaster_node: int | None = None,
        retorna_lista_de_requisicoes: bool = False,
        numero_de_requisicoes: int = 0,
        lista_de_roteamentos_de_desastre: list[type[RoutingBase]] | None = None,
        config: ScenarioConfig | None = None,
    ) -> tuple[Scenario, ...]:
        """Generate multiple scenarios with different routing algorithms.

        Args:
            topology: Network topology graph
            disaster_node: Specific node to fail (None = auto-select)
            retorna_lista_de_requisicoes: Generate traffic requests
            numero_de_requisicoes: Number of requests (0 = use config/settings default)
            lista_de_roteamentos_de_desastre: List of disaster routing algorithms to test
            config: ScenarioConfig with all parameters (None = use settings.py defaults)

        Returns:
            Tuple of Scenario objects, one for each routing algorithm
        """
        if lista_de_roteamentos_de_desastre is None:
            lista_de_roteamentos_de_desastre = [FirstFit]

        # Use provided config or create default
        if config is None:
            config = ScenarioConfig()

        # Generate first scenario
        cenario_result = ScenarioGenerator.gerar_cenario(
            topology,
            disaster_node=disaster_node,
            retornar_objetos=True,
            retorna_lista_de_requisicoes=retorna_lista_de_requisicoes,
            numero_de_requisicoes=numero_de_requisicoes,
            roteamento_de_desastre=lista_de_roteamentos_de_desastre[0],
            config=config,
        )
        cenario: Scenario = cast(Scenario, cenario_result)
        lista_de_cenarios: list[Scenario] = [cenario]

        # For additional routing algorithms, create scenarios by deepcopy
        # but keep same ISP topology/traffic (only change routing)
        for roteamento in lista_de_roteamentos_de_desastre[1:]:
            novo_cenario = deepcopy(cenario)
            novo_cenario.troca_roteamento_lista_de_desastre(roteamento)

            # Recompute disaster-aware paths with the new routing algorithm's requirements
            # This ensures weighted paths are computed for weighted routing algorithms
            for isp in novo_cenario.lista_de_isps:
                isp.computar_caminhos_internos_durante_desastre(
                    novo_cenario.topology.topology,
                    disaster_node,
                    config.numero_de_caminhos,
                    lista_de_isps=novo_cenario.lista_de_isps,
                    config=config,
                )

            lista_de_cenarios.append(novo_cenario)

        return tuple(lista_de_cenarios)

    @staticmethod
    def gerar_cenarios_com_diferentes_pesos(
        base_scenario: Scenario,
        lista_de_pesos: list[tuple[float, float, float]],
    ) -> list[Scenario]:
        """Generate multiple scenario variants with different routing weights.

        Takes an existing scenario and creates copies with different weight configurations.
        Each copy has the same topology, ISPs, disaster, and traffic, but different
        routing weights (alpha, beta, gamma) and recomputed weighted paths.

        Args:
            base_scenario: Existing Scenario object to use as template
            lista_de_pesos: List of (alpha, beta, gamma) tuples to test
                           Example: [(0.6, 0.2, 0.2), (0.8, 0.1, 0.1), (0.2, 0.6, 0.2)]

        Returns:
            List of Scenario objects, one per weight configuration.
            All scenarios have:
            - Same topology
            - Same ISP structure
            - Same disaster
            - Same request list (identical traffic)
            - Different routing weights (alpha, beta, gamma)
            - Different weighted paths (computed per config)
        """
        if not lista_de_pesos:
            raise ValueError("lista_de_pesos must contain at least one weight tuple")
        # Get base config from scenario or create default
        base_config = (
            base_scenario.config
            if base_scenario.config is not None
            else ScenarioConfig()
        )

        # Get disaster node from scenario
        disaster_node = None
        if base_scenario.desastre.list_of_dict_node_per_start_time:
            disaster_node = base_scenario.desastre.list_of_dict_node_per_start_time[0][
                "node"
            ]

        lista_de_cenarios: list[Scenario] = []

        # Create one scenario per weight configuration
        for idx, (alpha, beta, gamma) in enumerate(lista_de_pesos):
            print(
                f"Creating scenario variant {idx + 1}/{len(lista_de_pesos)} "
                f"with α={alpha:.2f}, β={beta:.2f}, γ={gamma:.2f}"
            )

            # Create config with new weights
            variant_config = base_config.copy_with(
                name=f"{base_config.name}_alpha{alpha:.2f}_beta{beta:.2f}_gamma{gamma:.2f}",
                alpha=alpha,
                beta=beta,
                gamma=gamma,
                metadata={
                    **base_config.metadata,
                    "weight_variation": True,
                    "weight_index": idx,
                    "base_scenario": base_config.name,
                },
            )

            # Deep copy the scenario (keeps same topology, ISPs, disaster, requests)
            novo_cenario = deepcopy(base_scenario)

            # Update config reference
            novo_cenario.config = variant_config

            # Recompute disaster-aware paths with NEW weights
            # This is crucial - the weighted paths depend on alpha, beta, gamma
            if disaster_node is not None:
                for isp in novo_cenario.lista_de_isps:
                    isp.computar_caminhos_internos_durante_desastre(
                        novo_cenario.topology.topology,
                        disaster_node,
                        variant_config.numero_de_caminhos,
                        lista_de_isps=novo_cenario.lista_de_isps,
                        config=variant_config,  # ← New config with different weights!
                    )

            lista_de_cenarios.append(novo_cenario)

        print(
            f"✓ Generated {len(lista_de_cenarios)} scenario variants with different routing weights"
        )

        return lista_de_cenarios
