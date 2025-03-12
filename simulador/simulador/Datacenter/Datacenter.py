
from Variaveis import *
from numpy.random import choice
from random import expovariate
from Requisicao.Requisicao import Requisicao    
from Roteamento.iRoteamento import iRoteamento
from Logger import Logger
from Registrador import Registrador
from Requisicao.GeradorDeTrafego import GeradorDeTrafego
import simpy
from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from ISP.ISP import ISP
    from Simulador import Simulador
    from Topology.Topologia import Topologia


class Datacenter:
    def __init__(self, source :int, destination :int, tempo_de_reacao :float, tamanho_datacenter:float, throughput_por_segundo:float) -> None:
        self.source: int = source
        self.destination: int = destination
        self.tempo_de_reacao: float = tempo_de_reacao
        self.tamanho_datacenter: float = tamanho_datacenter
        self.throughput_por_segundo: float = throughput_por_segundo
        self.lista_de_requisicoes: list[Requisicao] = None

    def iniciar_migracao(self, simulador: 'Simulador', isp: 'ISP') -> None:
        simulador.env.process( self.__migrar(simulador, isp) )

    def __migrar(self, simulador: 'Simulador', isp: 'ISP') -> Generator:
        Logger.mensagem_inicia_migracao(isp.id, self.source, self.destination, simulador.env.now)
        taxa_mensagens =  self.throughput_por_segundo / (sum(BANDWIDTH)/len(BANDWIDTH))
        inicio_desastre = simulador.desastre.start

        id = 0
        dados_enviados = 0
        while(dados_enviados < self.tamanho_datacenter and simulador.env.now < inicio_desastre):
            
            requisicao = self.pega_requisicao(id, simulador, isp.id)
            Registrador.adiciona_requisicao(requisicao)
            bandwidth = requisicao.bandwidth
            id += 1
            yield from self.espera_requisicao(requisicao, simulador.env, taxa_mensagens)

            roteador :iRoteamento = isp.roteamento_atual
            resultado = roteador.rotear_requisicao(requisicao, simulador.topology, simulador.env)
            if resultado:
                dados_enviados += bandwidth
                Logger.mensagem_acompanha_status_migracao(isp.id, dados_enviados/self.tamanho_datacenter, simulador.env.now)

        Registrador.porcentagem_de_dados_enviados(isp.id, simulador.env.now, dados_enviados/self.tamanho_datacenter)
        Logger.mensagem_finaliza_migracao(isp.id, simulador.env.now, dados_enviados/self.tamanho_datacenter)

    def gerar_requisicao(self, id:int, topologia: 'Topologia', isp_id: int) -> Requisicao:
        

            dict_values = {"src": int(self.source), "dst": int(self.destination), "src_ISP": int(isp_id), "dst_ISP": int(isp_id),
                        "requisicao_de_migracao": True}
         
            requisicao: Requisicao = GeradorDeTrafego.gerar_requisicao(topologia, f"{isp_id}.{id}", dict_values)

            return requisicao
    
    def pega_requisicao(self, id:int, topologia: 'Topologia', isp_id: int) -> Requisicao:
         
        if self.lista_de_requisicoes:
            return self.lista_de_requisicoes.pop(0)
        else:
            return self.gerar_requisicao(id, topologia, isp_id)
         
    def espera_requisicao(self, requisicao: Requisicao, env: simpy.Environment, taxa_mensagens: float) -> Generator:
        if self.lista_de_requisicoes:
            tempo_a_esperar = requisicao.tempo_criacao - env.now
            yield env.timeout( tempo_a_esperar)
        else:
            yield env.timeout(expovariate( taxa_mensagens ) )