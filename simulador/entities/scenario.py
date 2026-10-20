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

        self._inicializar_protecao(config)

    def _inicializar_protecao(self, config: ScenarioConfig) -> None:
        """Attach migration-corridor protection if the config enables it."""
        from simulador.coordination.migration_protection import MigrationProtection

        modo = getattr(config, "protecao_modo", None)
        protecao = None
        if modo is not None:
            protecao = MigrationProtection(
                self.lista_de_isps,
                self.topology.topology,
                self.topology.numero_de_slots,
                t_d=self.desastre.start,
                modo=modo,
                escopo=config.protecao_escopo,
                reserva_fracao=config.protecao_reserva_fracao,
                p_max=config.protecao_p_max,
                janela_migracao=config.protecao_janela_migracao,
                caminhos_corredor=config.protecao_caminhos_corredor,
                holding_time=config.holding_time,
                slot_size=config.slot_size,
                margem=getattr(config, "protecao_margem", 1.0),
            )
        # The router reads it from the topology; the coordinator updates it
        self.topology.protecao_migracao = protecao
        if self.cooperation_coordinator is not None:
            self.cooperation_coordinator.protecao = protecao

    def aplicar_modulacao_fixa(self, fator: float | None) -> None:
        """Override the modulation factor of every precomputed path.

        With a fixed factor, the slots a request needs depend only on its
        bandwidth, not on the path length. Paths computed later (e.g. weight
        recalculation during cooperation) use the same factor, because each
        ISP keeps it in ``fator_modulacao_fixo``.

        Args:
            fator: Fixed factor (> 0), or None to restore distance-based
                modulation on every path.
        """
        from simulador.core.path_manager import PathManager

        if fator is not None and fator <= 0:
            raise ValueError(f"fator must be positive or None, got {fator}")

        def _reescrever(caminhos_por_par: dict | None) -> None:
            for destinos in (caminhos_por_par or {}).values():
                for lista in destinos.values():
                    for info in lista:
                        info["fator_de_modulacao"] = (
                            fator
                            if fator is not None
                            else PathManager.calculate_modulation_factor(
                                info["distancia"]
                            )
                        )

        for isp in self.lista_de_isps:
            isp.fator_modulacao_fixo = fator
            _reescrever(isp.caminhos_internos_isp)
            _reescrever(isp.caminhos_internos_isp_durante_desastre)
            _reescrever(isp.weighted_caminhos_internos_isp_durante_desastre)

        _reescrever(getattr(self.topology, "caminhos_mais_curtos_entre_links", None))
        _reescrever(
            getattr(
                self.topology, "caminhos_mais_curtos_entre_links_durante_desastre", None
            )
        )

        if self.config is not None:
            self.config = self.config.copy_with(fator_modulacao_fixo=fator)

    def salva_cenario(self, nome: str) -> None:
        with open(f".cenario/cenarios/{nome}.pkl", "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def carrega_cenario(caminho: str) -> Scenario:
        print(os.getcwd())
        with open(f"{caminho}", "rb") as f:
            return cast("Scenario", pickle.load(f))
