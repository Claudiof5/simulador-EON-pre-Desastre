import random
from typing import TYPE_CHECKING

from numpy.random import choice, normal

from simulador.config.settings import (
    BANDWIDTH,
    CLASS_TYPE,
    CLASS_WEIGHT,
    HOLDING_TIME,
    REQUISICOES_POR_SEGUNDO,
)
from simulador.core.request import Request
from simulador.utils.metrics import Metrics

# Constante para número mínimo de nodes em uma ISP para tráfego de subrede
MIN_NODES_PER_ISP = 2

if TYPE_CHECKING:
    from simulador import Topology
    from simulador.entities.datacenter import Datacenter
    from simulador.entities.disaster import Disaster
    from simulador.entities.isp import ISP


class TrafficGenerator:
    @staticmethod
    def gerar_requisicao(
        topology: "Topology",
        req_id: int,
        specific_values: dict | None = None,
        trafego_subrede: bool = True,
    ) -> Request:
        """Generate a network request with random or specific values.

        Args:
            topology: Network topology
            req_id: Request identifier
            specific_values: Optional specific values to override defaults
            trafego_subrede: If True, generates subnet traffic (same ISP),
                           if False, uses original behavior (any ISP)

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
        topology: "Topology", req_id: int, trafego_subrede: bool = False
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

        if trafego_subrede:
            # Comportamento novo: tráfego de subrede (mesma ISP)
            isps_disponiveis = TrafficGenerator._get_isps_com_multiplos_nodes(topology)
            if not isps_disponiveis:
                # Fallback para comportamento original se não houver ISPs com múltiplos nodes
                src, dst = choice(
                    topology.topology.nodes, MIN_NODES_PER_ISP, replace=False
                )
                src_isp = choice(topology.topology.nodes[src]["ISPs"])
                dst_isp = src_isp  # Força mesma ISP
            else:
                # Seleciona ISP aleatória que tem pelo menos 2 nodes
                selected_isp = choice(isps_disponiveis)

                # Seleciona src e dst dentro da mesma ISP
                nodes_da_isp = TrafficGenerator._get_nodes_da_isp(
                    topology, selected_isp
                )
                src, dst = choice(nodes_da_isp, MIN_NODES_PER_ISP, replace=False)
                src_isp = dst_isp = selected_isp
        else:
            # Comportamento original: qualquer ISP
            src, dst = choice(topology.topology.nodes, MIN_NODES_PER_ISP, replace=False)
            src_isp = choice(topology.topology.nodes[src]["ISPs"])
            dst_isp = choice(topology.topology.nodes[dst]["ISPs"])

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
        topology: "Topology", req_id: int, specific_values: dict
    ) -> Request:
        """Generate a request with specific values."""
        src, dst = TrafficGenerator._get_src_dst(topology, specific_values)
        src_isp = specific_values.get("src_isp") or choice(
            topology.topology.nodes[src]["ISPs"]
        )
        dst_isp = specific_values.get("dst_isp") or choice(
            topology.topology.nodes[dst]["ISPs"]
        )
        bandwidth = specific_values.get("bandwidth") or choice(BANDWIDTH)
        holding_time = specific_values.get("holding_time") or normal(
            HOLDING_TIME, HOLDING_TIME * 0.1
        )
        class_type = specific_values.get("class_type") or choice(
            CLASS_TYPE, p=CLASS_WEIGHT
        )
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
    def _get_src_dst(topology: "Topology", specific_values: dict) -> tuple[int, int]:
        """Get source and destination nodes."""
        src = specific_values.get("src")
        dst = specific_values.get("dst")

        if src is None and dst is None:
            nodes = choice(topology.topology.nodes, 2, replace=False)
            return int(nodes[0]), int(nodes[1])
        if src is None:
            return int(choice(topology.topology.nodes)), int(
                dst
            ) if dst is not None else 0
        if dst is None:
            return int(src) if src is not None else 0, int(
                choice(topology.topology.nodes)
            )
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
    def _get_isps_com_multiplos_nodes(topology: "Topology") -> list[int]:
        """Get ISPs that have at least 2 nodes for subnet traffic generation.

        Args:
            topology: Network topology

        Returns:
            list[int]: List of ISP IDs that have multiple nodes
        """
        isp_node_count: dict[int, int] = {}

        # Conta quantos nodes cada ISP tem
        for node in topology.topology.nodes():
            for isp_id in topology.topology.nodes[node]["ISPs"]:
                isp_node_count[isp_id] = isp_node_count.get(isp_id, 0) + 1

        # Retorna ISPs com pelo menos 2 nodes
        return [
            isp_id
            for isp_id, count in isp_node_count.items()
            if count >= MIN_NODES_PER_ISP
        ]

    @staticmethod
    def _get_nodes_da_isp(topology: "Topology", isp_id: int) -> list[int]:
        """Get all nodes that belong to a specific ISP.

        Args:
            topology: Network topology
            isp_id: ISP identifier

        Returns:
            list[int]: List of node IDs belonging to the ISP
        """
        nodes_da_isp = []
        for node in topology.topology.nodes():
            if isp_id in topology.topology.nodes[node]["ISPs"]:
                nodes_da_isp.append(node)
        return nodes_da_isp

    @staticmethod
    def gerar_lista_de_requisicoes(
        topology: "Topology",
        numero_de_requisicoes: int,
        lista_de_isps: list["ISP"],
        desastre: "Disaster",
        trafego_subrede: bool = True,
    ) -> list[Request]:
        """Generate a list of network requests including datacenter requests.

        Args:
            topology: Network topology
            numero_de_requisicoes: Number of requests to generate
            lista_de_isps: List of ISPs
            desastre: Disaster scenario
            trafego_subrede: If True, generates subnet traffic (same ISP),
                           if False, uses original behavior (any ISP)

        Returns:
            list[Request]: List of generated network requests sorted by creation time

        """
        lista_de_requisicoes_nao_processadas: list[Request] = []
        tempo_de_criacao: float = 0.0
        for i in range(1, numero_de_requisicoes + 1):
            requisicao = TrafficGenerator.gerar_requisicao(
                topology, i, trafego_subrede=trafego_subrede
            )
            tempo_de_criacao = tempo_de_criacao + random.expovariate(
                REQUISICOES_POR_SEGUNDO
            )
            requisicao.tempo_criacao = tempo_de_criacao
            lista_de_requisicoes_nao_processadas.append(requisicao)

        for isp in lista_de_isps:
            if isp.datacenter is not None:
                datacenter_reqs = (
                    TrafficGenerator.gerar_lista_de_requisicoes_datacenter(
                        isp.datacenter, desastre, topology, isp.isp_id
                    )
                )
                if datacenter_reqs is not None:
                    lista_de_requisicoes_nao_processadas += datacenter_reqs

        lista_de_requisicoes_nao_processadas.sort(key=lambda x: x.tempo_criacao or 0.0)

        return lista_de_requisicoes_nao_processadas

    @staticmethod
    def gerar_lista_de_requisicoes_datacenter(
        datacenter: "Datacenter",
        desastre: "Disaster",
        topologia: "Topology",
        isp_id: int,
    ) -> list[Request]:
        tempo_de_criacao = datacenter.tempo_de_reacao
        req_id = 0
        lista_de_requisicoes = []
        taxa_mensagens = datacenter.throughput_por_segundo / (
            sum(BANDWIDTH) / len(BANDWIDTH)
        )
        while tempo_de_criacao < desastre.start:
            dict_values = {
                "src": int(datacenter.source),
                "dst": int(datacenter.destination),
                "src_isp": int(isp_id),
                "dst_isp": int(isp_id),
                "requisicao_de_migracao": True,
            }

            requisicao: Request = TrafficGenerator.gerar_requisicao(
                topologia, req_id, dict_values
            )
            tempo_de_criacao += random.expovariate(taxa_mensagens)
            requisicao.tempo_criacao = tempo_de_criacao
            lista_de_requisicoes.append(requisicao)
            req_id += 1

        # datacenter.lista_de_requisicoes = lista_de_requisicoes
        return lista_de_requisicoes
