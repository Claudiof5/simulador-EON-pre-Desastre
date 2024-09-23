from numpy.random import choice, normal
from Registrador import Registrador
from Topologia import Topologia
from Requisicao.Requisicao import Requisicao
from Variaveis import *

class GeradorDeTrafico:
    

    def gerar_requisicao( topology: Topologia, id :int, specific_values :dict = None)-> Requisicao:
        
        if specific_values == None:
            class_type = choice(CLASS_TYPE, p=CLASS_WEIGHT)
            src, dst = choice(topology.topology.nodes, 2, replace=False)
            src_ISP = choice( topology.topology.nodes[src]["ISPs"])
            dst_ISP = choice( topology.topology.nodes[dst]["ISPs"])
            
            bandwidth = choice(BANDWIDTH)
            holding_time = normal(HOLDING_TIME, HOLDING_TIME*0.1)
        else:
            src = specific_values["src"]
            dst = specific_values["dst"]
            src_ISP = specific_values["src_ISP"]
            dst_ISP = specific_values["dst_ISP"]
            bandwidth = specific_values["bandwidth"]
            holding_time = specific_values["holding_time"]
            class_type = specific_values["class_type"]

        Registrador.conta_requisicao_banda(bandwidth)
        Registrador.conta_requisicao_classe(class_type)

        return Requisicao( str(id), src, dst, src_ISP, dst_ISP, bandwidth, class_type, holding_time)

