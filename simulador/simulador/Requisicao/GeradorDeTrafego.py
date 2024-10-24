from numpy.random import choice, normal
from Registrador import Registrador
from Variaveis import *
from Requisicao.Requisicao import Requisicao
from typing import TYPE_CHECKING
import random
if TYPE_CHECKING:
    from Topology.Topologia import Topologia
    from Datacenter.Datacenter import Datacenter
    from Desastre.Desastre import Desastre
    from Simulador import Simulador

class GeradorDeTrafego:
    
    @staticmethod
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

    @staticmethod
    def gerar_lista_de_requisicoes( topology: 'Topologia', numero_de_requisicoes: int) -> list[Requisicao]:
        lista_de_requisicoes_nao_processadas: list[Requisicao] = []
        tempo_de_criacao = 0
        for i in range(1, numero_de_requisicoes + 1):
            requisicao = GeradorDeTrafego.gerar_requisicao(topology, i)
            tempo_de_criacao += random.expovariate( REQUISICOES_POR_SEGUNDO )
            requisicao.tempo_criacao = tempo_de_criacao
            lista_de_requisicoes_nao_processadas.append(requisicao)
        return lista_de_requisicoes_nao_processadas

    @staticmethod

    def gerar_lista_de_requisicoes_datacenter( datacenter: 'Datacenter', desastre: 'Desastre', topologia:'Topologia', isp_id: int )-> None:
        tempo_de_criacao = datacenter.tempo_de_reacao
        id = 0
        lista_de_requisicoes = []
        taxa_mensagens =  datacenter.throughput_por_segundo / (sum(BANDWIDTH)/len(BANDWIDTH))
        while tempo_de_criacao < desastre.start:

            requisicao = datacenter.gerar_requisicao(id, topologia, isp_id, )
            tempo_de_criacao += random.expovariate( taxa_mensagens )
            requisicao.tempo_criacao = tempo_de_criacao
            lista_de_requisicoes.append(requisicao)
            id += 1
        datacenter.lista_de_requisicoes = lista_de_requisicoes
        