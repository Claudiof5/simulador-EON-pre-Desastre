import random
from typing import TYPE_CHECKING

from numpy.random import choice, normal
from registrador import Registrador
from Requisicao.requisicao import Requisicao
from variaveis import (
    BANDWIDTH,
    CLASS_TYPE,
    CLASS_WEIGHT,
    HOLDING_TIME,
    REQUISICOES_POR_SEGUNDO,
)

if TYPE_CHECKING:
    from Datacenter.Datacenter import Datacenter
    from Desastre.Desastre import Desastre
    from ISP.ISP import ISP
    from Topology.Topologia import Topologia


class GeradorDeTrafego:
    @staticmethod
    def gerar_requisicao(
        topology: "Topologia", req_id: int, specific_values: dict | None = None
    ) -> Requisicao:
        """Generate a network request with random or specific values.

        Args:
            topology: Network topology
            req_id: Request identifier
            specific_values: Optional specific values to override defaults

        Returns:
            Requisicao: Generated network request

        """
        if specific_values is None:
            return GeradorDeTrafego._gerar_requisicao_aleatoria(topology, req_id)

        return GeradorDeTrafego._gerar_requisicao_especifica(
            topology, req_id, specific_values
        )

    @staticmethod
    def _gerar_requisicao_aleatoria(topology: "Topologia", req_id: int) -> Requisicao:
        """Generate a request with random values."""
        class_type = choice(CLASS_TYPE, p=CLASS_WEIGHT)
        src, dst = choice(topology.topology.nodes, 2, replace=False)
        src_isp = choice(topology.topology.nodes[src]["ISPs"])
        dst_isp = choice(topology.topology.nodes[dst]["ISPs"])
        bandwidth = choice(BANDWIDTH)
        holding_time = normal(HOLDING_TIME, HOLDING_TIME * 0.1)
        requisicao_de_migracao = False

        return GeradorDeTrafego._criar_requisicao(
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
        topology: "Topologia", req_id: int, specific_values: dict
    ) -> Requisicao:
        """Generate a request with specific values."""
        src, dst = GeradorDeTrafego._get_src_dst(topology, specific_values)
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

        return GeradorDeTrafego._criar_requisicao(
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
    def _get_src_dst(topology: "Topologia", specific_values: dict) -> tuple[int, int]:
        """Get source and destination nodes."""
        src = specific_values.get("src")
        dst = specific_values.get("dst")

        if src is None and dst is None:
            return choice(topology.topology.nodes, 2, replace=False)
        if src is None:
            return choice(topology.topology.nodes), dst
        if dst is None:
            return src, choice(topology.topology.nodes)
        return src, dst

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
    ) -> Requisicao:
        """Create and register a request."""
        Registrador.conta_requisicao_banda(bandwidth)
        Registrador.conta_requisicao_classe(class_type)

        return Requisicao(
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
    def gerar_lista_de_requisicoes(
        topology: "Topologia",
        numero_de_requisicoes: int,
        lista_de_isps: list["ISP"],
        desastre: "Desastre",
    ) -> list[Requisicao]:
        lista_de_requisicoes_nao_processadas: list[Requisicao] = []
        tempo_de_criacao = 0
        for i in range(1, numero_de_requisicoes + 1):
            requisicao = GeradorDeTrafego.gerar_requisicao(topology, i)
            tempo_de_criacao += random.expovariate(REQUISICOES_POR_SEGUNDO)
            requisicao.tempo_criacao = tempo_de_criacao
            lista_de_requisicoes_nao_processadas.append(requisicao)

        for isp in lista_de_isps:
            lista_de_requisicoes_nao_processadas += (
                GeradorDeTrafego.gerar_lista_de_requisicoes_datacenter(
                    isp.datacenter, desastre, topology, isp.id
                )
            )

        lista_de_requisicoes_nao_processadas.sort(key=lambda x: x.tempo_criacao)

        return lista_de_requisicoes_nao_processadas

    @staticmethod
    def gerar_lista_de_requisicoes_datacenter(
        datacenter: "Datacenter",
        desastre: "Desastre",
        topologia: "Topologia",
        isp_id: int,
    ) -> None:
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

            requisicao: Requisicao = GeradorDeTrafego.gerar_requisicao(
                topologia, f"{isp_id}.{req_id}", dict_values
            )
            tempo_de_criacao += random.expovariate(taxa_mensagens)
            requisicao.tempo_criacao = tempo_de_criacao
            lista_de_requisicoes.append(requisicao)
            req_id += 1

        # datacenter.lista_de_requisicoes = lista_de_requisicoes
        return lista_de_requisicoes
