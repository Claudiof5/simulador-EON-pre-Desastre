"""Cooperation metrics defined in ``overleaf/problema.tex`` (Objetivo e métricas).

- ``B_n`` / ``B_m``: blocking rate of background / migration requests.
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
    normais = df[~migracao]
    migracoes = df[migracao]
    normais_janela = normais[(tempo[~migracao] >= tau_min) & (tempo[~migracao] < t_d)]

    etas = eta_por_isp(df, scenario)
    eta_k = _media([etas[i] for i in k_set if i in etas])
    eta_iso = _media([etas[i] for i in isolados if i in etas])
    gamma = eta_k - eta_iso if k_set and isolados else math.nan

    b_n = _taxa_bloqueio(normais)
    b_m = _taxa_bloqueio(migracoes)
    src_normais = normais["src_isp_index"].astype(int)
    resumo = {
        "K": rotulo_cooperantes(k_set),
        "k": len(k_set),
        "B_n": b_n,
        "B_m": b_m,
        "A_n": 1 - b_n,
        "A_m": 1 - b_m,
        "B_n_janela": _taxa_bloqueio(normais_janela),
        "eta_todos": _media(list(etas.values())),
        "eta_K": eta_k,
        "eta_isolados": eta_iso,
        "Gamma": gamma,
        # Background blocking of K members vs isolated ISPs (cost of protection)
        "B_n_K": _taxa_bloqueio(normais[src_normais.isin(k_set)]),
        "B_n_isolados": _taxa_bloqueio(normais[src_normais.isin(isolados)]),
        "n_normais": len(normais),
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
    K, k, em_K, eta_K, eta_isolados, Gamma, B_n_K, B_n_isolados.

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

    def _bn(grupo: set[int]) -> float:
        n = sum(linhas_isp[i].get("n_normais_i", 0) for i in grupo)
        if not grupo or n == 0:
            return math.nan
        return (
            sum(
                linhas_isp[i]["B_n_i"] * linhas_isp[i].get("n_normais_i", 0)
                for i in grupo
            )
            / n
        )

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
                }
            )
            por_isp.extend(
                {**linhas_isp[i], "K": rotulo, "k": k, "em_K": i in k_set}
                for i in ids
            )
    return resumos, por_isp
