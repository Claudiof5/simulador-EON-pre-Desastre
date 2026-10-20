"""Protect migration corridors on links used only by cooperating ISPs.

Knowledge model (validation step): a mediator discloses, for each link e, how
many ISPs use it, sigma(e). Cooperating ISPs share their overlays, so for a link
they can count how many of *them* use it. If that count equals sigma(e), no
non-cooperating ISP uses the link and it is exclusive to the cooperating set.

On links that are exclusive AND lie on a cooperating member's migration
corridor (its first candidate migration paths), background (non-migration)
traffic is restricted during the warning window [tau_i, t_d):

- ``reserva``: background requests may not use the top ``reserva_fracao`` of the
  slots on those links, so the space stays free for migration.
- ``adaptativo``: a background request is kept off each such link with
  probability p = min(p_max, recent migration blocking rate of the link's
  owners). The request may still use a detour that avoids the link.
- ``reserva_demanda``: like ``reserva``, but each link reserves exactly the
  slots its owners still need to finish migrating before t_d. For owner o at
  time t: slots = ceil(margem * h * (D_o - M_o(t)) / ((t_d - t) * f_o * slot)),
  where h is the holding time, f_o the modulation factor of o's main path and
  M_o(t) the migration bandwidth o already had accepted. Summed over the
  link's owners and capped at the link size; it shrinks to 0 once o finishes.
  Use with ``caminhos_corredor = 1`` to reserve only on the main path.

Scope ``isolado`` is the control: every ISP that reacted protects the links of
its own corridor that only it uses (sigma(e) == 1), whether it cooperates or
not. It separates "the mediator's count helps" from "cooperation helps".
"""

from __future__ import annotations

import math
import random
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import networkx as nx

    from simulador.entities.isp import ISP

MODOS = ("reserva", "adaptativo", "reserva_demanda")
ESCOPOS = ("cooperacao", "isolado")

Link = frozenset


def _link(u: int, v: int) -> Link:
    return frozenset((int(u), int(v)))


class MigrationProtection:
    """Tracks protected links and restricts background traffic on them."""

    def __init__(
        self,
        lista_de_isps: list[ISP],
        topology: nx.Graph,
        numero_de_slots: int,
        t_d: float,
        modo: str,
        escopo: str = "cooperacao",
        reserva_fracao: float = 0.25,
        p_max: float = 0.9,
        janela_migracao: int = 100,
        caminhos_corredor: int = 3,
        seed: int = 0,
        holding_time: float = 1.0,
        slot_size: float = 12.5,
        margem: float = 1.0,
    ) -> None:
        if modo not in MODOS:
            raise ValueError(f"modo must be one of {MODOS}, got {modo!r}")
        if escopo not in ESCOPOS:
            raise ValueError(f"escopo must be one of {ESCOPOS}, got {escopo!r}")
        self.lista_de_isps = lista_de_isps
        self.topology = topology
        self.numero_de_slots = numero_de_slots
        self.t_d = t_d
        self.modo = modo
        self.escopo = escopo
        self.reserva_fracao = reserva_fracao
        self.p_max = p_max
        self.caminhos_corredor = caminhos_corredor
        self.rng = random.Random(seed)
        self.holding_time = holding_time
        self.slot_size = slot_size
        self.margem = margem
        self._por_id = {isp.isp_id: isp for isp in lista_de_isps}
        self._migrado: dict[int, float] = {isp.isp_id: 0.0 for isp in lista_de_isps}
        self._fator_principal: dict[int, float] = {}

        # sigma(e): what the mediator discloses (a count, not identities)
        self.sigma: dict[Link, int] = {}
        self._usuarios: dict[Link, set[int]] = {}
        for u, v, dados in topology.edges(data=True):
            usuarios = set(dados.get("ISPs", []))
            self._usuarios[_link(u, v)] = usuarios
            self.sigma[_link(u, v)] = len(usuarios)

        self.reagiram: set[int] = set()
        self.protegidos: dict[Link, set[int]] = {}  # link -> owner ISPs
        self._migracoes: dict[int, deque[bool]] = {
            isp.isp_id: deque(maxlen=janela_migracao) for isp in lista_de_isps
        }

        # Diagnostics
        self.max_links_protegidos = 0
        self.normais_restringidas = 0  # background requests that hit a restriction
        self._soma_reserva = 0.0  # slots reserved, summed over checked requests
        self._n_reserva = 0

    # ------------------------------------------------------------------ state
    def corredor(self, isp: ISP) -> set[Link]:
        """Links of the ISP's first candidate migration paths (current weights)."""
        dc = isp.datacenter
        if dc is None:
            return set()
        caminhos = isp.weighted_caminhos_internos_isp_durante_desastre.get(
            dc.source, {}
        ).get(dc.destination, [])[: self.caminhos_corredor]
        if caminhos:
            self._fator_principal[isp.isp_id] = caminhos[0].get(
                "fator_de_modulacao", 1.0
            )
        return {
            _link(c["caminho"][i], c["caminho"][i + 1])
            for c in caminhos
            for i in range(len(c["caminho"]) - 1)
        }

    def exclusivo(self, link: Link, grupo: set[int]) -> bool:
        """True if the group's own count on the link equals sigma(link)."""
        conhecidos = len(self._usuarios.get(link, set()) & grupo)
        return conhecidos > 0 and conhecidos == self.sigma.get(link, 0)

    def atualizar(self, isp_id: int, cooperantes: set[int]) -> None:
        """Recompute protected links after an ISP reacts.

        Args:
            isp_id: ISP that just reached its reaction time
            cooperantes: ISPs currently cooperating (after this reaction)
        """
        self.reagiram.add(isp_id)
        por_id = {isp.isp_id: isp for isp in self.lista_de_isps}
        if self.escopo == "cooperacao":
            grupos = [(i, set(cooperantes)) for i in cooperantes]
        else:
            grupos = [(i, {i}) for i in self.reagiram]

        protegidos: dict[Link, set[int]] = {}
        for dono, grupo in grupos:
            for link in self.corredor(por_id[dono]):
                if self.exclusivo(link, grupo):
                    protegidos.setdefault(link, set()).add(dono)
        self.protegidos = protegidos
        self.max_links_protegidos = max(self.max_links_protegidos, len(protegidos))

    def registra_migracao(
        self, isp_id: int, bloqueada: bool, banda: float = 0.0
    ) -> None:
        if isp_id in self._migracoes:
            self._migracoes[isp_id].append(bool(bloqueada))
        if not bloqueada and isp_id in self._migrado:
            self._migrado[isp_id] += banda

    def slots_necessarios(self, isp_id: int, agora: float) -> int:
        """Slots owner needs on its main path to finish migrating by t_d."""
        dc = self._por_id[isp_id].datacenter
        if dc is None:
            return 0
        restante = dc.tamanho_datacenter - self._migrado.get(isp_id, 0.0)
        if restante <= 0:
            return 0
        tempo = max(self.t_d - agora, 1e-6)
        fator = self._fator_principal.get(isp_id, 1.0)
        taxa = restante / tempo  # accepted bandwidth per second still needed
        return math.ceil(
            self.margem * taxa * self.holding_time / (fator * self.slot_size)
        )

    def reserva_link(self, link: Link, agora: float) -> int:
        """Slots reserved on a protected link at time ``agora``."""
        if self.modo == "reserva":
            return int(round(self.reserva_fracao * self.numero_de_slots))
        total = sum(
            self.slots_necessarios(dono, agora)
            for dono in self.protegidos.get(link, ())
        )
        return min(self.numero_de_slots, total)

    @property
    def reserva_media_slots(self) -> float | None:
        """Mean slots reserved on the protected links background requests hit."""
        return self._soma_reserva / self._n_reserva if self._n_reserva else None

    def _p_bloqueio(self, link: Link) -> float:
        taxas = [
            sum(h) / len(h)
            for dono in self.protegidos.get(link, ())
            if (h := self._migracoes.get(dono))
        ]
        return min(self.p_max, max(taxas)) if taxas else 0.0

    # ---------------------------------------------------------------- routing
    def ativa(self, agora: float) -> bool:
        return bool(self.protegidos) and agora < self.t_d

    def aplicar(
        self, requisicao, datapaths: list[dict], agora: float
    ) -> tuple[list[dict], bool]:
        """Apply the restriction to a background request's candidate paths.

        Returns the (possibly modified) datapaths and whether any still fits.
        Migration requests and requests outside the window pass unchanged.
        """
        habil = any(
            d["maior_janela_contigua_continua"] >= d["numero_slots_necessarios"]
            for d in datapaths
        )
        if requisicao.requisicao_de_migracao or not self.ativa(agora):
            return datapaths, habil

        restringiu = False
        novos = []
        for d in datapaths:
            caminho = d["caminho"]
            links = {_link(caminho[i], caminho[i + 1]) for i in range(len(caminho) - 1)}
            protegidos = links & self.protegidos.keys()
            if not protegidos:
                novos.append(d)
                continue
            if self.modo in ("reserva", "reserva_demanda"):
                reserva = max(self.reserva_link(link, agora) for link in protegidos)
                self._soma_reserva += reserva
                self._n_reserva += 1
                limite = self.numero_de_slots - reserva
                janelas = [
                    (ini, min(fim, limite - 1))
                    for ini, fim in d["lista_de_inicios_e_fins"]
                    if ini <= limite - 1
                ]
                maior = max((fim - ini + 1 for ini, fim in janelas), default=0)
                if maior < d["maior_janela_contigua_continua"]:
                    restringiu = True
                d = {**d, "lista_de_inicios_e_fins": janelas,
                     "maior_janela_contigua_continua": maior}
                novos.append(d)
            else:  # adaptativo: keep the request off the link with probability p
                p = max(self._p_bloqueio(link) for link in protegidos)
                if p > 0 and self.rng.random() < p:
                    restringiu = True
                    continue
                novos.append(d)

        if restringiu:
            self.normais_restringidas += 1
        habil = any(
            d["maior_janela_contigua_continua"] >= d["numero_slots_necessarios"]
            for d in novos
        )
        return novos, habil
