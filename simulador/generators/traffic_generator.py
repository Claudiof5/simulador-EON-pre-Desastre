from __future__ import annotations

import random
from typing import TYPE_CHECKING

import networkx as nx
from numpy.random import choice, normal

from simulador.config.settings import (
    BANDWIDTH,
    CLASS_TYPE,
    CLASS_WEIGHT,
    HOLDING_TIME,
    REQUISICOES_POR_SEGUNDO,
    TRAFFIC_WEIGHT_EDGES,
    TRAFFIC_WEIGHT_ISOLATION,
    TRAFFIC_WEIGHT_NODES,
)
from simulador.core.request import Request
from simulador.utils.metrics import Metrics

# Constante para número mínimo de nodes em uma ISP para tráfego de subrede
MIN_NODES_PER_ISP = 2

if TYPE_CHECKING:
    import networkx as nx

    from simulador import Topology
    from simulador.config.simulation_settings import ScenarioConfig
    from simulador.entities.datacenter import Datacenter
    from simulador.entities.disaster import Disaster
    from simulador.entities.isp import ISP


class TrafficGenerator:
    @staticmethod
    def _get_graph(topology: Topology | nx.Graph) -> nx.Graph:
        """Return the underlying NetworkX graph regardless of wrapper type."""
        if hasattr(topology, "topology"):
            return topology.topology
        return topology

    @staticmethod
    def gerar_requisicao(
        topology: Topology,
        req_id: int,
        specific_values: dict | None = None,
        trafego_subrede: bool = True,
    ) -> Request:
        """Generate a network request with random or specific values.

        For subnet traffic (trafego_subrede=True), ISP selection uses hybrid weighting:
        - 50% network capacity (edge count)
        - 30% network size (node count)
        - 20% isolation (penalty for overlapping ISPs)

        This ensures fair traffic distribution where larger ISPs with more capacity
        receive proportionally more traffic.

        Args:
            topology: Network topology
            req_id: Request identifier
            specific_values: Optional specific values to override defaults
            trafego_subrede: If True, generates subnet traffic (same ISP) with fair
                           weighted ISP selection. If False, uses original behavior.

        Returns:
            Request: Generated network request

        """
        if specific_values is None:
            return TrafficGenerator._gerar_requisicao_aleatoria(
                topology, req_id, trafego_subrede
            )

        return TrafficGenerator._gerar_requisicao_especifica(
            topology, req_id, specific_values
        )

    @staticmethod
    def _gerar_requisicao_aleatoria(
        topology: Topology, req_id: int, trafego_subrede: bool = False
    ) -> Request:
        """Generate a request with random values.

        Args:
            topology: Network topology
            req_id: Request identifier
            trafego_subrede: If True, generates subnet traffic (same ISP),
                           if False, uses original behavior (any ISP)

        Returns:
            Request: Generated network request
        """
        class_type = choice(CLASS_TYPE, p=CLASS_WEIGHT)
        graph = TrafficGenerator._get_graph(topology)

        # Fallback if topology doesn't expose ISP metadata
        has_isp_metadata = hasattr(topology, "lista_de_isps") or any(
            graph.nodes[node].get("ISPs") for node in graph.nodes
        )

        if trafego_subrede and not has_isp_metadata:
            trafego_subrede = False

        if trafego_subrede:
            # Comportamento novo: tráfego de subrede (mesma ISP)
            isps_disponiveis = TrafficGenerator._get_isps_com_multiplos_nodes(topology)
            if not isps_disponiveis:
                # Fallback para comportamento original se não houver ISPs com múltiplos nodes
                src, dst = choice(list(graph.nodes), MIN_NODES_PER_ISP, replace=False)
                src_isp = choice(graph.nodes[src]["ISPs"])
                dst_isp = src_isp  # Força mesma ISP
            else:
                # Calculate weighted probabilities for fair ISP selection
                isp_weights = TrafficGenerator._calculate_isp_traffic_weights(
                    topology, isps_disponiveis
                )

                # Select ISP based on weighted probabilities
                isp_ids = list(isp_weights.keys())
                probabilities = list(isp_weights.values())
                selected_isp = choice(isp_ids, p=probabilities)

                # Seleciona src e dst dentro da mesma ISP
                nodes_da_isp = TrafficGenerator._get_nodes_da_isp(
                    topology, selected_isp
                )
                src, dst = choice(nodes_da_isp, MIN_NODES_PER_ISP, replace=False)
                src_isp = dst_isp = selected_isp
        else:
            # Comportamento original: qualquer ISP
            src, dst = choice(list(graph.nodes), MIN_NODES_PER_ISP, replace=False)
            src_isp = choice(graph.nodes[src]["ISPs"])
            dst_isp = choice(graph.nodes[dst]["ISPs"])

        bandwidth = choice(BANDWIDTH)
        holding_time = normal(HOLDING_TIME, HOLDING_TIME * 0.1)
        requisicao_de_migracao = False

        return TrafficGenerator._criar_requisicao(
            req_id,
            src,
            dst,
            src_isp,
            dst_isp,
            bandwidth,
            class_type,
            holding_time,
            requisicao_de_migracao,
        )

    @staticmethod
    def _gerar_requisicao_especifica(
        topology: Topology, req_id: int, specific_values: dict
    ) -> Request:
        """Generate a request with specific values."""
        src, dst = TrafficGenerator._get_src_dst(topology, specific_values)
        graph = TrafficGenerator._get_graph(topology)
        src_isp_value = specific_values.get("src_isp_index")
        if src_isp_value is None:
            src_isp_value = specific_values.get("src_isp")
        if src_isp_value is None:
            src_isp_value = choice(graph.nodes[src]["ISPs"])

        dst_isp_value = specific_values.get("dst_isp_index")
        if dst_isp_value is None:
            dst_isp_value = specific_values.get("dst_isp")
        if dst_isp_value is None:
            dst_isp_value = choice(graph.nodes[dst]["ISPs"])

        bandwidth_value = specific_values.get("bandwidth")
        if bandwidth_value is None:
            bandwidth_value = choice(BANDWIDTH)

        holding_time_value = specific_values.get("holding_time")
        if holding_time_value is None:
            holding_time_value = normal(HOLDING_TIME, HOLDING_TIME * 0.1)

        class_type_value = specific_values.get("class_type")
        if class_type_value is None:
            class_type_value = choice(CLASS_TYPE, p=CLASS_WEIGHT)

        src_isp = int(src_isp_value)
        dst_isp = int(dst_isp_value)
        bandwidth = bandwidth_value
        holding_time = float(holding_time_value)
        class_type = int(class_type_value)
        requisicao_de_migracao = specific_values.get("requisicao_de_migracao", False)

        return TrafficGenerator._criar_requisicao(
            req_id,
            src,
            dst,
            src_isp,
            dst_isp,
            bandwidth,
            class_type,
            holding_time,
            requisicao_de_migracao,
        )

    @staticmethod
    def _get_src_dst(topology: Topology, specific_values: dict) -> tuple[int, int]:
        """Get source and destination nodes."""
        src = specific_values.get("src")
        dst = specific_values.get("dst")
        graph = TrafficGenerator._get_graph(topology)

        if src is None and dst is None:
            nodes = choice(list(graph.nodes), 2, replace=False)
            return int(nodes[0]), int(nodes[1])
        if src is None:
            return int(choice(list(graph.nodes))), int(dst) if dst is not None else 0
        if dst is None:
            return int(src) if src is not None else 0, int(choice(list(graph.nodes)))
        return int(src) if src is not None else 0, int(dst) if dst is not None else 0

    @staticmethod
    def _criar_requisicao(
        req_id: int,
        src: int,
        dst: int,
        src_isp: int,
        dst_isp: int,
        bandwidth: int,
        class_type: int,
        holding_time: float,
        requisicao_de_migracao: bool,
    ) -> Request:
        """Create and register a request."""
        Metrics.conta_requisicao_banda(bandwidth)
        Metrics.conta_requisicao_classe(class_type)

        return Request(
            str(req_id),
            src,
            dst,
            src_isp,
            dst_isp,
            bandwidth,
            class_type,
            holding_time,
            requisicao_de_migracao,
        )

    @staticmethod
    def _get_isps_com_multiplos_nodes(topology: Topology) -> list[int]:
        """Get ISPs that have at least 2 nodes for subnet traffic generation.

        Args:
            topology: Network topology

        Returns:
            list[int]: List of ISP IDs that have multiple nodes
        """
        graph = TrafficGenerator._get_graph(topology)
        isp_node_count: dict[int, int] = {}

        # Conta quantos nodes cada ISP tem
        for node in graph.nodes():
            for isp_id in graph.nodes[node].get("ISPs", []):
                isp_node_count[isp_id] = isp_node_count.get(isp_id, 0) + 1

        # Retorna ISPs com pelo menos 2 nodes
        return [
            isp_id
            for isp_id, count in isp_node_count.items()
            if count >= MIN_NODES_PER_ISP
        ]

    @staticmethod
    def _get_nodes_da_isp(topology: Topology, isp_id: int) -> list[int]:
        """Get all nodes that belong to a specific ISP.

        Args:
            topology: Network topology
            isp_id: ISP identifier

        Returns:
            list[int]: List of node IDs belonging to the ISP
        """
        graph = TrafficGenerator._get_graph(topology)
        nodes_da_isp = []
        for node in graph.nodes():
            if isp_id in graph.nodes[node].get("ISPs", []):
                nodes_da_isp.append(node)
        return nodes_da_isp

    @staticmethod
    def _calculate_isp_traffic_weights(
        topology: Topology,
        isp_ids: list[int],
        weight_edges: float | None = None,
        weight_nodes: float | None = None,
        weight_isolation: float | None = None,
    ) -> dict[int, float]:
        """Calculate weighted probabilities for ISP selection in traffic generation.

        Uses hybrid approach:
        - Edge count (capacity): How many links the ISP has
        - Node count (size): How many nodes the ISP covers
        - Isolation score: Penalty for overlapping with other ISPs

        Args:
            topology: Network topology
            isp_ids: List of ISP IDs to calculate weights for
            weight_edges: Weight for edge count component (default 0.5)
            weight_nodes: Weight for node count component (default 0.3)
            weight_isolation: Weight for isolation component (default 0.2)

        Returns:
            Dictionary mapping ISP ID to selection probability
        """
        # Use config defaults if not specified
        weight_edges = (
            weight_edges if weight_edges is not None else TRAFFIC_WEIGHT_EDGES
        )
        weight_nodes = (
            weight_nodes if weight_nodes is not None else TRAFFIC_WEIGHT_NODES
        )
        weight_isolation = (
            weight_isolation
            if weight_isolation is not None
            else TRAFFIC_WEIGHT_ISOLATION
        )

        # Collect ISP statistics when full metadata is available
        isp_stats = {}
        if hasattr(topology, "lista_de_isps"):
            for isp in topology.lista_de_isps:
                if isp.isp_id not in isp_ids:
                    continue

                num_nodes = len(isp.nodes)
                num_edges = len(isp.edges)

                # Calculate isolation: average ISPs per link in this ISP
                # Lower is better (1.0 = fully isolated, >1 = overlapping)
                total_isps_per_link = 0
                for edge in isp.edges:
                    node1, node2 = edge
                    # Count how many ISPs include both nodes of this edge
                    isps_on_edge = 0
                    for other_isp in topology.lista_de_isps:
                        if node1 in other_isp.nodes and node2 in other_isp.nodes:
                            isps_on_edge += 1
                    total_isps_per_link += isps_on_edge

                avg_isps_per_link = (
                    total_isps_per_link / num_edges if num_edges > 0 else 1.0
                )

                isp_stats[isp.isp_id] = {
                    "nodes": num_nodes,
                    "edges": num_edges,
                    "avg_isps_per_link": avg_isps_per_link,
                }

        if not isp_stats:
            # Fallback to uniform if no stats
            return {isp_id: 1.0 / len(isp_ids) for isp_id in isp_ids}

        # Normalize each component to [0, 1]
        max_nodes = max(s["nodes"] for s in isp_stats.values())
        max_edges = max(s["edges"] for s in isp_stats.values())

        # Calculate hybrid weights
        weights = {}
        for isp_id, stats in isp_stats.items():
            # Normalize components
            node_score = stats["nodes"] / max_nodes if max_nodes > 0 else 0
            edge_score = stats["edges"] / max_edges if max_edges > 0 else 0

            # Isolation score: invert so isolated ISPs score higher
            # 1.0 (isolated) -> 1.0, 3.0 (high overlap) -> 0.33
            isolation_score = (
                1.0 / stats["avg_isps_per_link"]
                if stats["avg_isps_per_link"] > 0
                else 1.0
            )

            # Combine with weights
            combined = (
                weight_edges * edge_score
                + weight_nodes * node_score
                + weight_isolation * isolation_score
            )

            weights[isp_id] = combined

        # Normalize to probabilities (sum to 1.0)
        total_weight = sum(weights.values())
        if total_weight > 0:
            probabilities = {isp_id: w / total_weight for isp_id, w in weights.items()}
        else:
            probabilities = {isp_id: 1.0 / len(isp_ids) for isp_id in isp_ids}

        return probabilities

    @staticmethod
    def gerar_lista_de_requisicoes(
        topology: Topology,
        numero_de_requisicoes: int,
        lista_de_isps: list[ISP],
        desastre: Disaster,
        trafego_subrede: bool = True,
        config: ScenarioConfig | None = None,
    ) -> list[Request]:
        """Generate a list of network requests including datacenter requests.

        Args:
            topology: Network topology
            numero_de_requisicoes: Number of requests to generate
            lista_de_isps: List of ISPs
            desastre: Disaster scenario
            trafego_subrede: If True, generates subnet traffic (same ISP),
                           if False, uses original behavior (any ISP)
            config: Optional ScenarioConfig with traffic parameters

        Returns:
            list[Request]: List of generated network requests sorted by creation time

        """
        # Use config if provided, otherwise fall back to settings.py
        if config is None:
            config = ScenarioConfig()

        # Calculate request rate from config's computed properties
        req_rate = config.requisicoes_por_segundo

        lista_de_requisicoes_nao_processadas: list[Request] = []
        tempo_de_criacao: float = 0.0
        for i in range(1, numero_de_requisicoes + 1):
            requisicao = TrafficGenerator.gerar_requisicao(
                topology, i, trafego_subrede=trafego_subrede
            )
            tempo_de_criacao = tempo_de_criacao + random.expovariate(req_rate)
            requisicao.tempo_criacao = tempo_de_criacao
            lista_de_requisicoes_nao_processadas.append(requisicao)

        for isp in lista_de_isps:
            if isp.datacenter is not None:
                datacenter_reqs = (
                    TrafficGenerator.gerar_lista_de_requisicoes_datacenter(
                        isp.datacenter, desastre, topology, isp.isp_id, config=config
                    )
                )
                if datacenter_reqs is not None:
                    lista_de_requisicoes_nao_processadas += datacenter_reqs

        # Sort by tempo_criacao to ensure temporal order
        lista_de_requisicoes_nao_processadas.sort(key=lambda x: x.tempo_criacao or 0.0)

        # Re-index req_id based on position in the sorted list to ensure uniqueness
        # This ensures all requests have unique IDs and req_id reflects the temporal order
        for index, req in enumerate(lista_de_requisicoes_nao_processadas, start=1):
            req.req_id = str(index)

        return lista_de_requisicoes_nao_processadas

    @staticmethod
    def gerar_lista_de_requisicoes_datacenter(
        datacenter: Datacenter,
        desastre: Disaster,
        topologia: Topology,
        isp_id: int,
        config: ScenarioConfig | None = None,
    ) -> list[Request]:
        """Generate migration requests before disaster.

        Note: This only generates requests. The actual 100% migration tracking
        must be done during request processing where we know if requests are
        blocked or successfully allocated.

        Migration starts at tempo_de_reacao and continues until disaster starts.

        Args:
            datacenter: Datacenter object
            desastre: Disaster scenario
            topologia: Network topology
            isp_id: ISP identifier
            config: Optional ScenarioConfig with bandwidth/slot parameters
        """
        # Use config if provided
        if config is None:
            config = ScenarioConfig()

        tempo_de_criacao = datacenter.tempo_de_reacao
        req_id = 0
        lista_de_requisicoes = []

        # Calculate request rate based on throughput and average bandwidth
        avg_bandwidth = sum(config.bandwidth_options) / len(config.bandwidth_options)
        avg_slots_per_request = avg_bandwidth / config.slot_size
        taxa_mensagens = datacenter.throughput_por_segundo / avg_slots_per_request

        # Generate requests until disaster starts
        # Note: 100% migration control must happen at allocation time, not here
        # Capture datacenter values at function start to avoid any reference issues
        datacenter_src = int(datacenter.source)
        datacenter_dst = int(datacenter.destination)
        while tempo_de_criacao < desastre.start:
            dict_values = {
                "src": datacenter_src,
                "dst": datacenter_dst,
                "src_isp_index": int(isp_id),
                "dst_isp_index": int(isp_id),
                "requisicao_de_migracao": True,
            }

            requisicao: Request = TrafficGenerator.gerar_requisicao(
                topologia, req_id, dict_values
            )
            # Verify destination was set correctly - CRITICAL FIX
            # If dst doesn't match, _get_src_dst() may have failed or dst was overwritten
            if requisicao.dst != datacenter_dst:
                # Force correct destination - this ensures migration requests
                # always have the correct datacenter destination
                requisicao.dst = datacenter_dst
                requisicao.src = datacenter_src  # Also ensure src is correct

            tempo_de_criacao += random.expovariate(taxa_mensagens)
            requisicao.tempo_criacao = tempo_de_criacao
            lista_de_requisicoes.append(requisicao)
            req_id += 1

        return lista_de_requisicoes
