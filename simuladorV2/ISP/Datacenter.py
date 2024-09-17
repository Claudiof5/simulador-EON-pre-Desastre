from Simulador import Simulador
from Variaveis import *
from ISP.ISP import ISP
import random
from Requisicao.Requisicao import Requisicao    
from Roteamento.iRoteamento import iRoteamento

class Datacenter:
    def __init__(self, source, destination, tempo_de_reacao, tamanho_datacenter, throughput_por_segundo):
        self.source = source
        self.destination = destination
        self.tempo_de_reacao = tempo_de_reacao
        self.tamanho_datacenter = tamanho_datacenter
        self.throughput_por_segundo = throughput_por_segundo
        self.requisicoes_de_migracao :list[Requisicao]= []

    def iniciar_migracao(self, simulador: Simulador):
        simulador.env.process(self.migrar(simulador))

    def migrar(self, simulador: Simulador, isp: ISP):
        
        taxa_mensagens =  self.throughput_por_segundo / BANDWIDTH[-1]
        migracao_restante = self.tamanho_datacenter

        id = 0
        bandwidth = BANDWIDTH[-1]
        while(migracao_restante > 0):
            yield simulador.env.timeout(random.expovariate( taxa_mensagens ) )
            
            class_type = random.choice(CLASS_TYPE, p=CLASS_WEIGHT)
            holding_time = random.expovariate(HOLDING_TIME)

            requisicao = Requisicao(id , self.source, self.destination, isp.id, isp.id, bandwidth, class_type, holding_time)
            self.requisicoes_de_migracao.append(requisicao)
            id += 1
            roteador :iRoteamento = isp.roteamento
            resultado = roteador.rotear_requisicao(simulador, requisicao, simulador.topology)
            if resultado:
                migracao_restante -= bandwidth
            
