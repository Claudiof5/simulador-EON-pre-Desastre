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
                feedback_lambda=getattr(config, "protecao_feedback_lambda", 1.0),
                feedback_kappa=getattr(config, "protecao_feedback_kappa", 0.5),
                feedback_intervalo=getattr(config, "protecao_feedback_intervalo", 1.0),
                reserva_max=getattr(config, "protecao_reserva_max", None),
                agregacao=getattr(config, "protecao_agregacao", "soma"),
                divisao_uso=getattr(config, "protecao_divisao_uso", False),
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

    def redefinir_destinos_migracao(self, criterio: str) -> dict[int, tuple[int, int]]:
        """Re-choose each ISP's migration destination and retarget its requests.

        Traffic is pre-generated, so only the destination of the existing
        migration requests changes: volume, bit rates and timing stay the same.

        Args:
            criterio: "saltos" (farthest in hops) or "distancia" (farthest in km)

        Returns:
            {isp_id: (old destination, new destination)}
        """
        from simulador.generators.datacenter_generator import DatacenterGenerator

        mudancas: dict[int, tuple[int, int]] = {}
        novo_destino: dict[int, int] = {}
        for isp in self.lista_de_isps:
            dc = isp.datacenter
            if dc is None:
                continue
            destino = DatacenterGenerator.destino_mais_distante(
                self.topology.topology, dc.source, isp.nodes, criterio
            )
            mudancas[isp.isp_id] = (int(dc.destination), destino)
            dc.destination = destino
            novo_destino[isp.isp_id] = destino

        for req in self.lista_de_requisicoes or []:
            if req.requisicao_de_migracao and req.src_isp_index in novo_destino:
                req.dst = novo_destino[req.src_isp_index]

        if self.config is not None:
            self.config = self.config.copy_with(destino_migracao=criterio)
        return mudancas

    def diversificar_saidas_migracao(self, n: int = 3) -> dict[int, int]:
        """Reorder migration paths so the first ``n`` use different exit links.

        For each provider, the candidate paths from its datacenter to its
        destination are re-ranked: the shortest path first, then the shortest
        path through each exit link (first link) not used yet, up to ``n``
        paths; the remaining paths follow in their original order. Providers
        with fewer exits get as many distinct exits as they have. The router
        tries migration paths in this order and the corridor uses the first
        ones, so both follow the new order.

        Returns:
            {isp_id: number of distinct exits among its first n paths}
        """
        resultado = {}
        for isp in self.lista_de_isps:
            dc = isp.datacenter
            if dc is None:
                continue
            for atributo in (
                "weighted_caminhos_internos_isp_durante_desastre",
                "caminhos_internos_isp_durante_desastre",
            ):
                tabela = getattr(isp, atributo, None) or {}
                caminhos = tabela.get(dc.source, {}).get(dc.destination)
                if not caminhos:
                    continue
                escolhidos, saidas = [], set()
                for c in caminhos:
                    saida = c["caminho"][1] if len(c["caminho"]) > 1 else None
                    if len(escolhidos) < n and saida not in saidas:
                        escolhidos.append(c)
                        saidas.add(saida)
                resto = [c for c in caminhos if all(c is not e for e in escolhidos)]
                tabela[dc.source][dc.destination] = escolhidos + resto
                resultado[isp.isp_id] = len(saidas)
        return resultado

    def recortar_janela(self) -> tuple[int, int]:
        """Drop the requests created at or after the failure (t_d).

        Metrics only count requests created before t_d, and requests created
        later cannot change anything that happened before, so the measured
        results are identical to a full run. The simulation still starts at the
        beginning, so the network state at each discovery time is the same.

        Returns:
            (requests before, requests after)
        """
        reqs = self.lista_de_requisicoes or []
        fim = self.desastre.start
        mantidas = [
            r for r in reqs if r.tempo_criacao is not None and r.tempo_criacao < fim
        ]
        self.lista_de_requisicoes = mantidas
        return len(reqs), len(mantidas)

    def aviso_compartilhado(self, semente: int = 0) -> int:
        """The first ISP to discover the threat warns the others.

        Every ISP reacts at tau_min, the earliest discovery time. Each ISP's
        migration stream is extended back to tau_min with the same rate,
        bit-rate and holding-time distributions as the stored one (drawn with a
        seeded generator), so its volume D_i is unchanged and only the window
        grows. Nothing changes before tau_min, so shared prefixes still apply.

        Returns:
            Number of migration requests added.
        """
        import numpy as np

        from simulador.config.settings import (
            BANDWIDTH,
            CLASS_TYPE,
            CLASS_WEIGHT,
            HOLDING_TIME,
            SLOT_SIZE,
        )
        from simulador.generators.traffic_generator import TrafficGenerator

        isps = [isp for isp in self.lista_de_isps if isp.datacenter is not None]
        tau_min = min(isp.datacenter.tempo_de_reacao for isp in isps)
        rng = np.random.default_rng(semente)
        reqs = self.lista_de_requisicoes or []
        proximo = max((int(r.req_id) for r in reqs), default=0) + 1
        slots_por_requisicao = (sum(BANDWIDTH) / len(BANDWIDTH)) / SLOT_SIZE
        novos = []
        for isp in sorted(isps, key=lambda i: i.isp_id):
            dc = isp.datacenter
            taxa = dc.throughput_por_segundo / slots_por_requisicao
            t = tau_min
            while True:
                t += rng.exponential(1 / taxa)
                if t >= dc.tempo_de_reacao:
                    break
                r = TrafficGenerator.gerar_requisicao(
                    self.topology,
                    str(proximo),
                    {
                        "src": int(dc.source),
                        "dst": int(dc.destination),
                        "src_isp_index": int(isp.isp_id),
                        "dst_isp_index": int(isp.isp_id),
                        "requisicao_de_migracao": True,
                        "bandwidth": int(rng.choice(BANDWIDTH)),
                        "holding_time": float(rng.normal(HOLDING_TIME, HOLDING_TIME * 0.1)),
                        "class_type": int(rng.choice(CLASS_TYPE, p=CLASS_WEIGHT)),
                    },
                )
                r.src, r.dst = int(dc.source), int(dc.destination)
                r.tempo_criacao = t
                novos.append(r)
                proximo += 1
            dc.tempo_de_reacao = tau_min
        self.lista_de_requisicoes = sorted(reqs + novos, key=lambda r: r.tempo_criacao)
        return len(novos)

    def reduzir_carga(self, fracao: float) -> tuple[int, int]:
        """Keep only a fraction of the background requests (independent thinning).

        A background request is kept when a pseudo-random number derived from
        its req_id is below ``fracao``, so thinning a Poisson stream gives a
        Poisson stream of rate ``fracao`` times the original, every scenario
        variant drops the same requests, and a smaller fraction keeps a subset
        of the requests kept by a larger one. Migration requests are untouched.

        Returns:
            (background requests before, background requests kept)
        """
        import hashlib

        if not 0 < fracao <= 1:
            raise ValueError(f"fracao must be in (0, 1], got {fracao}")

        def sorteio(req_id: str) -> float:
            h = hashlib.blake2b(str(req_id).encode(), digest_size=8).digest()
            return int.from_bytes(h, "big") / 2**64

        reqs = self.lista_de_requisicoes or []
        fundo = sum(not r.requisicao_de_migracao for r in reqs)
        self.lista_de_requisicoes = [
            r for r in reqs if r.requisicao_de_migracao or sorteio(r.req_id) < fracao
        ]
        mantidas = sum(not r.requisicao_de_migracao for r in self.lista_de_requisicoes)
        return fundo, mantidas

    def salva_cenario(self, nome: str) -> None:
        with open(f".cenario/cenarios/{nome}.pkl", "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def carrega_cenario(caminho: str) -> Scenario:
        print(os.getcwd())
        with open(f"{caminho}", "rb") as f:
            return cast("Scenario", pickle.load(f))
