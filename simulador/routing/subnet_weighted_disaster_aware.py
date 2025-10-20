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


class FirstFitSubnetDisasterAware(RoutingBase):
    """Subnet routing class for same-ISP traffic that avoids disaster nodes."""

    @staticmethod
    def __str__() -> str:
        """Return string representation of the routing method."""
        return "FirstFit subrede evitando nodes de desastre"

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
            FirstFitSubnetDisasterAware.__rotear_requisicao(requisicao, topology, env)
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
            FirstFitSubnetDisasterAware.__rotear_requisicao(requisicao, topology, env)
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
            FirstFitSubnetDisasterAware.__retorna_informacoes_datapaths(
                requisicao, topology
            )
        )
        if pelo_menos_uma_janela_habil:
            FirstFitSubnetDisasterAware.__aloca_requisicao(
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
                FirstFitSubnetDisasterAware.__aloca_datapath(
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
            FirstFitSubnetDisasterAware._get_caminhos_desastre_from_isp(
                requisicao, topology, isp_requisicao
            )
        )

        if caminhos_isp_desastre:
            # Use ISP disaster-aware precomputed paths
            return FirstFitSubnetDisasterAware._processar_caminhos_isp(
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
            caminhos_isp_regular = FirstFitSubnetDisasterAware._get_caminhos_from_isp(
                requisicao, topology, isp_requisicao
            )

            if caminhos_isp_regular:
                return FirstFitSubnetDisasterAware._processar_caminhos_isp(
                    caminhos_isp_regular, requisicao, topology
                )
            # Use topology paths with ISP filtering
            caminhos = topology.caminhos_mais_curtos_entre_links[int(requisicao.src)][
                int(requisicao.dst)
            ]

        # Process topology-wide paths with ISP filtering
        return FirstFitSubnetDisasterAware._processar_caminhos_topology(
            caminhos, requisicao, topology, isp_requisicao
        )

    @staticmethod
    def _get_caminhos_desastre_from_isp(
        requisicao: Request, topology: Topology, isp_id: int
    ) -> list[dict]:
        """Get precomputed disaster-aware paths from ISP if available.

        Args:
            requisicao: Network request
            topology: Network topology
            isp_id: ISP identifier

        Returns:
            list[dict]: List of disaster-aware path information from ISP, empty if not available
        """
        # Find the ISP object
        for isp in topology.lista_de_isps:  # Assuming topology has lista_de_isps
            if isp.isp_id == isp_id:
                return isp.get_caminhos_entre_nodes_durante_desastre(
                    int(requisicao.src), int(requisicao.dst)
                )
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
        """Process ISP precomputed paths.

        Args:
            caminhos_isp: ISP precomputed paths
            requisicao: Network request
            topology: Network topology

        Returns:
            tuple: (list of path information, at least one available window)
        """
        lista_de_informacoes_datapath = []
        pelo_menos_uma_janela_habil = False

        for informacoes_caminho in caminhos_isp:
            caminho = informacoes_caminho["caminho"]

            # Verifica se o caminho está em funcionamento
            if not topology.caminho_em_funcionamento(caminho):
                continue

            distancia = informacoes_caminho["distancia"]
            fator_de_modulacao = informacoes_caminho["fator_de_modulacao"]
            numero_slots_necessarios = FirstFitSubnetDisasterAware.__slots_nescessarios(
                requisicao.bandwidth, fator_de_modulacao
            )

            lista_de_inicios_e_fins, maior_janela_caminho = (
                FirstFitSubnetDisasterAware.informacoes_sobre_slots(caminho, topology)
            )

            dados_do_caminho = {
                "caminho": caminho,
                "distancia": distancia,
                "fator_de_modulacao": fator_de_modulacao,
                "lista_de_inicios_e_fins": lista_de_inicios_e_fins,
                "numero_slots_necessarios": numero_slots_necessarios,
                "maior_janela_contigua_continua": maior_janela_caminho,
            }

            lista_de_informacoes_datapath.append(dados_do_caminho)
            if maior_janela_caminho >= numero_slots_necessarios:
                pelo_menos_uma_janela_habil = True
                break

        return (lista_de_informacoes_datapath, pelo_menos_uma_janela_habil)

    @staticmethod
    def _processar_caminhos_topology(
        caminhos: list[dict], requisicao: Request, topology: Topology, isp_id: int
    ) -> tuple[list[dict], bool]:
        """Process topology-wide paths with ISP filtering.

        Args:
            caminhos: Topology paths
            requisicao: Network request
            topology: Network topology
            isp_id: ISP identifier

        Returns:
            tuple: (list of path information, at least one available window)
        """
        lista_de_informacoes_datapath = []
        pelo_menos_uma_janela_habil = False

        for informacoes_caminho in caminhos:
            caminho = informacoes_caminho["caminho"]

            # Verifica se o caminho está em funcionamento
            if not topology.caminho_em_funcionamento(caminho):
                continue

            # Verifica se todos os nodes do caminho pertencem à mesma ISP (subnet constraint)
            if not FirstFitSubnetDisasterAware.__caminho_pertence_a_isp(
                caminho, topology, isp_id
            ):
                continue

            distancia = informacoes_caminho["distancia"]
            fator_de_modulacao = informacoes_caminho["fator_de_modulacao"]
            numero_slots_necessarios = FirstFitSubnetDisasterAware.__slots_nescessarios(
                requisicao.bandwidth, fator_de_modulacao
            )

            lista_de_inicios_e_fins, maior_janela_caminho = (
                FirstFitSubnetDisasterAware.informacoes_sobre_slots(caminho, topology)
            )

            dados_do_caminho = {
                "caminho": caminho,
                "distancia": distancia,
                "fator_de_modulacao": fator_de_modulacao,
                "lista_de_inicios_e_fins": lista_de_inicios_e_fins,
                "numero_slots_necessarios": numero_slots_necessarios,
                "maior_janela_contigua_continua": maior_janela_caminho,
            }

            lista_de_informacoes_datapath.append(dados_do_caminho)
            if maior_janela_caminho >= numero_slots_necessarios:
                pelo_menos_uma_janela_habil = True
                break

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
            if FirstFitSubnetDisasterAware.__checa_concurrency_slot(
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
