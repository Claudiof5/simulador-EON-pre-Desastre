"""Shared warning: the first ISP to discover the threat warns the others.

Every ISP reacts at tau_min (Scenario.aviso_compartilhado), with its migration
stream extended back to tau_min. Runs, for each background load, the reference
(no reservation), individual protection and the cooperative demand-driven
reservation with all ISPs (K = I). Results go to the usual folders with the
suffix _aviso (before any _carga suffix).

Usage:
    .venv/bin/python run_shared_warning.py
"""

from __future__ import annotations

import argparse
import os
import pickle
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from experiment_worker import metrics_path, prefixo_path, run_cooperation_experiment
from run_cooperation_experiment import COOP_PATH, PROTECOES, pasta_saida, resultado_completo
from run_load_experiment import DESTINO, RAIZ_PREFIXOS

VARIANTES = {
    "sem reserva": (None, False),
    "demanda individual": ("demanda_isolado", False),
    "demanda cooperativa": ("demanda_max", True),
}


def pasta(protecao: str | None, carga: float) -> Path:
    sufixo = "" if carga == 1 else f"_carga{carga:g}"
    return Path(f"{pasta_saida(None, protecao, True, DESTINO)}_aviso{sufixo}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cargas", type=float, nargs="+", default=[1.0, 0.75, 0.5])
    parser.add_argument("--bases", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--workers", type=int, default=min(os.cpu_count() or 4, 12))
    opts = parser.parse_args()

    tarefas = []
    for carga in opts.cargas:
        for protecao, todos in VARIANTES.values():
            saida = pasta(protecao, carga)
            for b in opts.bases:
                with open(COOP_PATH.format(i=b), "rb") as f:
                    ids = tuple(sorted(i.isp_id for i in pickle.load(f).lista_de_isps))
                k = ids if todos else ()
                if resultado_completo(metrics_path(saida, k, b)):
                    continue
                prefixo = (prefixo_path("output", b) if carga == 1
                           else prefixo_path(RAIZ_PREFIXOS, b, None, carga))
                tarefas.append({
                    "base_path": COOP_PATH.format(i=b), "base_index": b,
                    "cooperantes": k, "variante": "cooperacao", "output_dir": str(saida),
                    "protecao": None if protecao is None else PROTECOES[protecao],
                    "sem_pesos": True, "destino_migracao": DESTINO, "recortar_janela": True,
                    "fator_carga": None if carga == 1 else carga, "prefixo": str(prefixo),
                    "aviso_compartilhado": True,
                })
    print(f"{len(tarefas)} runs pending", flush=True)
    with ProcessPoolExecutor(max_workers=opts.workers) as executor:
        falhas = sum(not r["success"] for r in executor.map(run_cooperation_experiment, tarefas))
    print(f"failures: {falhas}", flush=True)


if __name__ == "__main__":
    main()
