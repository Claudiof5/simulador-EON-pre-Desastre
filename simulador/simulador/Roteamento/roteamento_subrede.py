"""Subnet routing implementation for same-ISP traffic.

This module implements routing logic that ensures traffic only uses
nodes belonging to the same ISP (Internet Service Provider).
"""

import math
from typing import TYPE_CHECKING

from registrador import Registrador
from Requisicao.requisicao import Requisicao
from Roteamento.IRoteamento import IRoteamento
from simpy import Environment
from variaveis import *

if TYPE_CHECKING:
    from Topology.Topologia import Topologia


class RoteamentoSubrede(IRoteamento):
    """Subnet routing class for same-ISP traffic only."""
    
    @classmethod
    def __str__(cls) -> str:
        """Return string representation of the routing method."""
        return "Roteamento apenas subrede"

    def rotear_requisicao(
        requisicao: Requisicao, topology: "Topologia", env: Environment
    ) -> bool:
        """Route a request within the same ISP subnet.
        
        Args:
            requisicao: Network request to route
            topology: Network topology
            env: Simulation environment
            
        Returns:
            bool: True if routing successful, False otherwise
        """
        requisicao_roteada_com_sucesso = Roteamento.__rotear_requisicao(
            requisicao, topology, env
        )
        if requisicao_roteada_com_sucesso:
            Registrador.incrementa_numero_requisicoes_aceitas(requisicao, env)
            return True
        Registrador.incrementa_numero_requisicoes_bloqueadas(requisicao, env)
        return False

    def rerotear_requisicao(
        requisicao: Requisicao, topology: "Topologia", env: Environment
    ) -> bool:
        """Reroute a request within the same ISP subnet.
        
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

        requisicao_roteada_com_sucesso = Roteamento.__rotear_requisicao(
            requisicao, topology, env
        )

        if requisicao_roteada_com_sucesso:
            Registrador.incrementa_numero_requisicoes_reroteadas_aceitas(
                requisicao, env
            )
            return True
        Registrador.incrementa_numero_requisicoes_reroteadas_bloqueadas(requisicao, env)
        return False

    def __rotear_requisicao(
        requisicao: Requisicao, topology: "Topologia", env: Environment
    ) -> bool:
        """Internal method to route a request within subnet constraints.
        
        Args:
            requisicao: Network request to route
            topology: Network topology
            env: Simulation environment
            
        Returns:
            bool: True if routing successful, False otherwise
        """
        informacoes_dos_datapaths, pelo_menos_uma_janela_habil = (
            Roteamento.__retorna_informacoes_datapaths(requisicao, topology)
        )
        if pelo_menos_uma_janela_habil:
            Roteamento.__aloca_requisicao(
                requisicao, topology, informacoes_dos_datapaths, env
            )
            return True

        requisicao.bloqueia_requisicao(env.now)
        return False

    def __aloca_requisicao(
        requisicao: Requisicao,
        topology: "Topologia",
        informacoes_datapaths: dict,
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
                Roteamento.__aloca_datapath(
                    requisicao, topology, informacoes_datapath, env
                )
                break

    def __aloca_datapath(
        requisicao: Requisicao,
        topology: "Topologia",
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
        # janelas_possiveis = [ janela for janela in informacoes_datapath["slots_livres_agrupados"] if len(janela) >= informacoes_datapath["numero_slots_necessarios"]]
        index_inicio = next(
            (
                index_inicio
                for index_inicio, index_final in informacoes_datapath[
                    "lista_de_inicios_e_fins"
                ]
                if index_final - index_inicio + 1
                >= informacoes_datapath["numero_slots_necessarios"]
            ),
            None,
        )

        index_final = (
            index_inicio + informacoes_datapath["numero_slots_necessarios"] - 1
        )
        caminho = informacoes_datapath["caminho"]

        topology.aloca_janela(caminho, [index_inicio, index_final])

        requisicao.processo_de_desalocacao = env.process(
            topology.desaloca_janela(
                caminho, [index_inicio, index_final], requisicao.holding_time, env
            )
        )

        requisicao.aceita_requisicao(
            informacoes_datapath["numero_slots_necessarios"],
            caminho,
            len(caminho),
            [index_inicio, index_final],
            env.now,
            env.now + requisicao.holding_time,
            informacoes_datapath["distancia"],
        )

    def __retorna_informacoes_datapaths(
        requisicao: Requisicao, topology: "Topologia"
    ) -> tuple[list[dict], bool]:
        """Return information about available datapaths for subnet routing.
        
        Uses precomputed ISP internal paths when available, otherwise falls back
        to topology-wide paths filtered by ISP membership.
        """
        # Identifica a ISP da requisição (src_isp deve ser igual a dst_isp no tráfego de subrede)
        isp_requisicao = requisicao.src_isp
        
        # Try to get ISP-specific precomputed paths first
        caminhos_isp = Roteamento._get_caminhos_from_isp(
            requisicao, topology, isp_requisicao
        )
        
        if caminhos_isp:
            # Use ISP precomputed paths
            lista_de_informacoes_datapath = []
            pelo_menos_uma_janela_habil = False
            
            for informacoes_caminho in caminhos_isp:
                caminho = informacoes_caminho["caminho"]
                
                # Verifica se o caminho está em funcionamento
                if not topology.caminho_em_funcionamento(caminho):
                    continue
                    
                distancia = informacoes_caminho["distancia"]
                fator_de_modulacao = informacoes_caminho["fator_de_modulacao"]
                numero_slots_necessarios = Roteamento.__slots_nescessarios(
                    requisicao.bandwidth, fator_de_modulacao
                )

                lista_de_inicios_e_fins, maior_janela_caminho = (
                    Roteamento.informacoes_sobre_slots(caminho, topology)
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
        
        else:
            # Fallback to topology-wide paths with ISP filtering
            return Roteamento._get_caminhos_from_topology_filtered(
                requisicao, topology, isp_requisicao
            )

    @staticmethod
    def _get_caminhos_from_isp(
        requisicao: Requisicao, topology: "Topologia", isp_id: int
    ) -> list[dict]:
        """Get precomputed paths from ISP if available.
        
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
                return isp.get_caminhos_entre_nodes(int(requisicao.src), int(requisicao.dst))
        return []
    
    @staticmethod
    def _get_caminhos_from_topology_filtered(
        requisicao: Requisicao, topology: "Topologia", isp_id: int
    ) -> tuple[list[dict], bool]:
        """Get paths from topology with ISP filtering (fallback method).
        
        Args:
            requisicao: Network request
            topology: Network topology
            isp_id: ISP identifier
            
        Returns:
            tuple: (list of path information, at least one available window)
        """
        caminhos = topology.caminhos_mais_curtos_entre_links[int(requisicao.src)][
            int(requisicao.dst)
        ]

        lista_de_informacoes_datapath = []
        pelo_menos_uma_janela_habil = False

        for informacoes_caminho in caminhos:
            caminho = informacoes_caminho["caminho"]
            
            # Verifica se o caminho está em funcionamento
            if not topology.caminho_em_funcionamento(caminho):
                continue
                
            # Verifica se todos os nodes do caminho pertencem à mesma ISP
            if not Roteamento.__caminho_pertence_a_isp(caminho, topology, isp_id):
                continue
                
            distancia = informacoes_caminho["distancia"]
            fator_de_modulacao = informacoes_caminho["fator_de_modulacao"]
            numero_slots_necessarios = Roteamento.__slots_nescessarios(
                requisicao.bandwidth, fator_de_modulacao
            )

            lista_de_inicios_e_fins, maior_janela_caminho = (
                Roteamento.informacoes_sobre_slots(caminho, topology)
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

    def informacoes_sobre_slots(
        caminho, topology: "Topologia"
    ) -> tuple[list[tuple[int, int]], int]:
        """Get information about available slots in a path.
        
        Args:
            caminho: List of nodes representing the path
            topology: Network topology
            
        Returns:
            tuple: (list of start-end slot ranges, largest contiguous window)
        """
        lista_de_inicios_e_fins = []
        current_start = None
        last_slot_was_free = False
        maior_janela = 0

        for i in range(topology.numero_de_slots):
            if Roteamento.__checa_concurrency_slot(caminho, topology, i):
                if not last_slot_was_free:
                    current_start = i
                    last_slot_was_free = True
                    tamanho_janela_atual = 1
                else:
                    tamanho_janela_atual += 1

            elif last_slot_was_free:
                lista_de_inicios_e_fins.append((current_start, i - 1))
                maior_janela = max(maior_janela, tamanho_janela_atual)
                last_slot_was_free = False

        if last_slot_was_free:
            lista_de_inicios_e_fins.append((current_start, i))
            maior_janela = max(maior_janela, tamanho_janela_atual)
            last_slot_was_free = False

        return lista_de_inicios_e_fins, maior_janela

    def __checa_concurrency_slot(
        caminho: list, topology: "Topologia", indice: int
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

    def __slots_nescessarios(demanda, fator_modulacao) -> int:
        """Calculate number of slots needed for given demand and modulation.
        
        Args:
            demanda: Bandwidth demand
            fator_modulacao: Modulation factor
            
        Returns:
            int: Number of slots required
        """
        return int(math.ceil(float(demanda) / fator_modulacao))

    @staticmethod
    def __caminho_pertence_a_isp(
        caminho: list, topology: "Topologia", isp_id: int
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
