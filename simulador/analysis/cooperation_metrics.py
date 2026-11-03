"""Cooperation metrics defined in ``overleaf/problema.tex`` (Objetivo e métricas).

- ``B_n`` / ``B_m``: blocking rate of background / migration requests, measured
  over the warning window: a background request of ISP i counts only if it was
  created in [tau_i, t_d) (``B_n_total`` keeps every simulated request). All
  migration requests are created in that window by construction.
- ``B``: overall blocking rate over the same requests (background in the window
  plus migration).
- ``A = 1 - B``: availability as used in this repo (not two-terminal availability).
- ``eta_i = M_i(t_d) / D_i``: fraction of ISP i's datacenter migrated before the
  failure. ``M_i`` is the bandwidth of accepted migration requests created before
  ``t_d``; ``D_i`` is the datacenter size. Capped at 1 because pre-generated
  migration traffic keeps flowing after ``M_i >= D_i``.
- ``eta(S)``: mean of ``eta_i`` over S.
- ``Gamma(K) = eta(K) - eta(I \\ K)``, defined only when both sets are non-empty.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from simulador.entities.scenario import Scenario


def rotulo_cooperantes(cooperantes: Iterable[int]) -> str:
    """Return a stable label for K, e.g. ``K_0-2-4`` or ``K_none``."""
    ids = sorted(set(cooperantes))
    return "K_" + ("-".join(map(str, ids)) if ids else "none")


def _como_bool(serie: pd.Series) -> pd.Series:
    """Coerce a column that may come from CSV (strings) or memory to bool."""
    if serie.dtype == bool:
        return serie
    return serie.map(lambda v: str(v).strip().lower() == "true")


def _taxa_bloqueio(df: pd.DataFrame) -> float:
    if len(df) == 0:
        return math.nan
    return float(_como_bool(df["bloqueada"]).mean())


def _media(valores: list[float]) -> float:
    return sum(valores) / len(valores) if valores else math.nan


def eta_por_isp(df: pd.DataFrame, scenario: Scenario) -> dict[int, float]:
    """Compute ``eta_i`` for every ISP that has a datacenter."""
    t_d = scenario.desastre.start
    migracao = _como_bool(df["requisicao_de_migracao"])
    aceita = ~_como_bool(df["bloqueada"])
    antes_da_falha = df["tempo_criacao"].astype(float) < t_d
    migrado = (
        df[migracao & aceita & antes_da_falha]
        .groupby("src_isp_index")["bandwidth"]
        .sum()
    )

    etas: dict[int, float] = {}
    for isp in scenario.lista_de_isps:
        dc = isp.datacenter
        if dc is None or dc.tamanho_datacenter <= 0:
            continue
        m_i = float(migrado.get(isp.isp_id, 0.0))
        etas[isp.isp_id] = min(1.0, m_i / dc.tamanho_datacenter)
    return etas


def metricas_cooperacao(
    df: pd.DataFrame,
    scenario: Scenario,
    cooperantes: Iterable[int],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Compute the problema.tex metrics for one run with cooperating set K.

    Args:
        df: Request dataframe produced by ``Metrics.criar_dataframe``
        scenario: The scenario that was simulated (for t_d, tau_i, D_i)
        cooperantes: ISP IDs in K

    Returns:
        (summary, per_isp): one summary row for the run and one row per ISP.
    """
    k_set = set(cooperantes)
    todos = {isp.isp_id for isp in scenario.lista_de_isps}
    isolados = todos - k_set

    t_d = scenario.desastre.start
    taus = {
        isp.isp_id: isp.datacenter.tempo_de_reacao
        for isp in scenario.lista_de_isps
        if isp.datacenter is not None
    }
    tau_min = min(taus.values()) if taus else 0.0

    migracao = _como_bool(df["requisicao_de_migracao"])
    tempo = df["tempo_criacao"].astype(float)
    normais_todas = df[~migracao]
    migracoes = df[migracao]
    tempo_n = tempo[~migracao]
    normais_janela = normais_todas[(tempo_n >= tau_min) & (tempo_n < t_d)]
    # Each ISP's background counts only in its own warning window [tau_i, t_d)
    tau_src = normais_todas["src_isp_index"].astype(int).map(taus).astype(float)
    normais = normais_todas[(tempo_n >= tau_src) & (tempo_n < t_d)]

    etas = eta_por_isp(df, scenario)
    eta_k = _media([etas[i] for i in k_set if i in etas])
    eta_iso = _media([etas[i] for i in isolados if i in etas])
    gamma = eta_k - eta_iso if k_set and isolados else math.nan

    b_n = _taxa_bloqueio(normais)
    b_m = _taxa_bloqueio(migracoes)
    todas = pd.concat([normais, migracoes])
    b_geral = _taxa_bloqueio(todas)
    src_normais = normais["src_isp_index"].astype(int)
    src_todas = todas["src_isp_index"].astype(int)
    resumo = {
        "K": rotulo_cooperantes(k_set),
        "k": len(k_set),
        "B": b_geral,
        "A": 1 - b_geral,
        "B_n": b_n,
        "B_m": b_m,
        "A_n": 1 - b_n,
        "A_m": 1 - b_m,
        "B_n_janela": _taxa_bloqueio(normais_janela),
        "B_n_total": _taxa_bloqueio(normais_todas),
        "eta_todos": _media(list(etas.values())),
        "eta_K": eta_k,
        "eta_isolados": eta_iso,
        "Gamma": gamma,
        # Background blocking of K members vs isolated ISPs (cost of protection)
        "B_n_K": _taxa_bloqueio(normais[src_normais.isin(k_set)]),
        "B_n_isolados": _taxa_bloqueio(normais[src_normais.isin(isolados)]),
        "B_K": _taxa_bloqueio(todas[src_todas.isin(k_set)]),
        "B_isolados": _taxa_bloqueio(todas[src_todas.isin(isolados)]),
        "n_normais": len(normais),
        "n_normais_total": len(normais_todas),
        "n_migracao": len(migracoes),
        "t_d": t_d,
    }

    por_isp = []
    src = df["src_isp_index"].astype(int)
    for isp_id in sorted(todos):
        mig_i = migracoes[src[migracao] == isp_id]
        por_isp.append(
            {
                "K": resumo["K"],
                "k": len(k_set),
                "isp_id": isp_id,
                "em_K": isp_id in k_set,
                "tau_i": taus.get(isp_id, math.nan),
                "eta_i": etas.get(isp_id, math.nan),
                "B_m_i": _taxa_bloqueio(mig_i),
                "B_i": _taxa_bloqueio(todas[src_todas == isp_id]),
                "B_n_i": _taxa_bloqueio(normais[src_normais == isp_id]),
                "n_normais_i": int((src_normais == isp_id).sum()),
                "n_migracao_i": len(mig_i),
            }
        )
    return resumo, por_isp


def expandir_para_todos_k(
    resultado: dict[str, Any], isp_ids: Iterable[int]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Rebuild summary and per-ISP rows for every K from one K-independent run.

    Some variants do not depend on who cooperates (no protection, individual
    protection, First-Fit) once cooperative weights are off: the simulation is
    deterministic and K changes nothing. They run once (K = empty set) and this
    rebuilds, for every subset K, the fields that only depend on the labels:
    K, k, em_K, eta_K, eta_isolados, Gamma, B_n_K, B_n_isolados, B_K,
    B_isolados.

    Args:
        resultado: dict returned by run_cooperation_experiment (one run)
        isp_ids: all ISP ids of the scenario

    Returns:
        (summaries, per_isp) with one summary per subset K.
    """
    from itertools import combinations

    ids = sorted(isp_ids)
    base = resultado["summary"]
    linhas_isp = {row["isp_id"]: row for row in resultado["per_isp"]}

    def _pooled(grupo: set[int], taxa: str, contagens: tuple[str, ...]) -> float:
        def n_de(i: int) -> int:
            return sum(linhas_isp[i].get(c, 0) for c in contagens)

        n = sum(n_de(i) for i in grupo)
        if not grupo or n == 0 or any(taxa not in linhas_isp[i] for i in grupo):
            return math.nan
        return sum(linhas_isp[i][taxa] * n_de(i) for i in grupo) / n

    def _bn(grupo: set[int]) -> float:
        return _pooled(grupo, "B_n_i", ("n_normais_i",))

    def _b(grupo: set[int]) -> float:
        return _pooled(grupo, "B_i", ("n_normais_i", "n_migracao_i"))

    resumos, por_isp = [], []
    for k in range(len(ids) + 1):
        for comb in combinations(ids, k):
            k_set, fora = set(comb), set(ids) - set(comb)
            rotulo = rotulo_cooperantes(k_set)
            eta_k = _media([linhas_isp[i]["eta_i"] for i in k_set])
            eta_fora = _media([linhas_isp[i]["eta_i"] for i in fora])
            resumos.append(
                {
                    **base,
                    "K": rotulo,
                    "k": k,
                    "eta_K": eta_k,
                    "eta_isolados": eta_fora,
                    "Gamma": eta_k - eta_fora if k_set and fora else math.nan,
                    "B_n_K": _bn(k_set),
                    "B_n_isolados": _bn(fora),
                    "B_K": _b(k_set),
                    "B_isolados": _b(fora),
                }
            )
            por_isp.extend(
                {**linhas_isp[i], "K": rotulo, "k": k, "em_K": i in k_set}
                for i in ids
            )
    return resumos, por_isp


def uso_da_rede(
    requisicoes: Iterable[Any],
    topology: Any,
    inicio: float,
    fim: float,
    conexoes_iniciais: Iterable[tuple[list[int], tuple[int, int], float]] = (),
    links_protegidos: Iterable[Iterable[int]] = (),
) -> dict[str, Any]:
    """Spectrum usage in the window [inicio, fim), integrated exactly over time.

    Each accepted connection occupies its slots on every link of its path from
    its creation until its release; the usage is the occupied slot-time divided
    by the available slot-time (slots per link x links x window length).

    Args:
        requisicoes: Request objects of the run (accepted ones have a path)
        topology: networkx graph whose edges hold the ``slots`` array
        inicio: start of the window (first discovery time)
        fim: end of the window (failure time t_d)
        conexoes_iniciais: (path, (first, last slot), release time) of
            connections already active at ``inicio`` that are not among
            ``requisicoes`` (runs resumed from the shared prefix)
        links_protegidos: links protected at some point of the run

    Returns:
        U (whole network), U_n / U_m (share used by background / migration,
        U = U_n + U_m), U_protegidos (mean over the protected links, NaN if
        none) and U_links (per link, key "u-v" with u < v).
    """
    duracao = fim - inicio
    links = {
        frozenset((int(u), int(v))): len(d["slots"])
        for u, v, d in topology.edges(data=True)
    }
    ocupado = {link: 0.0 for link in links}
    ocupado_m = {link: 0.0 for link in links}

    def _soma(caminho, ini_fim, t0, t1, migracao):
        dt = min(t1, fim) - max(t0, inicio)
        if dt <= 0:
            return
        n_slots = ini_fim[1] - ini_fim[0] + 1
        for u, v in zip(caminho, caminho[1:]):
            link = frozenset((int(u), int(v)))
            ocupado[link] += n_slots * dt
            if migracao:
                ocupado_m[link] += n_slots * dt

    for caminho, ini_fim, t_fim in conexoes_iniciais:
        _soma(caminho, ini_fim, inicio, t_fim, False)
    for r in requisicoes:
        if r.bloqueada is not False or r.caminho is None or r.tempo_desalocacao is None:
            continue
        _soma(
            r.caminho,
            r.index_de_inicio_e_final,
            r.tempo_criacao,
            r.tempo_desalocacao,
            bool(r.requisicao_de_migracao),
        )

    capacidade = sum(links.values()) * duracao
    u_links = {link: ocupado[link] / (links[link] * duracao) for link in links}
    protegidos = [frozenset(int(x) for x in l) for l in links_protegidos]
    protegidos = [l for l in protegidos if l in links]
    total = sum(ocupado.values())
    total_m = sum(ocupado_m.values())
    return {
        "U": total / capacidade,
        "U_n": (total - total_m) / capacidade,
        "U_m": total_m / capacidade,
        "U_protegidos": (
            _media([u_links[l] for l in protegidos]) if protegidos else math.nan
        ),
        "n_links_protegidos": len(protegidos),
        "U_links": {
            "-".join(str(x) for x in sorted(link)): u for link, u in u_links.items()
        },
    }


def caminhos_fundo(
    requisicoes: Iterable[Any], taus: dict[int, float], t_d: float
) -> dict[str, float]:
    """Length of the paths given to accepted background requests.

    Counts background requests created in their own ISP's warning window
    [tau_i, t_d), like B_n. A reserve that pushes background traffic onto
    detours shows up as longer paths (more links, worse modulation). Only
    accepted requests have a path, so compare it together with B_n.

    Returns:
        D_n_km (mean path length in km), H_n (mean hops), n_fundo_aceitas.
    """
    distancias, saltos = [], []
    for r in requisicoes:
        if r.requisicao_de_migracao or r.bloqueada is not False or r.caminho is None:
            continue
        tau = taus.get(int(r.src_isp_index))
        if tau is None or not (tau <= r.tempo_criacao < t_d):
            continue
        distancias.append(float(r.distacia))
        saltos.append(len(r.caminho) - 1)
    return {
        "D_n_km": _media(distancias),
        "H_n": _media(saltos),
        "n_fundo_aceitas": len(distancias),
    }
