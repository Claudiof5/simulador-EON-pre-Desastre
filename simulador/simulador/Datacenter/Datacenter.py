
from Variaveis import *
from numpy.random import choice
from random import expovariate
from Requisicao.Requisicao import Requisicao    
from Roteamento.iRoteamento import iRoteamento
from Logger import Logger
from Registrador import Registrador
from Requisicao.GeradorDeTrafego import GeradorDeTrafego

from typing import TYPE_CHECKING, Generator
if TYPE_CHECKING:
    from ISP.ISP import ISP
    from Simulador import Simulador

class Datacenter:
    def __init__(self, source :int, destination :int, tempo_de_reacao :float, tamanho_datacenter:float, throughput_por_segundo:float) -> None:
        self.source: int = source
        self.destination: int = destination
        self.tempo_de_reacao: float = tempo_de_reacao
        self.tamanho_datacenter: float = tamanho_datacenter
        self.throughput_por_segundo: float = throughput_por_segundo

    def iniciar_migracao(self, simulador: 'Simulador', isp: 'ISP') -> None:
        simulador.env.process( self.__migrar(simulador, isp) )

    def __migrar(self, simulador: 'Simulador', isp: 'ISP') -> Generator:
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
            dict_values = {"src": self.source, "dst": self.destination, "src_ISP": isp.id, "dst_ISP": isp.id, "bandwidth": bandwidth,
                            "holding_time": holding_time, "class_type": class_type, "requisicao_de_migracao": True}
         
            requisicao: Requisicao = GeradorDeTrafego.gerar_requisicao(simulador.topology, f"{isp.id}.{id}", dict_values)
            requisicao.requisicao_de_migracao == True
            Registrador.adiciona_requisicao(requisicao)

            id += 1
            roteador :iRoteamento = isp.roteamento_atual
            resultado = roteador.rotear_requisicao(requisicao, simulador.topology, simulador.env)
            if resultado:
                dados_enviados += bandwidth
                Logger.mensagem_acompanha_status_migracao(isp.id, dados_enviados/self.tamanho_datacenter, simulador.env.now)

        Registrador.porcentagem_de_dados_enviados(isp.id, simulador.env.now, dados_enviados/self.tamanho_datacenter)
        Logger.mensagem_finaliza_migracao(isp.id, simulador.env.now, dados_enviados/self.tamanho_datacenter)
        
            
