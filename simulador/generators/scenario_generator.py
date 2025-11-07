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
from simulador.routing import FirstFit, FirstFitWeightedSubnetDisasterAware
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
        topology: nx.Graph,
        disaster_node: int,
        lista_de_pesos: list[tuple[float, float, float]],
        base_config: ScenarioConfig | None = None,
        roteamento_de_desastre: type[RoutingBase] | None = None,
    ) -> list[Scenario]:
        """Generate multiple scenarios with same traffic but different routing weights.

        This function is useful for comparing how different routing weight configurations
        (alpha, beta, gamma) affect the same traffic pattern and network conditions.

        Args:
            topology: Network topology graph
            disaster_node: Specific node that will fail during disaster
            lista_de_pesos: List of (alpha, beta, gamma) tuples to test
                           Example: [(0.6, 0.2, 0.2), (0.8, 0.1, 0.1), (0.2, 0.6, 0.2)]
            base_config: Optional base ScenarioConfig (if None, uses defaults)
                        The routing weights will be overridden by lista_de_pesos
            roteamento_de_desastre: Disaster routing algorithm (if None, uses default)

        Returns:
            List of Scenario objects, one per weight configuration.
            All scenarios have:
            - Same topology
            - Same ISP structure
            - Same disaster
            - Same request list (identical traffic)
            - Different routing weights (alpha, beta, gamma)
            - Different weighted paths (computed per config)

        Example:
            >>> # Compare ISP-priority vs migration-aware vs criticality-aware
            >>> weight_configs = [
            ...     (0.8, 0.1, 0.1),  # High ISP priority
            ...     (0.2, 0.6, 0.2),  # Avoid migration paths
            ...     (0.2, 0.1, 0.7),  # Avoid critical links
            ... ]
            >>> scenarios = ScenarioGenerator.gerar_cenarios_com_diferentes_pesos(
            ...     topology,
            ...     disaster_node=10,
            ...     lista_de_pesos=weight_configs
            ... )
            >>> # Now run each scenario and compare results
            >>> for scenario in scenarios:
            ...     print(f"Config: α={scenario.config.alpha}, β={scenario.config.beta}, γ={scenario.config.gamma}")
            ...     results = run_simulation(scenario)
        """
        if not lista_de_pesos:
            raise ValueError("lista_de_pesos must contain at least one weight tuple")

        # Validate weight tuples
        for i, (alpha, beta, gamma) in enumerate(lista_de_pesos):
            if not (0 <= alpha <= 1 and 0 <= beta <= 1 and 0 <= gamma <= 1):
                raise ValueError(
                    f"Weight tuple {i} has invalid values: ({alpha}, {beta}, {gamma}). "
                    f"All weights must be in [0, 1]"
                )

        # Use provided base config or create default
        if base_config is None:
            base_config = ScenarioConfig()

        # Use provided routing algorithm or default from config
        if roteamento_de_desastre is None:
            roteamento_de_desastre = FirstFitWeightedSubnetDisasterAware

        # Get first weight configuration
        alpha_0, beta_0, gamma_0 = lista_de_pesos[0]

        # Create config for first scenario with first weight set
        first_config = base_config.copy_with(
            name=f"{base_config.name}_alpha{alpha_0:.2f}_beta{beta_0:.2f}_gamma{gamma_0:.2f}",
            alpha=alpha_0,
            beta=beta_0,
            gamma=gamma_0,
            metadata={
                **base_config.metadata,
                "weight_variation": True,
                "weight_index": 0,
            },
        )

        # Generate base scenario with first weight configuration
        print(
            f"Generating base scenario with α={alpha_0:.2f}, β={beta_0:.2f}, γ={gamma_0:.2f}"
        )
        base_scenario = ScenarioGenerator.gerar_cenario(
            topology,
            disaster_node=disaster_node,
            retornar_objetos=True,
            retorna_lista_de_requisicoes=True,
            numero_de_requisicoes=0,  # Use config default
            roteamento_de_desastre=roteamento_de_desastre,
            config=first_config,
        )
        base_scenario = cast(Scenario, base_scenario)

        lista_de_cenarios: list[Scenario] = [base_scenario]

        # For additional weight configurations, create scenarios with:
        # - Same topology, ISPs, disaster, and requests (deep copy)
        # - Different routing weights
        # - Recomputed weighted paths
        for idx, (alpha, beta, gamma) in enumerate(lista_de_pesos[1:], start=1):
            print(
                f"Creating variant {idx} with α={alpha:.2f}, β={beta:.2f}, γ={gamma:.2f}"
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
                },
            )

            # Deep copy the scenario (keeps same topology, ISPs, disaster, requests)
            novo_cenario = deepcopy(base_scenario)

            # Update config reference
            novo_cenario.config = variant_config

            # Recompute disaster-aware paths with NEW weights
            # This is crucial - the weighted paths depend on alpha, beta, gamma
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
            f"✓ Generated {len(lista_de_cenarios)} scenarios with different routing weights"
        )

        return lista_de_cenarios
