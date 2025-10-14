import os
import pickle
from copy import deepcopy
from typing import cast

from simulador.core.request import Request
from simulador.core.topology import Topology
from simulador.entities.disaster import Disaster
from simulador.entities.isp import ISP
from simulador.routing.base import RoutingBase


class Scenario:
    def __init__(
        self,
        topology: Topology,
        lista_de_isps: list[ISP],
        desastre: Disaster,
        lista_de_requisicoes: list[Request] | None = None,
    ) -> None:
        """Initialize the Scenario class.

        Args:
            topology: The topology of the scenario
            lista_de_isps: The list of ISPs in the scenario
            desastre: The disaster of the scenario
            lista_de_requisicoes: The list of requests in the scenario
        """
        self.topology: Topology = topology
        self.lista_de_isps: list[ISP] = lista_de_isps
        self.desastre: Disaster = desastre
        self.lista_de_requisicoes: list[Request] | None = lista_de_requisicoes

    def retorna_atributos(
        self,
    ) -> tuple[Topology, list[ISP], Disaster, list[Request] | None]:
        return deepcopy(
            (
                self.topology,
                self.lista_de_isps,
                self.desastre,
                self.lista_de_requisicoes,
            )
        )

    def imprime_atributos(self) -> None:
        self.topology.imprime_topologia()
        print("")
        self.desastre.imprime_desastre()
        print("")
        for isp in self.lista_de_isps:
            isp.imprime_isp()
            print("")

    def troca_roteamento_lista_de_desastre(self, roteamento: type[RoutingBase]) -> None:
        for isp in self.lista_de_isps:
            isp.troca_roteamento_desastre(roteamento)

    def salva_cenario(self, nome: str) -> None:
        with open(f".cenario/cenarios/{nome}.pkl", "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def carrega_cenario(caminho: str) -> "Scenario":
        print(os.getcwd())
        with open(f"{caminho}", "rb") as f:
            return cast("Scenario", pickle.load(f))
