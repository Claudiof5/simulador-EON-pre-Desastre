from numpy.random import choice, normal
from Registrador import Registrador
from Variaveis import *
from Requisicao.Requisicao import Requisicao
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Topologia import Topologia

class GeradorDeTrafego:
    

    def gerar_requisicao( topology: 'Topologia', id :int, specific_values :dict = None)-> Requisicao:
        
        if specific_values == None:
            class_type = choice(CLASS_TYPE, p=CLASS_WEIGHT)
            src, dst = choice(topology.topology.nodes, 2, replace=False)
            src_ISP = choice( topology.topology.nodes[src]["ISPs"])
            dst_ISP = choice( topology.topology.nodes[dst]["ISPs"])
            
            bandwidth = choice(BANDWIDTH)
            holding_time = normal(HOLDING_TIME, HOLDING_TIME*0.1)
            requisicao_de_migracao = False
        else:
            src = specific_values["src"]
            dst = specific_values["dst"]
            src_ISP = specific_values["src_ISP"]
            dst_ISP = specific_values["dst_ISP"]
            bandwidth = specific_values["bandwidth"]
            holding_time = specific_values["holding_time"]
            class_type = specific_values["class_type"]
            requisicao_de_migracao = specific_values["requisicao_de_migracao"]

        Registrador.conta_requisicao_banda(bandwidth)
        Registrador.conta_requisicao_classe(class_type)

        return Requisicao( str(id), src, dst, src_ISP, dst_ISP, bandwidth, class_type, holding_time, requisicao_de_migracao)

    def gerar_lista_de_requisicoes( topology: 'Topologia', numero_de_requisicoes: int) -> list[Requisicao]:
        lista_de_requisicoes_nao_processadas: list[Requisicao] = []
        for i in range(1, numero_de_requisicoes + 1):
            lista_de_requisicoes_nao_processadas.append(GeradorDeTrafego.gerar_requisicao(topology, i))
        return lista_de_requisicoes_nao_processadas
