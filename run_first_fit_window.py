"""Re-run the First-Fit baseline with 10 candidate paths in the warning window.

The stored First-Fit scenarios precompute 3 candidate paths per node pair,
while the disaster-aware variants use 10. Here each ISP keeps its 3 paths
before its discovery time (as in every other variant, so the shared prefixes
still apply) and switches to the 10 shortest paths of its overlay from tau_i
on (experiment_worker caminhos_first_fit). Results go to
output/cooperation_experiment_v3_dist_ff10[_carga<c>]/first_fit/.

Usage:
    .venv/bin/python run_first_fit_window.py
"""

from __future__ import annotations

import argparse
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from experiment_worker import metrics_path, prefixo_path, run_cooperation_experiment
from run_cooperation_experiment import FIRST_FIT_PATH, pasta_saida, resultado_completo
from run_load_experiment import DESTINO, RAIZ_PREFIXOS

K_JANELA = 10


def pasta(carga: float) -> Path:
    sufixo = "" if carga == 1 else f"_carga{carga:g}"
    return Path(f"{pasta_saida(None, None, True, DESTINO)}_ff{K_JANELA}{sufixo}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cargas", type=float, nargs="+", default=[1.0, 0.75, 0.5])
    parser.add_argument("--bases", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--workers", type=int, default=min(os.cpu_count() or 4, 12))
    opts = parser.parse_args()

    tarefas = []
    for carga in opts.cargas:
        saida = pasta(carga)
        for b in opts.bases:
            if resultado_completo(metrics_path(saida, (), b, "first_fit")):
                continue
            prefixo = (prefixo_path("output", b) if carga == 1
                       else prefixo_path(RAIZ_PREFIXOS, b, None, carga))
            tarefas.append({
                "base_path": FIRST_FIT_PATH.format(i=b), "base_index": b,
                "cooperantes": (), "variante": "first_fit", "output_dir": str(saida),
                "sem_pesos": True, "destino_migracao": DESTINO, "recortar_janela": True,
                "fator_carga": None if carga == 1 else carga, "prefixo": str(prefixo),
                "caminhos_first_fit": K_JANELA,
            })
    print(f"{len(tarefas)} runs pending", flush=True)
    with ProcessPoolExecutor(max_workers=opts.workers) as executor:
        falhas = sum(not r["success"] for r in executor.map(run_cooperation_experiment, tarefas))
    print(f"failures: {falhas}", flush=True)


if __name__ == "__main__":
    main()
