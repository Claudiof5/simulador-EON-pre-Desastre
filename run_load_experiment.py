"""Repeat the final experiment (Experiment_final_v3.ipynb) at lower background loads.

The fixed reservation is the main-path one (nome_reserva_principal); with
--cargas 1 only those runs are missing at full load, so only they are run.

Each load keeps a fraction of the background requests of the stored base
scenarios (Scenario.reduzir_carga); migration traffic, overlays, disaster and
discovery times are unchanged. The full load (1.0) is the final experiment
itself, in output/cooperation_experiment_v3_dist*. Results of a load c go to
the same folders with the suffix _carga<c>, and its shared prefixes to
output/carga/prefixos/.

Usage:
    .venv/bin/python run_load_experiment.py --cargas 0.5 0.75
"""

from __future__ import annotations

import argparse
import os
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from experiment_worker import (
    calcular_prefixo,
    metrics_path,
    prefixo_path,
    run_cooperation_experiment,
)
from run_cooperation_experiment import (
    COOP_PATH,
    PROTECOES,
    montar_tarefas,
    nome_reserva_principal,
    pasta_saida,
    resultado_completo,
)

DESTINO = "distancia"
FIXAS = [25, 55, 85]
RAIZ_PREFIXOS = "output/carga"


def pastas(carga: float) -> dict[str, Path]:
    """Results folders of one load (same layout as the final experiment)."""
    sufixo = "" if carga == 1 else f"_carga{carga:g}"

    def p(protecao):
        return Path(f"{pasta_saida(None, protecao, True, DESTINO)}{sufixo}")

    return {
        "sem reserva": p(None),
        "demanda cooperativa": p("demanda_max"),
        "demanda individual": p("demanda_isolado"),
        **{f"fixa {f}%": p(nome_reserva_principal(f)) for f in FIXAS},
    }


def tarefas_da_carga(carga: float, bases: list[int]) -> list[dict]:
    ids = {}
    for b in bases:
        with open(COOP_PATH.format(i=b), "rb") as f:
            ids[b] = tuple(sorted(isp.isp_id for isp in pickle.load(f).lista_de_isps))
    pp = pastas(carga)
    comum = {"sem_pesos": True, "destino_migracao": DESTINO, "recortar_janela": True,
             "fator_carga": None if carga == 1 else carga}
    tarefas = []

    def completar(lista, pasta, protecao):
        pasta.mkdir(parents=True, exist_ok=True)
        for t in lista:
            t.update(output_dir=str(pasta), protecao=protecao, **comum)
        tarefas.extend(lista)

    completar(montar_tarefas(bases, pp["sem reserva"], first_fit=True, somente_k_vazio=True),
              pp["sem reserva"], None)
    completar(montar_tarefas(bases, pp["demanda cooperativa"], first_fit=False),
              pp["demanda cooperativa"], PROTECOES["demanda_max"])
    completar(montar_tarefas(bases, pp["demanda individual"], first_fit=False,
                             somente_k_vazio=True),
              pp["demanda individual"], PROTECOES["demanda_isolado"])
    for f in FIXAS:
        pasta = pp[f"fixa {f}%"]
        pasta.mkdir(parents=True, exist_ok=True)
        for b in bases:
            if not resultado_completo(metrics_path(pasta, ids[b], b)):
                tarefas.append({"base_path": COOP_PATH.format(i=b), "base_index": b,
                                "cooperantes": ids[b], "variante": "cooperacao",
                                "output_dir": str(pasta),
                                "protecao": PROTECOES[nome_reserva_principal(f)], **comum})
    return tarefas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cargas", type=float, nargs="+", default=[0.5, 0.75])
    parser.add_argument("--bases", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--workers", type=int, default=min(os.cpu_count() or 4, 8))
    opts = parser.parse_args()

    tarefas = []
    for carga in opts.cargas:
        if not 0 < carga <= 1:
            raise SystemExit("use loads in (0, 1]")
        prefixos = {}
        for b in opts.bases:
            caminho = (prefixo_path("output", b) if carga == 1
                       else prefixo_path(RAIZ_PREFIXOS, b, None, carga))
            if not caminho.exists():
                calcular_prefixo(COOP_PATH.format(i=b), caminho, None,
                                 None if carga == 1 else carga)
            prefixos[b] = str(caminho)
        for t in tarefas_da_carga(carga, opts.bases):
            t["prefixo"] = prefixos[t["base_index"]]
            tarefas.append(t)
    for i, t in enumerate(tarefas):
        t.update(run_index=i, total_runs=len(tarefas))

    print(f"{len(tarefas)} runs pending | loads {opts.cargas} | {opts.workers} processes",
          flush=True)
    inicio = datetime.now()
    falhas = 0
    with ProcessPoolExecutor(max_workers=opts.workers) as executor:
        futures = [executor.submit(run_cooperation_experiment, t) for t in tarefas]
        for future in as_completed(futures):
            falhas += not future.result()["success"]
    print(f"Done in {datetime.now() - inicio} | failures: {falhas}", flush=True)


if __name__ == "__main__":
    main()
