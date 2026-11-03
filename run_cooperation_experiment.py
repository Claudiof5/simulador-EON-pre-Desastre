"""Run the cooperating-set (K) experiment from the command line.

For every base scenario it runs all 2^I cooperating sets K on the weighted
disaster-aware scenario (output/cenario_disaster_aware{i}.pkl) plus one run of
the First-Fit competitor on the same instance
(output/cenario_nao_disaster_aware{i}.pkl). Finished runs are skipped, so the
command can be interrupted and restarted.

Usage:
    poetry run python run_cooperation_experiment.py --bases 0
    poetry run python run_cooperation_experiment.py --bases 0 1 2 --workers 6
    poetry run python run_cooperation_experiment.py --bases 0 --modulacao-fixa 1

With --modulacao-fixa every path uses that modulation factor (no distance-based
modulation) and results go to a separate folder (..._mod<factor>).

With --protecao <name> the weighted router also protects migration corridors on
links exclusive to the cooperating set (see PROTECOES); results go to
..._prot-<name>. First-Fit is skipped (the protection does not apply to it).
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from itertools import combinations
from pathlib import Path

import pandas as pd

from experiment_worker import metrics_path, run_cooperation_experiment

# Migration-corridor protection variants (ScenarioConfig protecao_* overrides)
PROTECOES: dict[str, dict] = {
    "reserva": {"protecao_modo": "reserva", "protecao_escopo": "cooperacao"},
    "adaptativo": {"protecao_modo": "adaptativo", "protecao_escopo": "cooperacao"},
    # Control: each ISP protects the links only it uses, cooperating or not
    "reserva_isolado": {"protecao_modo": "reserva", "protecao_escopo": "isolado"},
    "adaptativo_isolado": {
        "protecao_modo": "adaptativo",
        "protecao_escopo": "isolado",
    },
}
# Reservation sweep: "reserva" / "reserva_isolado" above are the 25% runs.
# Any other percentage is registered by nome_reserva(); these are pre-registered
# so the command line accepts them.
def nome_reserva(pct: int, isolado: bool = False) -> str:
    """PROTECOES key for a reservation percentage, registering it if needed.

    25% keeps its original name ("reserva" / "reserva_isolado").
    """
    if not 0 < pct < 100:
        raise ValueError(f"pct must be between 0 and 100, got {pct}")
    prefixo = "reserva_isolado" if isolado else "reserva"
    nome = prefixo if pct == 25 else f"{prefixo}_{pct:g}"
    PROTECOES.setdefault(
        nome,
        {
            "protecao_modo": "reserva",
            "protecao_escopo": "isolado" if isolado else "cooperacao",
            "protecao_reserva_fracao": pct / 100,
        },
    )
    return nome


# Reservation sized by each owner's remaining migration, main path only
PROTECOES["demanda"] = {
    "protecao_modo": "reserva_demanda",
    "protecao_escopo": "cooperacao",
    "protecao_caminhos_corredor": 1,
}
PROTECOES["demanda_isolado"] = {**PROTECOES["demanda"], "protecao_escopo": "isolado"}
# Same sizing, applied to every exclusive link of the first 3 corridor paths
PROTECOES["demanda_corredor"] = {**PROTECOES["demanda"], "protecao_caminhos_corredor": 3}
PROTECOES["demanda_corredor_isolado"] = {
    **PROTECOES["demanda_corredor"],
    "protecao_escopo": "isolado",
}


# Simplified demand-driven reservation: a link reserves the largest need among
# its owners instead of their sum
PROTECOES["demanda_max"] = {**PROTECOES["demanda"], "protecao_agregacao": "max"}
# ... over each provider's first 3 migration paths, need split by observed use
PROTECOES["demanda_max_3c"] = {
    **PROTECOES["demanda_max"],
    "protecao_caminhos_corredor": 3,
    "protecao_divisao_uso": True,
}
# ... with the first 3 paths leaving the disaster node through different exits
PROTECOES["demanda_max_3c_saidas"] = {
    **PROTECOES["demanda_max_3c"],
    "migracao_saidas_distintas": 3,
}
# Ablation: different exits only, no reservation
PROTECOES["saidas_sem_reserva"] = {"migracao_saidas_distintas": 3}

# Last-Fit for migration (background keeps First-Fit): alone, and combined
# with the simplified demand-driven reservation
PROTECOES["lastfit_sem_reserva"] = {"migracao_last_fit": True}
PROTECOES["lastfit_demanda_max"] = {**PROTECOES["demanda_max"], "migracao_last_fit": True}
PROTECOES["lastfit_demanda_max_3c"] = {**PROTECOES["demanda_max_3c"], "migracao_last_fit": True}


def nome_feedback(lam: float, isolado: bool = False) -> str:
    """PROTECOES key for the feedback reserve with weight lambda, registering it.

    Corridor of 3 paths, need split by where migration is accepted, reserve
    capped at 50% of each link (see MigrationProtection).
    """
    if lam < 0:
        raise ValueError(f"lambda must be >= 0, got {lam}")
    nome = f"feedback{'_isolado' if isolado else ''}_l{lam:g}"
    PROTECOES.setdefault(
        nome,
        {
            "protecao_modo": "reserva_feedback",
            "protecao_escopo": "isolado" if isolado else "cooperacao",
            "protecao_caminhos_corredor": 3,
            "protecao_feedback_lambda": lam,
            "protecao_reserva_max": 0.5,
        },
    )
    return nome


def nome_corredor(pct: int, peso: str = "posicao", isolado: bool = False) -> str:
    """PROTECOES key for the corridor-weighted reserve, registering it.

    pct is the reserve per corridor path (main path weight 1); a link adds it
    up for every corridor path and owner through it, capped at 85%.
    peso: "posicao" (w = 1/rank) or "uso" (w = observed share / largest share).
    """
    if peso not in ("posicao", "uso"):
        raise ValueError(f"peso must be 'posicao' or 'uso', got {peso!r}")
    if not 0 < pct < 100:
        raise ValueError(f"pct must be between 0 and 100, got {pct}")
    nome = f"corredor_{peso}{'_isolado' if isolado else ''}_{pct:g}"
    PROTECOES.setdefault(
        nome,
        {
            "protecao_modo": "reserva_corredor" if peso == "posicao" else "reserva_corredor_uso",
            "protecao_escopo": "isolado" if isolado else "cooperacao",
            "protecao_caminhos_corredor": 3,
            "protecao_reserva_fracao": pct / 100,
            "protecao_reserva_max": 0.85,
        },
    )
    return nome


for _pct in (10, 15, 20, 30):
    for _peso in ("posicao", "uso"):
        nome_corredor(_pct, _peso)
        nome_corredor(_pct, _peso, isolado=True)

for _lam in (0.5, 1, 2):
    nome_feedback(_lam)
    nome_feedback(_lam, isolado=True)

for _pct in (10, 40, 55, 70):
    nome_reserva(_pct)
    nome_reserva(_pct, isolado=True)


def nome_reserva_principal(pct: int) -> str:
    """PROTECOES key for a fixed reservation of pct% on the main path only.

    Same scope as the demand-driven rule (``demanda_max``): exclusive links of
    each member's main migration path. This is the fixed control of the article.
    """
    if not 0 < pct < 100:
        raise ValueError(f"pct must be between 0 and 100, got {pct}")
    nome = f"reserva_principal_{pct:g}"
    PROTECOES.setdefault(
        nome,
        {
            "protecao_modo": "reserva",
            "protecao_escopo": "cooperacao",
            "protecao_reserva_fracao": pct / 100,
            "protecao_caminhos_corredor": 1,
        },
    )
    return nome


for _pct in (25, 55, 85):
    nome_reserva_principal(_pct)

COOP_PATH = "output/cenario_disaster_aware{i}.pkl"
FIRST_FIT_PATH = "output/cenario_nao_disaster_aware{i}.pkl"


def montar_tarefas(
    bases: list[int],
    output_dir: Path,
    first_fit: bool = True,
    somente_k_vazio: bool = False,
) -> list[dict]:
    """List the pending runs (all K per base + First-Fit), skipping finished ones.

    somente_k_vazio=True keeps only K = empty set: for variants whose outcome does
    not depend on K (see cooperation_metrics.expandir_para_todos_k).
    """
    tarefas = []
    for i in bases:
        coop_path = COOP_PATH.format(i=i)
        with open(coop_path, "rb") as f:
            isp_ids = sorted(isp.isp_id for isp in pickle.load(f).lista_de_isps)
        subconjuntos = [
            c for k in range(len(isp_ids) + 1) for c in combinations(isp_ids, k)
        ]
        if somente_k_vazio:
            subconjuntos = [()]
        for k_set in subconjuntos:
            tarefas.append(
                {"base_path": coop_path, "base_index": i, "cooperantes": k_set,
                 "variante": "cooperacao"}
            )
        if first_fit:
            tarefas.append(
                {"base_path": FIRST_FIT_PATH.format(i=i), "base_index": i,
                 "cooperantes": (), "variante": "first_fit"}
            )
    return [
        t
        for t in tarefas
        if not resultado_completo(
            metrics_path(output_dir, t["cooperantes"], t["base_index"], t["variante"])
        )
    ]


# Fields every saved run must have; older results without them are re-run
CAMPOS_OBRIGATORIOS = ("U", "D_n_km")


def resultado_completo(caminho: Path) -> bool:
    """True if the run's JSON exists and has every current metric."""
    if not caminho.exists():
        return False
    try:
        resumo = json.loads(caminho.read_text())["summary"]
    except (ValueError, KeyError):
        return False
    return all(c in resumo for c in CAMPOS_OBRIGATORIOS)


def pasta_saida(
    fator_modulacao_fixo: float | None,
    protecao: str | None = None,
    sem_pesos: bool = False,
    destino: str | None = None,
) -> Path:
    """Default results folder; each modulation/protection setting gets its own.

    sem_pesos=True (no cooperative weights) uses output/cooperation_experiment_v3.
    """
    nome = (
        "output/cooperation_experiment_v3"
        if sem_pesos
        else "output/cooperation_experiment_v2"
    )
    if destino == "distancia":
        nome += "_dist"
    if fator_modulacao_fixo is not None:
        nome += f"_mod{fator_modulacao_fixo:g}"
    if protecao is not None:
        nome += f"_prot-{protecao}"
    return Path(nome)


def consolidar(output_dir: Path) -> None:
    """Merge every metrics JSON into two CSVs."""
    resumos, por_isp = [], []
    for arquivo in sorted(output_dir.glob("*/metrics_*.json")):
        r = json.loads(arquivo.read_text())
        resumos.append(r["summary"])
        por_isp.extend(r["per_isp"])
    pd.DataFrame(resumos).to_csv(output_dir / "resumo_por_rodada.csv", index=False)
    pd.DataFrame(por_isp).to_csv(output_dir / "resumo_por_isp.csv", index=False)
    print(f"✓ {len(resumos)} runs consolidated in {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bases", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--workers", type=int, default=min(os.cpu_count() or 4, 8))
    parser.add_argument("--output", default=None)
    parser.add_argument(
        "--modulacao-fixa",
        type=float,
        default=None,
        help="fixed modulation factor for every path (default: distance-based)",
    )
    parser.add_argument("--no-first-fit", action="store_true")
    parser.add_argument("--protecao", choices=sorted(PROTECOES), default=None)
    parser.add_argument(
        "--destino",
        choices=["saltos", "distancia"],
        default=None,
        help="migration destination: farthest in hops or in km (default: as stored)",
    )
    parser.add_argument(
        "--recortar",
        action="store_true",
        help="end the simulation at the failure (faster, same metrics)",
    )
    parser.add_argument(
        "--prefixo",
        action="store_true",
        help="simulate [0, first alert) once per base and start every run from it",
    )
    parser.add_argument(
        "--sem-pesos",
        action="store_true",
        help="drop the cooperative alpha/beta/gamma weights (writes to ..._v3)",
    )
    opts = parser.parse_args()

    output_dir = Path(
        opts.output
        or pasta_saida(opts.modulacao_fixa, opts.protecao, opts.sem_pesos, opts.destino)
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    first_fit = not opts.no_first_fit and opts.protecao is None
    tarefas = montar_tarefas(opts.bases, output_dir, first_fit)
    prefixos = {}
    if opts.prefixo:
        from experiment_worker import calcular_prefixo, prefixo_path

        for b in opts.bases:
            caminho = prefixo_path("output", b, opts.modulacao_fixa)
            if not caminho.exists():
                print(f"computing prefix for base {b}...")
                calcular_prefixo(COOP_PATH.format(i=b), caminho, opts.modulacao_fixa)
            prefixos[b] = str(caminho)

    for idx, t in enumerate(tarefas):
        t.update(
            prefixo=prefixos.get(t["base_index"]),
            output_dir=str(output_dir),
            run_index=idx,
            total_runs=len(tarefas),
            fator_modulacao_fixo=opts.modulacao_fixa,
            protecao=PROTECOES.get(opts.protecao),
            sem_pesos=opts.sem_pesos,
            destino_migracao=opts.destino,
            recortar_janela=opts.recortar,
        )

    modulacao = (
        "distance-based"
        if opts.modulacao_fixa is None
        else f"fixed {opts.modulacao_fixa:g}"
    )
    print(
        f"{len(tarefas)} runs pending | bases {opts.bases} | "
        f"{opts.workers} processes | modulation {modulacao} | "
        f"protection {opts.protecao} | -> {output_dir}"
    )
    inicio = datetime.now()
    falhas = 0
    with ProcessPoolExecutor(max_workers=opts.workers) as executor:
        futures = [executor.submit(run_cooperation_experiment, t) for t in tarefas]
        for future in as_completed(futures):
            falhas += not future.result()["success"]
    print(f"Done in {datetime.now() - inicio} | failures: {falhas}")
    consolidar(output_dir)


if __name__ == "__main__":
    main()
