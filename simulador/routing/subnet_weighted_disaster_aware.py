"""Subnet routing implementation with disaster node avoidance for same-ISP traffic.

This module implements routing logic that ensures traffic only uses
nodes belonging to the same ISP and avoids disaster-affected nodes.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from simpy import Environment

from simulador.config.settings import SLOT_SIZE
from simulador.core.request import Request
from simulador.routing.base import RoutingBase
from simulador.utils.metrics import Metrics

if TYPE_CHECKING:
    from simulador import Topology


class FirstFitWeightedSubnetDisasterAware(RoutingBase):
    """Subnet routing class for same-ISP traffic that avoids disaster nodes.

    Uses weighted path selection where weights are based on:
    1. Link usage frequency in shortest paths (0-20% increase)
    2. Link usage frequency in migration paths (0-20% increase)

    Total weight range: 1.0 to 1.4 (encouraging load balancing)
    """

    # Cache for link weights per ISP
    _link_weights_cache: dict[int, dict[tuple[int, int], float]] = {}
    # Cache for migration-based weights (global across all ISPs)
    _migration_weights_cache: dict[tuple[int, int], float] | None = None

    @staticmethod
    def __str__() -> str:
        """Return string representation of the routing method."""
        return "FirstFit subrede evitando nodes de desastre com pesos"

    @staticmethod
    def rotear_requisicao(
        requisicao: Request, topology: Topology, env: Environment
    ) -> bool:
        """Route a request within the same ISP subnet avoiding disaster nodes.

        Args:
            requisicao: Network request to route
            topology: Network topology
            env: Simulation environment

        Returns:
            bool: True if routing successful, False otherwise
        """
        requisicao_roteada_com_sucesso = (
            FirstFitWeightedSubnetDisasterAware.__rotear_requisicao(
                requisicao, topology, env
            )
        )
        if requisicao_roteada_com_sucesso:
            Metrics.incrementa_numero_requisicoes_aceitas(requisicao, env)
            return True
        Metrics.incrementa_numero_requisicoes_bloqueadas(requisicao, env)
        return False

    @staticmethod
    def rerotear_requisicao(
        requisicao: Request, topology: Topology, env: Environment
    ) -> bool:
        """Reroute a request within the same ISP subnet avoiding disaster nodes.

        Args:
            requisicao: Network request to reroute
            topology: Network topology
            env: Simulation environment

        Returns:
            bool: True if rerouting successful, False otherwise
        """
        requisicao.dados_pre_reroteamento = (
            requisicao.retorna_tupla_chave_dicionario_dos_atributos()
        )

        requisicao_roteada_com_sucesso = (
            FirstFitWeightedSubnetDisasterAware.__rotear_requisicao(
                requisicao, topology, env
            )
        )

        if requisicao_roteada_com_sucesso:
            Metrics.incrementa_numero_requisicoes_reroteadas_aceitas(requisicao, env)
            return True
        Metrics.incrementa_numero_requisicoes_reroteadas_bloqueadas(requisicao, env)
        return False

    @staticmethod
    def __rotear_requisicao(
        requisicao: Request, topology: Topology, env: Environment
    ) -> bool:
        """Internal method to route a request within subnet constraints avoiding disasters.

        Args:
            requisicao: Network request to route
            topology: Network topology
            env: Simulation environment

        Returns:
            bool: True if routing successful, False otherwise
        """
        informacoes_dos_datapaths, pelo_menos_uma_janela_habil = (
            FirstFitWeightedSubnetDisasterAware.__retorna_informacoes_datapaths(
                requisicao, topology
            )
        )
        if pelo_menos_uma_janela_habil:
            FirstFitWeightedSubnetDisasterAware.__aloca_requisicao(
                requisicao, topology, informacoes_dos_datapaths, env
            )
            return True

        requisicao.bloqueia_requisicao(env.now)
        return False

    @staticmethod
    def __aloca_requisicao(
        requisicao: Request,
        topology: Topology,
        informacoes_datapaths: list[dict],
        env: Environment,
    ) -> None:
        """Allocate request to the first available path with sufficient slots.

        Args:
            requisicao: Network request to allocate
            topology: Network topology
            informacoes_datapaths: Dictionary with path information
            env: Simulation environment
        """
        for informacoes_datapath in informacoes_datapaths:
            if (
                informacoes_datapath["maior_janela_contigua_continua"]
                >= informacoes_datapath["numero_slots_necessarios"]
            ):
                FirstFitWeightedSubnetDisasterAware.__aloca_datapath(
                    requisicao, topology, informacoes_datapath, env
                )
                break

    @staticmethod
    def __aloca_datapath(
        requisicao: Request,
        topology: Topology,
        informacoes_datapath: dict,
        env: Environment,
    ) -> None:
        """Allocate a specific datapath for the request.

        Args:
            requisicao: Network request to allocate
            topology: Network topology
            informacoes_datapath: Dictionary with specific path information
            env: Simulation environment
        """
        index_inicio = next(
            (
                index_inicio
                for index_inicio, index_final in informacoes_datapath[
                    "lista_de_inicios_e_fins"
                ]
                if index_final - index_inicio + 1
                >= informacoes_datapath["numero_slots_necessarios"]
            ),
            0,
        )

        index_final = int(
            index_inicio + informacoes_datapath["numero_slots_necessarios"] - 1
        )
        caminho = informacoes_datapath["caminho"]

        topology.aloca_janela(caminho, (index_inicio, index_final))

        requisicao.processo_de_desalocacao = env.process(
            topology.desaloca_janela(
                caminho, (index_inicio, index_final), requisicao.holding_time, env
            )
        )

        requisicao.aceita_requisicao(
            informacoes_datapath["numero_slots_necessarios"],
            caminho,
            len(caminho),
            (index_inicio, index_final),
            env.now,
            env.now + requisicao.holding_time,
            informacoes_datapath["distancia"],
        )

    @staticmethod
    def __retorna_informacoes_datapaths(
        requisicao: Request, topology: Topology
    ) -> tuple[list[dict], bool]:
        """Return information about available datapaths for subnet routing avoiding disasters.

        Uses ISP-specific disaster-aware paths when available, falls back to
        topology-wide disaster paths, then regular ISP paths.
        """
        # Identifica a ISP da requisição (src_isp deve ser igual a dst_isp no tráfego de subrede)
        isp_requisicao = requisicao.src_isp

        # Try to get ISP-specific disaster-aware paths first
        caminhos_isp_desastre = (
            FirstFitWeightedSubnetDisasterAware._get_caminhos_desastre_from_isp(
                requisicao, topology, isp_requisicao
            )
        )

        if caminhos_isp_desastre:
            # Use ISP disaster-aware precomputed paths
            return FirstFitWeightedSubnetDisasterAware._processar_caminhos_isp(
                caminhos_isp_desastre, requisicao, topology
            )

        # Fallback to topology-wide disaster paths with ISP filtering
        if (
            int(requisicao.dst)
            in topology.caminhos_mais_curtos_entre_links_durante_desastre
            and int(requisicao.src)
            in topology.caminhos_mais_curtos_entre_links_durante_desastre
            and int(requisicao.dst)
            in topology.caminhos_mais_curtos_entre_links_durante_desastre[
                int(requisicao.src)
            ]
        ):
            caminhos = topology.caminhos_mais_curtos_entre_links_durante_desastre[
                int(requisicao.src)
            ][int(requisicao.dst)]
        else:
            # Final fallback to regular ISP paths or topology paths
            caminhos_isp_regular = (
                FirstFitWeightedSubnetDisasterAware._get_caminhos_from_isp(
                    requisicao, topology, isp_requisicao
                )
            )

            if caminhos_isp_regular:
                return FirstFitWeightedSubnetDisasterAware._processar_caminhos_isp(
                    caminhos_isp_regular, requisicao, topology
                )
            # Use topology paths with ISP filtering
            caminhos = topology.caminhos_mais_curtos_entre_links[int(requisicao.src)][
                int(requisicao.dst)
            ]

        # Process topology-wide paths with ISP filtering
        return FirstFitWeightedSubnetDisasterAware._processar_caminhos_topology(
            caminhos, requisicao, topology, isp_requisicao
        )

    @staticmethod
    def _calculate_link_weights_for_isp(
        isp_id: int, topology: Topology
    ) -> dict[tuple[int, int], float]:
        """Calculate link weights based on usage frequency in shortest paths.

        Links that appear more frequently in shortest paths get higher weights
        (up to 20% increase) to encourage load balancing.

        Args:
            isp_id: ISP identifier
            topology: Network topology

        Returns:
            dict: Mapping from (src, dst) link tuple to weight multiplier (1.0 to 1.2)
        """
        # Find the ISP object
        isp = None
        for isp_obj in topology.lista_de_isps:
            if isp_obj.isp_id == isp_id:
                isp = isp_obj
                break

        if not isp or not isp.caminhos_internos_isp:
            return {}

        # Count link occurrences in shortest paths
        link_count: dict[tuple[int, int], int] = {}
        total_paths = 0

        # Iterate over all precomputed paths in the ISP
        for src_node, dst_dict in isp.caminhos_internos_isp.items():
            for dst_node, path_list in dst_dict.items():
                if not path_list:
                    continue

                # Only consider the shortest path (first one)
                shortest_path_info = path_list[0]
                caminho = shortest_path_info["caminho"]
                total_paths += 1

                # Count each link in this path
                for i in range(len(caminho) - 1):
                    link = (caminho[i], caminho[i + 1])
                    # Count both directions (undirected graph)
                    link_count[link] = link_count.get(link, 0) + 1
                    reverse_link = (caminho[i + 1], caminho[i])
                    link_count[reverse_link] = link_count.get(reverse_link, 0) + 1

        if not link_count or total_paths == 0:
            return {}

        # Calculate average occurrence
        avg_occurrence = sum(link_count.values()) / len(link_count)

        # Normalize to weights between 1.0 and 1.2
        # Links with higher usage get higher weights (making them "longer")
        link_weights: dict[tuple[int, int], float] = {}
        max_count = max(link_count.values())

        for link, count in link_count.items():
            if max_count > 0:
                # Normalize: links with max usage get 1.2, min usage get 1.0
                normalized = count / max_count
                weight = 1.0 + (normalized * 0.2)  # Range: 1.0 to 1.2
            else:
                weight = 1.0
            link_weights[link] = weight

        return link_weights

    @staticmethod
    def _calculate_migration_link_weights(
        topology: Topology,
    ) -> dict[tuple[int, int], float]:
        """Calculate link weights based on migration path usage across ALL ISPs.

        Links that appear more frequently in migration paths get higher weights
        (up to 20% increase) to discourage normal traffic from using them.

        Args:
            topology: Network topology

        Returns:
            dict: Mapping from (src, dst) link tuple to weight multiplier (0.0 to 0.2)
        """
        link_count: dict[tuple[int, int], int] = {}
        total_migration_paths = 0

        # Iterate over all ISPs and their datacenters
        for isp in topology.lista_de_isps:
            # Check if ISP has datacenters
            if not hasattr(isp, "datacenters") or not isp.datacenters:
                continue

            # For each datacenter, get migration paths
            for datacenter in isp.datacenters:
                src = datacenter.source
                dst = datacenter.destination

                # Try to get paths from ISP's internal paths
                # Migration paths are from datacenter source to backup destination
                paths = isp.get_caminhos_entre_nodes(int(src), int(dst))

                if not paths:
                    continue

                # Consider first 3 paths (k-shortest) for migration
                for path_info in paths[:3]:
                    caminho = path_info["caminho"]
                    total_migration_paths += 1

                    # Count each link in the migration path
                    for i in range(len(caminho) - 1):
                        link = (caminho[i], caminho[i + 1])
                        link_count[link] = link_count.get(link, 0) + 1
                        # Count both directions (undirected graph)
                        reverse_link = (caminho[i + 1], caminho[i])
                        link_count[reverse_link] = link_count.get(reverse_link, 0) + 1

        if not link_count or total_migration_paths == 0:
            return {}

        # Normalize to weights between 0.0 and 0.2
        # Links with highest migration usage get +0.2, unused get +0.0
        migration_weights: dict[tuple[int, int], float] = {}
        max_count = max(link_count.values())

        for link, count in link_count.items():
            if max_count > 0:
                # Normalize: links with max usage get 0.2, min usage get 0.0
                normalized = count / max_count
                weight = normalized * 0.2  # Range: 0.0 to 0.2
            else:
                weight = 0.0
            migration_weights[link] = weight

        return migration_weights

    @staticmethod
    def _get_migration_weights(topology: Topology) -> dict[tuple[int, int], float]:
        """Get cached migration link weights or calculate them.

        Migration weights are calculated once and cached globally across all ISPs.

        Args:
            topology: Network topology

        Returns:
            dict: Migration link weights mapping
        """
        if FirstFitWeightedSubnetDisasterAware._migration_weights_cache is None:
            FirstFitWeightedSubnetDisasterAware._migration_weights_cache = (
                FirstFitWeightedSubnetDisasterAware._calculate_migration_link_weights(
                    topology
                )
            )
        return FirstFitWeightedSubnetDisasterAware._migration_weights_cache

    @staticmethod
    def _get_link_weights(
        isp_id: int, topology: Topology
    ) -> dict[tuple[int, int], float]:
        """Get cached link weights or calculate them.

        Args:
            isp_id: ISP identifier
            topology: Network topology

        Returns:
            dict: Link weights mapping
        """
        if isp_id not in FirstFitWeightedSubnetDisasterAware._link_weights_cache:
            FirstFitWeightedSubnetDisasterAware._link_weights_cache[isp_id] = (
                FirstFitWeightedSubnetDisasterAware._calculate_link_weights_for_isp(
                    isp_id, topology
                )
            )
        return FirstFitWeightedSubnetDisasterAware._link_weights_cache[isp_id]

    @staticmethod
    def _calculate_weighted_path_distance(
        caminho: list[int],
        base_distance: float,
        link_weights: dict[tuple[int, int], float],
        migration_weights: dict[tuple[int, int], float] | None = None,
    ) -> float:
        """Calculate weighted distance for a path using combined link weights.

        Combines two weight systems:
        1. ISP-specific weights based on shortest path usage (1.0 to 1.2)
        2. Global migration weights based on migration path usage (0.0 to 0.2)

        Total weight range: 1.0 to 1.4

        Args:
            caminho: List of nodes in the path
            base_distance: Original path distance
            link_weights: Dictionary of ISP-specific link weights
            migration_weights: Dictionary of migration-based link weights

        Returns:
            float: Weighted distance (up to 40% longer than original)
        """
        if not link_weights and not migration_weights:
            return base_distance

        # Calculate average combined weight for links in this path
        total_weight = 0.0
        link_count = 0

        for i in range(len(caminho) - 1):
            link = (caminho[i], caminho[i + 1])

            # Base weight from ISP-specific usage (1.0 to 1.2)
            isp_weight = link_weights.get(link, 1.0) if link_weights else 1.0

            # Additional weight from migration usage (0.0 to 0.2)
            mig_weight = migration_weights.get(link, 0.0) if migration_weights else 0.0

            # Combined weight: 1.0 to 1.4
            combined_weight = isp_weight + mig_weight

            total_weight += combined_weight
            link_count += 1

        if link_count == 0:
            return base_distance

        avg_weight = total_weight / link_count
        return base_distance * avg_weight

    @staticmethod
    def _get_caminhos_desastre_from_isp(
        requisicao: Request, topology: Topology, isp_id: int
    ) -> list[dict]:
        """Get precomputed weighted disaster-aware paths from ISP if available.

        Args:
            requisicao: Network request
            topology: Network topology
            isp_id: ISP identifier

        Returns:
            list[dict]: List of weighted disaster-aware path information from ISP, empty if not available
        """
        # Find the ISP object
        for isp in topology.lista_de_isps:
            if isp.isp_id == isp_id:
                # Use weighted disaster-aware paths if available
                src = int(requisicao.src)
                dst = int(requisicao.dst)

                if (
                    hasattr(isp, "weighted_caminhos_internos_isp_durante_desastre")
                    and src in isp.weighted_caminhos_internos_isp_durante_desastre
                    and dst in isp.weighted_caminhos_internos_isp_durante_desastre[src]
                ):
                    return isp.weighted_caminhos_internos_isp_durante_desastre[src][dst]

                # Fallback to regular disaster-aware paths
                return isp.get_caminhos_entre_nodes_durante_desastre(src, dst)
        return []

    @staticmethod
    def _get_caminhos_from_isp(
        requisicao: Request, topology: Topology, isp_id: int
    ) -> list[dict]:
        """Get precomputed regular paths from ISP if available.

        Args:
            requisicao: Network request
            topology: Network topology
            isp_id: ISP identifier

        Returns:
            list[dict]: List of path information from ISP, empty if not available
        """
        # Find the ISP object
        for isp in topology.lista_de_isps:  # Assuming topology has lista_de_isps
            if isp.isp_id == isp_id:
                return isp.get_caminhos_entre_nodes(
                    int(requisicao.src), int(requisicao.dst)
                )
        return []

    @staticmethod
    def _processar_caminhos_isp(
        caminhos_isp: list[dict], requisicao: Request, topology: Topology
    ) -> tuple[list[dict], bool]:
        """Process ISP precomputed paths with weighted selection.

        Args:
            caminhos_isp: ISP precomputed paths
            requisicao: Network request
            topology: Network topology

        Returns:
            tuple: (list of path information sorted by weighted distance, at least one available window)
        """
        # Get link weights for this ISP
        isp_id = requisicao.src_isp
        link_weights = FirstFitWeightedSubnetDisasterAware._get_link_weights(
            isp_id, topology
        )

        # Get migration weights (global across all ISPs)
        migration_weights = FirstFitWeightedSubnetDisasterAware._get_migration_weights(
            topology
        )

        lista_de_informacoes_datapath = []
        pelo_menos_uma_janela_habil = False

        # Process all paths and calculate weighted distances
        paths_with_weights = []

        for informacoes_caminho in caminhos_isp:
            caminho = informacoes_caminho["caminho"]

            # Verifica se o caminho está em funcionamento
            if not topology.caminho_em_funcionamento(caminho):
                continue

            distancia = informacoes_caminho["distancia"]
            fator_de_modulacao = informacoes_caminho["fator_de_modulacao"]
            numero_slots_necessarios = (
                FirstFitWeightedSubnetDisasterAware.__slots_nescessarios(
                    requisicao.bandwidth, fator_de_modulacao
                )
            )

            lista_de_inicios_e_fins, maior_janela_caminho = (
                FirstFitWeightedSubnetDisasterAware.informacoes_sobre_slots(
                    caminho, topology
                )
            )

            # Calculate weighted distance for path ranking
            # Combines ISP-specific weights + migration weights
            weighted_distance = (
                FirstFitWeightedSubnetDisasterAware._calculate_weighted_path_distance(
                    caminho, distancia, link_weights, migration_weights
                )
            )

            dados_do_caminho = {
                "caminho": caminho,
                "distancia": distancia,
                "weighted_distance": weighted_distance,
                "fator_de_modulacao": fator_de_modulacao,
                "lista_de_inicios_e_fins": lista_de_inicios_e_fins,
                "numero_slots_necessarios": numero_slots_necessarios,
                "maior_janela_contigua_continua": maior_janela_caminho,
            }

            paths_with_weights.append(dados_do_caminho)

            if maior_janela_caminho >= numero_slots_necessarios:
                pelo_menos_uma_janela_habil = True

        # Sort paths by weighted distance (prefer less congested paths)
        paths_with_weights.sort(key=lambda x: x["weighted_distance"])
        lista_de_informacoes_datapath = paths_with_weights

        return (lista_de_informacoes_datapath, pelo_menos_uma_janela_habil)

    @staticmethod
    def _processar_caminhos_topology(
        caminhos: list[dict], requisicao: Request, topology: Topology, isp_id: int
    ) -> tuple[list[dict], bool]:
        """Process topology-wide paths with ISP filtering and weighted selection.

        Args:
            caminhos: Topology paths
            requisicao: Network request
            topology: Network topology
            isp_id: ISP identifier

        Returns:
            tuple: (list of path information sorted by weighted distance, at least one available window)
        """
        # Get link weights for this ISP
        link_weights = FirstFitWeightedSubnetDisasterAware._get_link_weights(
            isp_id, topology
        )

        # Get migration weights (global across all ISPs)
        migration_weights = FirstFitWeightedSubnetDisasterAware._get_migration_weights(
            topology
        )

        lista_de_informacoes_datapath = []
        pelo_menos_uma_janela_habil = False

        # Process all paths and calculate weighted distances
        paths_with_weights = []

        for informacoes_caminho in caminhos:
            caminho = informacoes_caminho["caminho"]

            # Verifica se o caminho está em funcionamento
            if not topology.caminho_em_funcionamento(caminho):
                continue

            # Verifica se todos os nodes do caminho pertencem à mesma ISP (subnet constraint)
            if not FirstFitWeightedSubnetDisasterAware.__caminho_pertence_a_isp(
                caminho, topology, isp_id
            ):
                continue

            distancia = informacoes_caminho["distancia"]
            fator_de_modulacao = informacoes_caminho["fator_de_modulacao"]
            numero_slots_necessarios = (
                FirstFitWeightedSubnetDisasterAware.__slots_nescessarios(
                    requisicao.bandwidth, fator_de_modulacao
                )
            )

            lista_de_inicios_e_fins, maior_janela_caminho = (
                FirstFitWeightedSubnetDisasterAware.informacoes_sobre_slots(
                    caminho, topology
                )
            )

            # Calculate weighted distance for path ranking
            # Combines ISP-specific weights + migration weights
            weighted_distance = (
                FirstFitWeightedSubnetDisasterAware._calculate_weighted_path_distance(
                    caminho, distancia, link_weights, migration_weights
                )
            )

            dados_do_caminho = {
                "caminho": caminho,
                "distancia": distancia,
                "weighted_distance": weighted_distance,
                "fator_de_modulacao": fator_de_modulacao,
                "lista_de_inicios_e_fins": lista_de_inicios_e_fins,
                "numero_slots_necessarios": numero_slots_necessarios,
                "maior_janela_contigua_continua": maior_janela_caminho,
            }

            paths_with_weights.append(dados_do_caminho)

            if maior_janela_caminho >= numero_slots_necessarios:
                pelo_menos_uma_janela_habil = True

        # Sort paths by weighted distance (prefer less congested paths)
        paths_with_weights.sort(key=lambda x: x["weighted_distance"])
        lista_de_informacoes_datapath = paths_with_weights

        return (lista_de_informacoes_datapath, pelo_menos_uma_janela_habil)

    @staticmethod
    def informacoes_sobre_slots(
        caminho, topology: Topology
    ) -> tuple[list[tuple[int, int]], int]:
        """Get information about available slots in a path.

        Args:
            caminho: List of nodes representing the path
            topology: Network topology

        Returns:
            tuple: (list of start-end slot ranges, largest contiguous window)
        """
        lista_de_inicios_e_fins = []
        current_start: int | None = None
        last_slot_was_free = False
        maior_janela = 0

        for i in range(topology.numero_de_slots):
            if FirstFitWeightedSubnetDisasterAware.__checa_concurrency_slot(
                caminho, topology, i
            ):
                if not last_slot_was_free:
                    current_start = i
                    last_slot_was_free = True
                    tamanho_janela_atual = 1
                else:
                    tamanho_janela_atual += 1

            elif last_slot_was_free and current_start is not None:
                lista_de_inicios_e_fins.append((current_start, i - 1))
                maior_janela = max(maior_janela, tamanho_janela_atual)
                last_slot_was_free = False

        if last_slot_was_free and current_start is not None:
            lista_de_inicios_e_fins.append((current_start, i))
            maior_janela = max(maior_janela, tamanho_janela_atual)
            last_slot_was_free = False

        return lista_de_inicios_e_fins, maior_janela

    @staticmethod
    def __checa_concurrency_slot(
        caminho: list, topology: Topology, indice: int
    ) -> bool:
        """Check if a slot is available across all links in the path.

        Args:
            caminho: List of nodes representing the path
            topology: Network topology
            indice: Slot index to check

        Returns:
            bool: True if slot is free across entire path, False otherwise
        """
        for i in range(0, (len(caminho) - 1)):
            if topology.topology[caminho[i]][caminho[i + 1]]["slots"][indice] != 0:
                return False
        return True

    @staticmethod
    def __slots_nescessarios(demanda, fator_modulacao) -> int:
        """Calculate number of slots needed for given demand and modulation.

        Args:
            demanda: Bandwidth demand in Gbps
            fator_modulacao: Modulation factor (1, 2, 3, or 4)

        Returns:
            int: Number of slots required

        Formula: slots = ceil(bandwidth / (modulation_factor * SLOT_SIZE))
        Higher modulation = fewer slots needed
        """
        return int(math.ceil(float(demanda) / (fator_modulacao * SLOT_SIZE)))

    @staticmethod
    def __caminho_pertence_a_isp(
        caminho: list, topology: Topology, isp_id: int
    ) -> bool:
        """Verify if all nodes in the path belong to the specified ISP.

        Args:
            caminho: List of node IDs representing the path
            topology: Network topology
            isp_id: ISP identifier to check

        Returns:
            bool: True if all nodes belong to the ISP, False otherwise
        """
        for node in caminho:
            node_isps = topology.topology.nodes[node]["ISPs"]
            if isp_id not in node_isps:
                return False
        return True
