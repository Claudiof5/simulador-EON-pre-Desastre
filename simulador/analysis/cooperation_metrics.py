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
                "n_migracao_i": len(mig_i),
            }
        )
    return resumo, por_isp
