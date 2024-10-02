import simpy
import simpy.events

class Requisicao:

    def __init__(self, id: str, src: int, dst: int, src_ISP: int, dst_ISP: int, bandwidth: int, class_type: int, holding_time: float, requisicao_de_migracao: bool = False ):
        self.id: str = id
        self.src: int = src
        self.dst: int = dst
        self.src_ISP_index: int = src_ISP
        self.dst_ISP_index: int = dst_ISP
        self.bandwidth: int = bandwidth
        self.class_type: int = class_type
        self.holding_time: float = holding_time

        self.requisicao_de_migracao: bool = requisicao_de_migracao
        self.bloqueada: bool = None

        self.afetada_por_desastre: bool = False
        self.dados_pre_reroteamento: dict = None

        self.processo_de_desalocacao :simpy.events.Process = None
    
        self.numero_de_slots: int = None
        self.caminho: list[int] = None
        self.tamanho_do_caminho: int = None
        self.index_de_inicio_e_final: tuple[int, int] = None
        self.tempo_criacao: float = None
        self.tempo_desalocacao: float = None
        self.distacia: int = None
        
    def bloqueia_requisicao(self, tempo_criacao: float) -> None:
        
        self.numero_de_slots: int = None
        self.caminho: list[int] = None
        self.tamanho_do_caminho: int = None
        self.index_de_inicio_e_final: tuple[int, int] = None
        self.tempo_criacao: float = tempo_criacao
        self.tempo_desalocacao: float = None
        self.distacia: int = None
        self.bloqueada: bool = True
    					
    def aceita_requisicao(self, numero_de_slots: int, caminho: list[int], tamanho_do_caminho: int, index_de_inicio_e_final: tuple[int, int], tempo_criacao: float, tempo_desalocacao: float, distancia: int) -> None:
        
        self.numero_de_slots: int = numero_de_slots
        self.caminho: list[int] = caminho
        self.tamanho_do_caminho: int = tamanho_do_caminho
        self.index_de_inicio_e_final: tuple[int, int] = index_de_inicio_e_final
        self.tempo_criacao: float = tempo_criacao
        self.tempo_desalocacao: float = tempo_desalocacao
        self.distacia: int = distancia
        self.bloqueada: bool = False

    def retorna_tupla_chave_dicionario_dos_atributos(self) -> tuple[int, dict]:
        return ( self.id, {
            "src": self.src,
            "dst": self.dst,
            "src_ISP_index": self.src_ISP_index,
            "dst_ISP_index": self.dst_ISP_index,
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
            "dados_pre_reroteamento": self.dados_pre_reroteamento
        })