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
    from ISP.ISP import ISP

class GeradorDeTrafego:
    
    @staticmethod
    def gerar_requisicao( topology: 'Topologia', id :int, specific_values :dict = {})-> Requisicao:
        

        if specific_values == {}:
            class_type = choice(CLASS_TYPE, p=CLASS_WEIGHT)
            src, dst = choice(topology.topology.nodes, 2, replace=False)
            src_ISP = choice( topology.topology.nodes[src]["ISPs"])
            dst_ISP = choice( topology.topology.nodes[dst]["ISPs"])
            
            bandwidth = choice(BANDWIDTH)
            holding_time = normal(HOLDING_TIME, HOLDING_TIME*0.1)
            requisicao_de_migracao = False
        else:
            if specific_values.get("src") == None and specific_values.get("dst") == None:
                src, dst = choice(topology.topology.nodes, 2, replace=False)
            elif specific_values.get("src") == None:
                dst = specific_values["dst"]
                src = choice(topology.topology.nodes)
            elif specific_values.get("dst") == None:
                src = specific_values["src"]
                dst = choice(topology.topology.nodes)
            else:
                src = specific_values["src"]
                dst = specific_values["dst"]
                
            if specific_values.get("src_ISP") == None:
                src_ISP = choice( topology.topology.nodes[src]["ISPs"])
            else:
                src_ISP = specific_values["src_ISP"]

            if specific_values.get("dst_ISP") == None:
                dst_ISP = choice( topology.topology.nodes[dst]["ISPs"])
            else:
                dst_ISP = specific_values["dst_ISP"]

            if specific_values.get("bandwidth") == None:
                bandwidth = choice(BANDWIDTH)
            else:
                bandwidth = specific_values["bandwidth"]

            if specific_values.get("holding_time") == None:
                holding_time = normal(HOLDING_TIME, HOLDING_TIME*0.1)
            else:
                holding_time = specific_values["holding_time"]
            
            if specific_values.get("class_type") == None:
                class_type = choice(CLASS_TYPE, p=CLASS_WEIGHT)
            else:
                class_type = specific_values["class_type"]
            
            if specific_values.get("requisicao_de_migracao") == None:
                requisicao_de_migracao = False
            else:
                requisicao_de_migracao = specific_values["requisicao_de_migracao"]
            

        Registrador.conta_requisicao_banda(bandwidth)
        Registrador.conta_requisicao_classe(class_type)

        return Requisicao( str(id), src, dst, src_ISP, dst_ISP, bandwidth, class_type, holding_time, requisicao_de_migracao)

    @staticmethod
    def gerar_lista_de_requisicoes( topology: 'Topologia', numero_de_requisicoes: int,
                                    lista_de_ISPs: list['ISP'], desastre: 'Desastre') -> list[Requisicao]:
        lista_de_requisicoes_nao_processadas: list[Requisicao] = []
        tempo_de_criacao = 0
        for i in range(1, numero_de_requisicoes + 1):
            requisicao = GeradorDeTrafego.gerar_requisicao(topology, i)
            tempo_de_criacao += random.expovariate( REQUISICOES_POR_SEGUNDO )
            requisicao.tempo_criacao = tempo_de_criacao
            lista_de_requisicoes_nao_processadas.append(requisicao)
        
        for isp in lista_de_ISPs:
            lista_de_requisicoes_nao_processadas += GeradorDeTrafego.gerar_lista_de_requisicoes_datacenter( isp.datacenter, desastre, topology, isp.id )

        lista_de_requisicoes_nao_processadas.sort(key=lambda x : x.tempo_criacao)

        return lista_de_requisicoes_nao_processadas

    @staticmethod

    def gerar_lista_de_requisicoes_datacenter( datacenter: 'Datacenter', desastre: 'Desastre', topologia:'Topologia', isp_id: int )-> None:
        tempo_de_criacao = datacenter.tempo_de_reacao
        id = 0
        lista_de_requisicoes = []
        taxa_mensagens =  datacenter.throughput_por_segundo / (sum(BANDWIDTH)/len(BANDWIDTH))
        while tempo_de_criacao < desastre.start:
            
            dict_values = {"src": int(datacenter.source), "dst": int(datacenter.destination), "src_ISP": int(isp_id), "dst_ISP": int(isp_id),
                        "requisicao_de_migracao": True}
            
            requisicao: Requisicao = GeradorDeTrafego.gerar_requisicao(topologia, f"{isp_id}.{id}", dict_values)
            tempo_de_criacao += random.expovariate( taxa_mensagens )
            requisicao.tempo_criacao = tempo_de_criacao
            lista_de_requisicoes.append(requisicao)
            id += 1
        
        #datacenter.lista_de_requisicoes = lista_de_requisicoes
        return lista_de_requisicoes
        