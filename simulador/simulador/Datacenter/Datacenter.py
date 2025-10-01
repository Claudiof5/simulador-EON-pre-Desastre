from collections.abc import Generator
from random import expovariate
from typing import TYPE_CHECKING

import simpy
from logger import Logger
from registrador import Registrador
from Requisicao.GeradorDeTrafego import GeradorDeTrafego
from Requisicao.requisicao import Requisicao
from Roteamento.IRoteamento import IRoteamento
from variaveis import BANDWIDTH

if TYPE_CHECKING:
    from ISP.ISP import ISP
    from Topology.Topologia import Topologia

    from simulador import Simulador


class Datacenter:
    def __init__(
        self,
        source: int,
        destination: int,
        tempo_de_reacao: float,
        tamanho_datacenter: float,
        throughput_por_segundo: float,
    ) -> None:
        """Initialize the Datacenter class.

        Args:
            source: The source of the datacenter
            destination: The destination of the datacenter
            tempo_de_reacao: The reaction time of the datacenter
            tamanho_datacenter: The size of the datacenter
            throughput_por_segundo: The throughput of the datacenter
        """
        self.source: int = source
        self.destination: int = destination
        self.tempo_de_reacao: float = tempo_de_reacao
        self.tamanho_datacenter: float = tamanho_datacenter
        self.throughput_por_segundo: float = throughput_por_segundo
        self.lista_de_requisicoes: list[Requisicao] = None

    def iniciar_migracao(self, simulador: "Simulador", isp: "ISP") -> None:
        simulador.env.process(self.__migrar(simulador, isp))

    def __migrar(self, simulador: "Simulador", isp: "ISP") -> Generator:
        Logger.mensagem_inicia_migracao(
            isp.id, self.source, self.destination, simulador.env.now
        )
        taxa_mensagens = self.throughput_por_segundo / (sum(BANDWIDTH) / len(BANDWIDTH))
        inicio_desastre = simulador.desastre.start

        req_id = 0
        dados_enviados = 0
        while (
            dados_enviados < self.tamanho_datacenter
            and simulador.env.now < inicio_desastre
        ):
            requisicao = self.pega_requisicao(req_id, simulador, isp.id)
            Registrador.adiciona_requisicao(requisicao)
            bandwidth = requisicao.bandwidth
            req_id += 1
            yield from self.espera_requisicao(requisicao, simulador.env, taxa_mensagens)

            roteador: IRoteamento = isp.roteamento_atual
            resultado = roteador.rotear_requisicao(
                requisicao, simulador.topology, simulador.env
            )
            if resultado:
                dados_enviados += bandwidth
                Logger.mensagem_acompanha_status_migracao(
                    isp.id, dados_enviados / self.tamanho_datacenter, simulador.env.now
                )

        Registrador.porcentagem_de_dados_enviados(
            isp.id, simulador.env.now, dados_enviados / self.tamanho_datacenter
        )
        Logger.mensagem_finaliza_migracao(
            isp.id, simulador.env.now, dados_enviados / self.tamanho_datacenter
        )

    def gerar_requisicao(
        self, req_id: int, topologia: "Topologia", isp_id: int
    ) -> Requisicao:
        dict_values = {
            "src": int(self.source),
            "dst": int(self.destination),
            "src_isp": int(isp_id),
            "dst_isp": int(isp_id),
            "requisicao_de_migracao": True,
        }

        requisicao: Requisicao = GeradorDeTrafego.gerar_requisicao(
            topologia, f"{isp_id}.{req_id}", dict_values
        )

        return requisicao

    def pega_requisicao(
        self, req_id: int, topologia: "Topologia", isp_id: int
    ) -> Requisicao:
        if self.lista_de_requisicoes:
            return self.lista_de_requisicoes.pop(0)
        return self.gerar_requisicao(req_id, topologia, isp_id)

    def espera_requisicao(
        self, requisicao: Requisicao, env: simpy.Environment, taxa_mensagens: float
    ) -> Generator:
        if self.lista_de_requisicoes:
            tempo_a_esperar = requisicao.tempo_criacao - env.now
            yield env.timeout(tempo_a_esperar)
        else:
            yield env.timeout(expovariate(taxa_mensagens))
