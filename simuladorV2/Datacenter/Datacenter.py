
from Variaveis import *
from numpy.random import choice
from random import expovariate
from Requisicao.Requisicao import Requisicao    
from Roteamento.iRoteamento import iRoteamento
from Logger import Logger
from Registrador import Registrador

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ISP.ISP import ISP
    from Simulador import Simulador

class Datacenter:
    def __init__(self, source :int, destination :int, tempo_de_reacao :float, tamanho_datacenter:float, throughput_por_segundo:float):
        self.source: int = source
        self.destination: int = destination
        self.tempo_de_reacao: float = tempo_de_reacao
        self.tamanho_datacenter: float = tamanho_datacenter
        self.throughput_por_segundo: float = throughput_por_segundo
        self.requisicoes_de_migracao: list[Requisicao] = []
        

    def iniciar_migracao(self, simulador: 'Simulador', isp: 'ISP'):
        simulador.env.process( self.migrar(simulador, isp) )

    def migrar(self, simulador: 'Simulador', isp: 'ISP'):
        Logger.mensagem_inicia_migracao(isp.id, self.source, self.destination, simulador.env.now)
        taxa_mensagens =  self.throughput_por_segundo / (sum(BANDWIDTH)/len(BANDWIDTH))
        inicio_desastre = simulador.desastre.start
        id = 0

        dados_enviados = 0
        while(dados_enviados < self.tamanho_datacenter and simulador.env.now < inicio_desastre):
            yield simulador.env.timeout(expovariate( taxa_mensagens ) )
            
            
            class_type = choice(CLASS_TYPE, p=CLASS_WEIGHT)
            bandwidth = choice(BANDWIDTH)
            holding_time = expovariate(HOLDING_TIME)

            requisicao = Requisicao(f"{isp.id}.{id}" , self.source, self.destination, isp.id, isp.id, bandwidth, class_type, holding_time, True)
            self.requisicoes_de_migracao.append(requisicao)
            id += 1
            roteador :iRoteamento = isp.roteamento
            resultado = roteador.rotear_requisicao(requisicao, simulador.topology)
            if resultado:
                dados_enviados += bandwidth
                Logger.mensagem_acompanha_status_migracao(isp.id, dados_enviados/self.tamanho_datacenter, simulador.env.now)

        Registrador.porcentagem_de_dados_enviados(isp.id, simulador.env.now, dados_enviados/self.tamanho_datacenter)
        Logger.mensagem_finaliza_migracao(isp.id, simulador.env.now, dados_enviados/self.tamanho_datacenter)
        
            
