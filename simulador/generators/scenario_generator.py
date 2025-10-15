from __future__ import annotations

from copy import deepcopy
from typing import cast

import networkx as nx

from simulador import Topology
from simulador.config.settings import (
    NUMERO_DE_CAMINHOS,
    NUMERO_DE_SLOTS,
    numero_de_isps,
)
from simulador.core.request import Request
from simulador.entities.disaster import Disaster
from simulador.entities.isp import ISP
from simulador.entities.scenario import Scenario
from simulador.generators.disaster_generator import DisasterGenerator
from simulador.generators.isp_generator import ISPGenerator
from simulador.generators.traffic_generator import TrafficGenerator
from simulador.routing.base import RoutingBase
from simulador.routing.first_fit import FirstFit


class ScenarioGenerator:
    @staticmethod
    def gerar_cenario(
        topology: nx.Graph,
        disaster_node: int | None = None,
        retornar_objetos: bool = False,
        retorna_lista_de_requisicoes: bool = False,
        numero_de_requisicoes: int = 0,
        roteamento_de_desastre: type[RoutingBase] = FirstFit,
    ) -> tuple[Topology, list[ISP], Disaster, list[Request]] | Scenario:
        datacenter_destinations: set[int] = set()
        while len(datacenter_destinations) < numero_de_isps:
            desastre_temp: Disaster | None = None
            while desastre_temp is None or (
                disaster_node is not None
                and desastre_temp.list_of_dict_node_per_start_time[0]["node"]
                != disaster_node
            ):
                lista_de_isps: list[ISP] = ISPGenerator.gerar_lista_isps_aleatorias(
                    topology=topology,
                    numero_de_isps=numero_de_isps,
                    roteamento_de_desastre=roteamento_de_desastre,
                )
                desastre_temp = DisasterGenerator.generate_disaster(
                    topology, lista_de_isps
                )

            desastre: Disaster = desastre_temp

            topologia: Topology = Topology(
                topology, lista_de_isps, NUMERO_DE_CAMINHOS, NUMERO_DE_SLOTS
            )
            lista_de_requisicoes: list[Request] | None = None

            for isp in lista_de_isps:
                isp.define_datacenter(desastre, topologia.topology)
            datacenter_destinations = set(
                isp.datacenter.destination
                for isp in lista_de_isps
                if isp.datacenter is not None
            )

        topologia.desastre = desastre
        desastre.seta_links_como_prestes_a_falhar(topologia)
        topologia.inicia_caminhos_mais_curtos_durante_desastre(
            NUMERO_DE_CAMINHOS, desastre.list_of_dict_node_per_start_time[0]["node"]
        )

        if retorna_lista_de_requisicoes:
            lista_de_requisicoes = TrafficGenerator.gerar_lista_de_requisicoes(
                topologia, numero_de_requisicoes, lista_de_isps, desastre
            )

        if retornar_objetos:
            return Scenario(
                topologia, lista_de_isps, desastre, lista_de_requisicoes or []
            )
        return topologia, lista_de_isps, desastre, lista_de_requisicoes or []

    @staticmethod
    def gerar_cenarios(
        topology: nx.Graph,
        disaster_node: int | None = None,
        retorna_lista_de_requisicoes: bool = False,
        numero_de_requisicoes: int = 0,
        lista_de_roteamentos_de_desastre: list[type[RoutingBase]] | None = None,
    ) -> tuple[Scenario, ...]:
        if lista_de_roteamentos_de_desastre is None:
            lista_de_roteamentos_de_desastre = [FirstFit]

        cenario_result = ScenarioGenerator.gerar_cenario(
            topology,
            disaster_node=disaster_node,
            retornar_objetos=True,
            retorna_lista_de_requisicoes=retorna_lista_de_requisicoes,
            numero_de_requisicoes=numero_de_requisicoes,
            roteamento_de_desastre=lista_de_roteamentos_de_desastre.pop(0),
        )
        cenario: Scenario = cast(Scenario, cenario_result)

        lista_de_cenarios: list[Scenario] = [cenario]
        for roteamento in lista_de_roteamentos_de_desastre:
            novo_cenario = deepcopy(cenario)
            novo_cenario.troca_roteamento_lista_de_desastre(roteamento)
            lista_de_cenarios.append(novo_cenario)

        return tuple(lista_de_cenarios)
