import random
from Contador import Contador
from Topologia import Topologia
from Requisicao.Requisicao import Requisicao
from Variaveis import *

class GeradorDeTrafico:
    

    def gerar_requisicao(self, topology: Topologia, id :int)-> Requisicao:

        class_type = random.choice(CLASS_TYPE, p=CLASS_WEIGHT)
        src, dst = random.sample(topology.topology.nodes, 2)
        src_ISP = random.choice( topology.topology.nodes[src]["ISPs"])
        dst_ISP = random.choice( topology.topology.nodes[dst]["ISPs"])
        
        bandwidth = random.choice(BANDWIDTH)
        holding_time = random.expovariate(HOLDING_TIME)

        Contador.conta_requisicao_banda(bandwidth)
        Contador.conta_requisicao_classe(class_type)

        return Requisicao( id, src, dst, src_ISP, dst_ISP, bandwidth, class_type, holding_time)

