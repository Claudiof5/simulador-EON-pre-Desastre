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

for _pct in (10, 40, 55, 70):
    nome_reserva(_pct)
    nome_reserva(_pct, isolado=True)

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
        if not metrics_path(
            output_dir, t["cooperantes"], t["base_index"], t["variante"]
        ).exists()
    ]


def pasta_saida(
    fator_modulacao_fixo: float | None,
    protecao: str | None = None,
    sem_pesos: bool = False,
) -> Path:
    """Default results folder; each modulation/protection setting gets its own.

    sem_pesos=True (no cooperative weights) uses output/cooperation_experiment_v3.
    """
    nome = (
        "output/cooperation_experiment_v3"
        if sem_pesos
        else "output/cooperation_experiment_v2"
    )
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
        "--sem-pesos",
        action="store_true",
        help="drop the cooperative alpha/beta/gamma weights (writes to ..._v3)",
    )
    opts = parser.parse_args()

    output_dir = Path(
        opts.output or pasta_saida(opts.modulacao_fixa, opts.protecao, opts.sem_pesos)
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    first_fit = not opts.no_first_fit and opts.protecao is None
    tarefas = montar_tarefas(opts.bases, output_dir, first_fit)
    for idx, t in enumerate(tarefas):
        t.update(
            output_dir=str(output_dir),
            run_index=idx,
            total_runs=len(tarefas),
            fator_modulacao_fixo=opts.modulacao_fixa,
            protecao=PROTECOES.get(opts.protecao),
            sem_pesos=opts.sem_pesos,
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
