from copy import deepcopy

import networkx as nx
from simulador.Cenario.Cenario import Cenario
from simulador.Desastre.Desastre import Desastre
from simulador.Desastre.GeradorDeDesastre import GeradorDeDesastre
from simulador.ISP.GeradorDeISPs import GeradorDeISPs
from simulador.ISP.ISP import ISP
from simulador.Requisicao.GeradorDeTrafego import GeradorDeTrafego
from simulador.Requisicao.requisicao import Requisicao
from simulador.Roteamento.IRoteamento import IRoteamento
from simulador.Roteamento.Roteamento import Roteamento
from simulador.Topology.Topologia import Topologia
from simulador.variaveis import NUMERO_DE_CAMINHOS, NUMERO_DE_SLOTS, numero_de_isps


class GeradorDeCenarios:
    @staticmethod
    def gerar_cenario(
        topology: nx.Graph,
        disaster_node: int | None = None,
        retornar_objetos: bool = False,
        retorna_lista_de_requisicoes: bool = False,
        numero_de_requisicoes: int = 0,
        roteamento_de_desastre: "IRoteamento" = Roteamento,
    ) -> tuple[Topologia, list[ISP], Desastre, list[Requisicao]] | Cenario:
        datacenter_destinations = ()
        # garante que os datacenters pra migração não estão no mesmo lugar
        while len(datacenter_destinations) < numero_de_isps:
            desastre = None
            while desastre is None or (
                disaster_node is not None
                and desastre.list_of_dict_node_per_start_time[0]["node"]
                != disaster_node
            ):
                lista_de_isps: list[ISP] = GeradorDeISPs.gerar_lista_isps_aleatorias(
                    topology=topology,
                    numero_de_isps=numero_de_isps,
                    roteamento_de_desastre=roteamento_de_desastre,
                )
                desastre: Desastre = GeradorDeDesastre.generate_disaster(
                    topology, lista_de_isps
                )

            topologia: Topologia = Topologia(
                topology, lista_de_isps, NUMERO_DE_CAMINHOS, NUMERO_DE_SLOTS
            )
            lista_de_requisicoes: list[Requisicao] = None

            for isp in lista_de_isps:
                isp.define_datacenter(desastre, topologia.topology)
            datacenter_destinations = set(
                isp.datacenter.destination for isp in lista_de_isps
            )

        topologia.desastre = desastre
        desastre.seta_links_como_prestes_a_falhar(topologia)
        topologia.inicia_caminhos_mais_curtos_durante_desastre(
            NUMERO_DE_CAMINHOS, desastre.list_of_dict_node_per_start_time[0]["node"]
        )

        if retorna_lista_de_requisicoes:
            lista_de_requisicoes = GeradorDeTrafego.gerar_lista_de_requisicoes(
                topologia, numero_de_requisicoes, lista_de_isps, desastre
            )

        if retornar_objetos:
            return Cenario(topologia, lista_de_isps, desastre, lista_de_requisicoes)
        return topologia, lista_de_isps, desastre, lista_de_requisicoes

    @staticmethod
    def gerar_cenarios(
        topology: nx.Graph,
        disaster_node: int | None = None,
        retorna_lista_de_requisicoes: bool = False,
        numero_de_requisicoes: int = 0,
        lista_de_roteamentos_de_desastre: list["IRoteamento"] | None = None,
    ) -> tuple[Cenario, ...]:
        if lista_de_roteamentos_de_desastre is None:
            lista_de_roteamentos_de_desastre = [Roteamento]

        cenario = GeradorDeCenarios.gerar_cenario(
            topology,
            disaster_node=disaster_node,
            retornar_objetos=True,
            retorna_lista_de_requisicoes=retorna_lista_de_requisicoes,
            numero_de_requisicoes=numero_de_requisicoes,
            roteamento_de_desastre=lista_de_roteamentos_de_desastre.pop(0),
        )
        lista_de_cenarios: list[Cenario] = [cenario]
        for roteamento in lista_de_roteamentos_de_desastre:
            novo_cenario = deepcopy(cenario)
            novo_cenario.troca_roteamento_lista_de_desastre(roteamento)
            lista_de_cenarios.append(novo_cenario)

        return tuple(lista_de_cenarios)
