"""Run the cooperating-set (K) experiment from the command line.

For every base scenario it runs all 2^I cooperating sets K on the weighted
disaster-aware scenario (output/cenario_disaster_aware{i}.pkl) plus one run of
the First-Fit competitor on the same instance
(output/cenario_nao_disaster_aware{i}.pkl). Finished runs are skipped, so the
command can be interrupted and restarted.

Usage:
    poetry run python run_cooperation_experiment.py --bases 0
    poetry run python run_cooperation_experiment.py --bases 0 1 2 --workers 6
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

COOP_PATH = "output/cenario_disaster_aware{i}.pkl"
FIRST_FIT_PATH = "output/cenario_nao_disaster_aware{i}.pkl"


def montar_tarefas(
    bases: list[int], output_dir: Path, first_fit: bool = True
) -> list[dict]:
    """List the pending runs (all K per base + First-Fit), skipping finished ones."""
    tarefas = []
    for i in bases:
        coop_path = COOP_PATH.format(i=i)
        with open(coop_path, "rb") as f:
            isp_ids = sorted(isp.isp_id for isp in pickle.load(f).lista_de_isps)
        subconjuntos = [
            c for k in range(len(isp_ids) + 1) for c in combinations(isp_ids, k)
        ]
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
    parser.add_argument("--output", default="output/cooperation_experiment_v2")
    parser.add_argument("--no-first-fit", action="store_true")
    opts = parser.parse_args()

    output_dir = Path(opts.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    tarefas = montar_tarefas(opts.bases, output_dir, not opts.no_first_fit)
    for idx, t in enumerate(tarefas):
        t.update(output_dir=str(output_dir), run_index=idx, total_runs=len(tarefas))

    print(f"{len(tarefas)} runs pending | bases {opts.bases} | {opts.workers} processes")
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
