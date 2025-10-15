from __future__ import annotations

import simpy
import simpy.events


class Request:
    def __init__(
        self,
        req_id: str,
        src: int,
        dst: int,
        src_isp_index: int,
        dst_isp_index: int,
        bandwidth: int,
        class_type: int,
        holding_time: float,
        requisicao_de_migracao: bool = False,
    ) -> None:
        """Initialize the Request class.

        Args:
            req_id: The ID of the request
            src: The source node of the request
            dst: The destination node of the request
            src_isp_index: The index of the source ISP
            dst_isp_index: The index of the destination ISP
            bandwidth: The bandwidth of the request
            class_type: The class type of the request
            holding_time: The holding time of the request
            requisicao_de_migracao: Whether the request is a migration request

        Returns:
            None
        """
        self.req_id: str = req_id
        self.src: int = src
        self.dst: int = dst
        self.src_isp_index: int = src_isp_index
        self.dst_isp_index: int = dst_isp_index
        self.src_isp: int = src_isp_index  # Alias for compatibility
        self.dst_isp: int = dst_isp_index  # Alias for compatibility
        self.bandwidth: int = bandwidth
        self.class_type: int = class_type
        self.holding_time: float = holding_time

        self.requisicao_de_migracao: bool = requisicao_de_migracao
        self.bloqueada: bool | None = None

        self.afetada_por_desastre: bool = False
        self.dados_pre_reroteamento: tuple[str, dict] | None = None

        self.processo_de_desalocacao: simpy.events.Process | None = None

        self.numero_de_slots: int | None = None
        self.caminho: list[int] | None = None
        self.tamanho_do_caminho: int | None = None
        self.index_de_inicio_e_final: tuple[int, int] | None = None
        self.tempo_criacao: float | None = None
        self.tempo_desalocacao: float | None = None
        self.distacia: int | None = None

    def bloqueia_requisicao(self, tempo_criacao: float) -> None:
        self.numero_de_slots = None
        self.caminho = None
        self.tamanho_do_caminho = None
        self.index_de_inicio_e_final = None
        self.tempo_criacao = tempo_criacao
        self.tempo_desalocacao = None
        self.distacia = None
        self.bloqueada = True

    def aceita_requisicao(
        self,
        numero_de_slots: int,
        caminho: list[int],
        tamanho_do_caminho: int,
        index_de_inicio_e_final: tuple[int, int],
        tempo_criacao: float,
        tempo_desalocacao: float,
        distancia: int,
    ) -> None:
        self.numero_de_slots = numero_de_slots
        self.caminho = caminho
        self.tamanho_do_caminho = tamanho_do_caminho
        self.index_de_inicio_e_final = index_de_inicio_e_final
        self.tempo_criacao = tempo_criacao
        self.tempo_desalocacao = tempo_desalocacao
        self.distacia = distancia
        self.bloqueada = False

    def retorna_tupla_chave_dicionario_dos_atributos(self) -> tuple[str, dict]:
        return (
            self.req_id,
            {
                "src": self.src,
                "dst": self.dst,
                "src_isp_index": self.src_isp_index,
                "dst_isp_index": self.dst_isp_index,
                "bandwidth": self.bandwidth,
                "class_type": self.class_type,
                "holding_time": self.holding_time,
                "requisicao_de_migracao": self.requisicao_de_migracao,
                "bloqueada": self.bloqueada,
                "afetada_por_desastre": self.afetada_por_desastre,
                "numero_de_slots": self.numero_de_slots,
                "caminho": self.caminho,
                "tamanho_do_caminho": self.tamanho_do_caminho,
                "index_de_inicio_e_final": self.index_de_inicio_e_final,
                "tempo_criacao": self.tempo_criacao,
                "tempo_desalocacao": self.tempo_desalocacao,
                "distacia": self.distacia,
                "dados_pre_reroteamento": self.dados_pre_reroteamento,
            },
        )
