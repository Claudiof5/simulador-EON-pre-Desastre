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
  With ``caminhos_corredor = 1`` only the main path is protected. With more
  corridor paths, every exclusive link of the first ``caminhos_corredor`` paths
  reserves the owner's full need, using the modulation factor of the first
  corridor path that crosses that link (backup capacity for when the main
  path is congested on links that cannot be protected).

- ``reserva_feedback``: the demand-driven reserve corrected by a feedback
  loop. Each owner o has a gain g_o (starts at 1), updated every
  ``feedback_intervalo`` seconds:

      g_o <- g_o * exp(kappa * (atraso - lambda * B_n_res - ociosa))

  atraso = 1 - (migration accepted in the interval) / (what o had to migrate
  in it to finish D_o by t_d), clipped to [-1, 1]: positive when o is behind
  schedule, negative when ahead. (Migration blocking itself is not used: the
  datacenter offers more than it needs, so blocked requests do not mean it is
  late.) B_n_res is the share of background requests that touched o's
  protected links and lost every feasible path because of the reserve;
  ociosa the share of o's reserved slots left free, counted only when o is on
  schedule (reserve nobody needs). lambda weighs background loss against the
  migration deficit.
  The need is split among o's corridor paths in proportion to where its
  migration was actually accepted (moving average, starts on the main path),
  so backup paths only get reserve once migration spills onto them. A link
  reserves sum_o g_o * sum_{p through link} share_{o,p} * need_o(f_p), capped
  at ``reserva_max`` of its slots so it never disappears for background.

- ``reserva_corredor``: fixed reserve weighted by the corridor. Each owner
  adds, on every protected link, ``reserva_fracao`` x w_p for each of its
  corridor paths p through the link, with w_p = 1/rank (1, 1/2, 1/3): links
  where several corridor paths (or several owners) converge reserve more,
  links on a single backup path little. Capped at ``reserva_max``.
- ``reserva_corredor_uso``: same, but w_p = share_p / max_q share_q, where
  share is where the owner's migration was actually accepted (moving
  average, starts all on the main path): the most used path weighs 1.

Options of ``reserva_demanda``:

- ``agregacao``: how a link combines the needs of its owners. ``"soma"`` adds
  them up; ``"max"`` keeps only the largest (each owner reserves its own need
  and the link reserves the largest of them).
- ``divisao_uso``: with ``caminhos_corredor > 1``, the need is split among the
  owner's corridor paths in proportion to where its migration was accepted
  (moving average, starts all on the main path), instead of being reserved on
  the main path only.

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

MODOS = (
    "reserva",
    "adaptativo",
    "reserva_demanda",
    "reserva_feedback",
    "reserva_corredor",
    "reserva_corredor_uso",
)
MODOS_RESERVA = ("reserva", "reserva_demanda", "reserva_feedback", "reserva_corredor", "reserva_corredor_uso")
# Modes that follow where migration is accepted (per-path shares)
MODOS_USO = ("reserva_feedback", "reserva_corredor_uso")
GANHO_MIN, GANHO_MAX = 0.05, 20.0
ALFA_USO = 0.5  # moving-average weight of the last interval in the path shares
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
        feedback_lambda: float = 1.0,
        feedback_kappa: float = 0.5,
        feedback_intervalo: float = 1.0,
        reserva_max: float | None = None,
        agregacao: str = "soma",
        divisao_uso: bool = False,
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
        self.feedback_lambda = feedback_lambda
        self.feedback_kappa = feedback_kappa
        self.feedback_intervalo = feedback_intervalo
        self.reserva_max = reserva_max
        if agregacao not in ("soma", "max"):
            raise ValueError(f"agregacao must be 'soma' or 'max', got {agregacao!r}")
        self.agregacao = agregacao
        # Modes that track where migration is accepted (per-path shares)
        self._usa_uso = modo in MODOS_USO or (modo == "reserva_demanda" and divisao_uso)
        # Feedback state, per owner
        self._ganho: dict[int, float] = {isp.isp_id: 1.0 for isp in lista_de_isps}
        self._caminhos: dict[int, list[tuple[tuple[int, ...], set[Link], float]]] = {}
        self._uso_caminho: dict[int, list[float]] = {}
        self._int_mig: dict[int, list[float]] = {}  # tried, blocked, accepted Gb
        self._inicio_intervalo: float | None = None
        self._int_mig_caminho: dict[int, list[float]] = {}  # accepted Gb per path
        self._int_fundo: dict[int, list[int]] = {}  # touched, blocked by the reserve
        self._proxima_atualizacao: float | None = None
        self.historico_ganho: list[tuple[float, dict[int, float]]] = []
        self._por_id = {isp.isp_id: isp for isp in lista_de_isps}
        self._migrado: dict[int, float] = {isp.isp_id: 0.0 for isp in lista_de_isps}
        self._fator_principal: dict[int, float] = {}
        # owner -> link -> modulation factor of the first corridor path using it
        self._fator_link: dict[int, dict[Link, float]] = {}

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
        self.links_ja_protegidos: set[Link] = set()  # every link protected at some point
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
        fatores: dict[Link, float] = {}
        lista = []
        for c in caminhos:  # in order: the first path through a link wins
            fator = c.get("fator_de_modulacao", 1.0)
            links = {
                _link(c["caminho"][i], c["caminho"][i + 1])
                for i in range(len(c["caminho"]) - 1)
            }
            lista.append((tuple(int(n) for n in c["caminho"]), links, fator))
            for link in links:
                fatores.setdefault(link, fator)
        self._fator_link[isp.isp_id] = fatores
        self._caminhos[isp.isp_id] = lista
        if lista and len(self._uso_caminho.get(isp.isp_id, ())) != len(lista):
            self._uso_caminho[isp.isp_id] = [1.0] + [0.0] * (len(lista) - 1)
        return set(fatores)

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
        self.links_ja_protegidos |= protegidos.keys()
        self.max_links_protegidos = max(self.max_links_protegidos, len(protegidos))

    def registra_migracao(
        self,
        isp_id: int,
        bloqueada: bool,
        banda: float = 0.0,
        caminho: list[int] | None = None,
    ) -> None:
        if isp_id in self._migracoes:
            self._migracoes[isp_id].append(bool(bloqueada))
        if not bloqueada and isp_id in self._migrado:
            self._migrado[isp_id] += banda
        if not self._usa_uso:
            return
        contagem = self._int_mig.setdefault(isp_id, [0, 0, 0.0])
        contagem[0] += 1
        contagem[1] += bool(bloqueada)
        if not bloqueada:
            contagem[2] += banda
        if not bloqueada and caminho is not None:
            alvo = tuple(int(n) for n in caminho)
            for idx, (nos, _, _) in enumerate(self._caminhos.get(isp_id, ())):
                if nos == alvo:
                    uso = self._int_mig_caminho.setdefault(
                        isp_id, [0.0] * len(self._caminhos[isp_id])
                    )
                    uso[idx] += banda
                    break

    def slots_necessarios(
        self, isp_id: int, agora: float, link: Link | None = None
    ) -> int:
        """Slots the owner needs to finish migrating by t_d.

        Uses the modulation factor of the owner's first corridor path through
        ``link`` (the main path's factor when ``link`` is None or unknown).
        """
        dc = self._por_id[isp_id].datacenter
        if dc is None:
            return 0
        fator = self._fator_principal.get(isp_id, 1.0)
        if link is not None:
            fator = self._fator_link.get(isp_id, {}).get(link, fator)
        return math.ceil(self._necessidade(isp_id, agora) / (fator * self.slot_size))

    def _necessidade(self, isp_id: int, agora: float) -> float:
        """margem * h * (bandwidth per second still needed): slots x slot_size at factor 1."""
        dc = self._por_id[isp_id].datacenter
        if dc is None:
            return 0.0
        restante = dc.tamanho_datacenter - self._migrado.get(isp_id, 0.0)
        if restante <= 0:
            return 0.0
        tempo = max(self.t_d - agora, 1e-6)
        taxa = restante / tempo  # accepted bandwidth per second still needed
        return self.margem * taxa * self.holding_time

    def _agregar(self, valores: list[float]) -> float:
        if not valores:
            return 0
        return max(valores) if self.agregacao == "max" else sum(valores)

    def _reserva_por_uso(self, link: Link, agora: float) -> float:
        """Each owner's need split among its corridor paths by observed use."""
        por_dono = []
        for dono in self.protegidos.get(link, ()):
            base = self._necessidade(dono, agora)
            if base <= 0:
                continue
            ganho = self._ganho[dono] if self.modo == "reserva_feedback" else 1.0
            partes = self._uso_caminho.get(dono, [1.0])
            soma = sum(partes) or 1.0
            parcela = 0.0
            for (_, links, fator), parte in zip(self._caminhos.get(dono, ()), partes):
                if link in links and parte > 0:
                    parcela += ganho * (parte / soma) * base / (fator * self.slot_size)
            por_dono.append(parcela)
        return self._agregar(por_dono)

    def reserva_link(self, link: Link, agora: float) -> int:
        """Slots reserved on a protected link at time ``agora``."""
        if self.modo == "reserva":
            return int(round(self.reserva_fracao * self.numero_de_slots))
        if self.modo == "reserva_feedback" or (
            self.modo == "reserva_demanda" and self._usa_uso
        ):
            total = math.ceil(self._reserva_por_uso(link, agora))
        elif self.modo in ("reserva_corredor", "reserva_corredor_uso"):
            total = round(self._peso_corredor(link) * self.reserva_fracao * self.numero_de_slots)
        else:
            total = self._agregar(
                [
                    self.slots_necessarios(dono, agora, link)
                    for dono in self.protegidos.get(link, ())
                ]
            )
        teto = self.numero_de_slots
        if self.reserva_max is not None:
            teto = min(teto, int(self.reserva_max * self.numero_de_slots))
        return min(teto, total)

    def _peso_corredor(self, link: Link) -> float:
        """Sum over owners and their corridor paths through ``link`` of w_p."""
        peso = 0.0
        for dono in self.protegidos.get(link, ()):
            caminhos = self._caminhos.get(dono, ())
            if self.modo == "reserva_corredor":
                pesos = [1.0 / (i + 1) for i in range(len(caminhos))]
            else:
                partes = self._uso_caminho.get(dono) or [1.0]
                topo = max(partes) or 1.0
                pesos = [p / topo for p in partes]
            for (_, links, _), w in zip(caminhos, pesos):
                if link in links:
                    peso += w
        return peso

    # --------------------------------------------------------------- feedback
    def _ociosa(self, dono: int, agora: float) -> float:
        """Share of the slots reserved on the owner's links that are free now."""
        reservado = livre = 0
        for link, donos in self.protegidos.items():
            if dono not in donos:
                continue
            r = self.reserva_link(link, agora)
            if r <= 0:
                continue
            u, v = tuple(link)
            slots = self.topology[u][v].get("slots")
            if slots is None:
                continue
            reservado += r
            livre += sum(1 for x in slots[len(slots) - r:] if x == 0)
        return livre / reservado if reservado else 0.0

    def _atraso(self, dono: int, agora: float) -> float:
        """How far the owner fell behind schedule in the last interval."""
        dc = self._por_id[dono].datacenter
        inicio = self._inicio_intervalo
        if dc is None or inicio is None or agora <= inicio:
            return 0.0
        aceito = self._int_mig.get(dono, (0, 0, 0.0))[2]
        # Remaining volume at the start of the interval, over the time left then
        restante = dc.tamanho_datacenter - self._migrado.get(dono, 0.0) + aceito
        if restante <= 0:
            return -1.0
        precisava = restante / max(self.t_d - inicio, 1e-6) * (agora - inicio)
        return max(-1.0, min(1.0, 1.0 - aceito / precisava))

    def _atualizar_ganhos(self, agora: float) -> None:
        donos = {d for ds in self.protegidos.values() for d in ds}
        for dono in donos:
            self._atualizar_uso(dono)
            if self.modo != "reserva_feedback":
                continue
            atraso = self._atraso(dono, agora)
            tocadas, barradas = self._int_fundo.get(dono, (0, 0))
            b_n = barradas / tocadas if tocadas else 0.0
            ociosa = self._ociosa(dono, agora) if atraso <= 0 else 0.0
            erro = atraso - self.feedback_lambda * b_n - ociosa
            g = self._ganho[dono] * math.exp(self.feedback_kappa * erro)
            self._ganho[dono] = min(GANHO_MAX, max(GANHO_MIN, g))
        if self.modo == "reserva_feedback":
            self.historico_ganho.append(
                (agora, {d: self._ganho[d] for d in sorted(donos)})
            )
        self._int_mig.clear()
        self._int_mig_caminho.clear()
        self._int_fundo.clear()
        self._inicio_intervalo = agora

    def _atualizar_uso(self, dono: int) -> None:
        uso = self._int_mig_caminho.get(dono)
        if uso and sum(uso) > 0:
            total = sum(uso)
            self._uso_caminho[dono] = [
                (1 - ALFA_USO) * a + ALFA_USO * b / total
                for a, b in zip(self._uso_caminho[dono], uso)
            ]

    def _talvez_atualizar(self, agora: float) -> None:
        if self._proxima_atualizacao is None:
            self._proxima_atualizacao = agora + self.feedback_intervalo
            self._inicio_intervalo = agora
            return
        if agora >= self._proxima_atualizacao:
            self._atualizar_ganhos(agora)
            while self._proxima_atualizacao <= agora:
                self._proxima_atualizacao += self.feedback_intervalo

    @property
    def ganho_medio(self) -> float | None:
        """Mean gain over owners and feedback updates (None if no update)."""
        valores = [g for _, gs in self.historico_ganho for g in gs.values()]
        return sum(valores) / len(valores) if valores else None

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
        if self._usa_uso and self.ativa(agora):
            self._talvez_atualizar(agora)
        if requisicao.requisicao_de_migracao or not self.ativa(agora):
            return datapaths, habil
        habil_antes = habil
        donos_tocados: set[int] = set()

        restringiu = False
        novos = []
        for d in datapaths:
            caminho = d["caminho"]
            links = {_link(caminho[i], caminho[i + 1]) for i in range(len(caminho) - 1)}
            protegidos = links & self.protegidos.keys()
            if not protegidos:
                novos.append(d)
                continue
            for link in protegidos:
                donos_tocados |= self.protegidos[link]
            if self.modo in MODOS_RESERVA:
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
        if self.modo == "reserva_feedback":
            barrada = habil_antes and not habil
            for dono in donos_tocados:
                contagem = self._int_fundo.setdefault(dono, [0, 0])
                contagem[0] += 1
                contagem[1] += barrada
        return novos, habil
