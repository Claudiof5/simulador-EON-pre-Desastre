from __future__ import annotations

import os
import pickle
from copy import deepcopy
from typing import TYPE_CHECKING, cast

from simulador.core.request import Request
from simulador.core.topology import Topology
from simulador.entities.disaster import Disaster
from simulador.entities.isp import ISP
from simulador.routing.base import RoutingBase

if TYPE_CHECKING:
    from collections.abc import Iterable

    from simulador.config.simulation_settings import ScenarioConfig
    from simulador.coordination.cooperation_coordinator import CooperationCoordinator


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
        self.config = None  # Will be set by ScenarioGenerator if config was provided
        self.cooperation_coordinator: CooperationCoordinator | None = (
            None  # Set by initialize_cooperation
        )

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

    def initialize_cooperation(
        self,
        disaster_node: int,
        config: ScenarioConfig,
        cooperating_isps: Iterable[int] | None = None,
    ) -> None:
        """Initialize cooperation coordinator and link to ISPs.

        This sets up the cooperation mechanism where ISPs gradually share
        information as they react to the disaster. Each ISP starts with
        isolated weights (own data only) and incorporates cooperating ISPs'
        data as they join the cooperation network.

        Args:
            disaster_node: Node affected by disaster
            config: Scenario configuration with weight parameters (α, β, γ)
            cooperating_isps: ISP IDs in the cooperating set K. None falls back
                to ``config.cooperating_isps``; if that is None too, every ISP
                cooperates.
        """
        from simulador.coordination.cooperation_coordinator import (
            CooperationCoordinator,
        )

        if cooperating_isps is None:
            # getattr: configs pickled before this field existed lack it
            cooperating_isps = getattr(config, "cooperating_isps", None)
        allowed = None if cooperating_isps is None else set(cooperating_isps)

        self.cooperation_coordinator = CooperationCoordinator(
            self.lista_de_isps,
            self.topology.topology,
            disaster_node,
            config,
            allowed_isps=allowed,
        )

        # Link coordinator to all ISPs so they can register when they start cooperating
        for isp in self.lista_de_isps:
            isp.cooperation_coordinator = self.cooperation_coordinator

    def salva_cenario(self, nome: str) -> None:
        with open(f".cenario/cenarios/{nome}.pkl", "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def carrega_cenario(caminho: str) -> Scenario:
        print(os.getcwd())
        with open(f"{caminho}", "rb") as f:
            return cast("Scenario", pickle.load(f))
