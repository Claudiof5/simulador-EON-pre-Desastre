# Summarizes the shared-warning experiment (run_shared_warning.py): every ISP
# reacts at the first discovery time, against the stored discovery times.
# Writes output/carga/warning_summary.csv and prints the 2x2 effects per load.
# Usage: .venv/bin/python make_warning_analysis.py
import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_shared_warning import pasta as pasta_aviso
from run_load_experiment import pastas

T9 = 2.262  # t quantile 0.975, 9 degrees of freedom
BASES = range(10)
CHAVE = {"sem reserva": "K_none", "demanda individual": "K_none",
         "demanda cooperativa": "K_0-1-2-3-4"}
PROTECAO = {"sem reserva": None, "demanda individual": "demanda_isolado",
            "demanda cooperativa": "demanda_max"}


def ler(pasta: Path, chave: str) -> list[dict]:
    return [json.loads((pasta / chave / f"metrics_{chave}_{b}.json").read_text())
            for b in BASES]


def resumo(runs: list[dict]) -> dict:
    s = [r["summary"] for r in runs]
    fim = [np.mean([p["eta_i"] >= 1 - 1e-9 for p in r["per_isp"]]) for r in runs]
    return {"eta": np.array([x["eta_todos"] for x in s]),
            "B_n": np.array([x["B_n"] for x in s]),
            "B_m": np.array([x["B_m"] for x in s]),
            "completam": np.array(fim)}


def ic(d):
    d = np.asarray(d) * 100
    h = T9 * d.std(ddof=1) / np.sqrt(len(d))
    return d.mean(), d.std(ddof=1), d.mean() - h, d.mean() + h, int((d > 0).sum())


linhas = []
for carga in (1.0, 0.75, 0.5):
    proprio = {m: resumo(ler(pastas(carga)[m], CHAVE[m])) for m in CHAVE}
    aviso = {m: resumo(ler(pasta_aviso(PROTECAO[m], carga), CHAVE[m])) for m in CHAVE}
    ref, ref_a = proprio["sem reserva"], aviso["sem reserva"]
    coop, coop_a = proprio["demanda cooperativa"], aviso["demanda cooperativa"]
    efeitos = {
        "warning alone (ref_aviso - ref)": ref_a["eta"] - ref["eta"],
        "cooperation, own times (coop - ref)": coop["eta"] - ref["eta"],
        "cooperation, shared warning (coop_aviso - ref_aviso)": coop_a["eta"] - ref_a["eta"],
        "both (coop_aviso - ref)": coop_a["eta"] - ref["eta"],
        "individual, shared warning (ind_aviso - ref_aviso)":
            aviso["demanda individual"]["eta"] - ref_a["eta"],
        "dB_n cooperation, shared warning": coop_a["B_n"] - ref_a["B_n"],
    }
    for nome, d in efeitos.items():
        m, sd, lo, hi, pos = ic(d)
        linhas.append({"carga": carga, "efeito": nome, "media_pp": m, "dp_pp": sd,
                       "ic_lo": lo, "ic_hi": hi, "positivos": pos})
    for rot, grupo in (("own", proprio), ("warning", aviso)):
        for m, r in grupo.items():
            linhas.append({"carga": carga, "efeito": f"level {rot} {m}",
                           "media_pp": r["eta"].mean() * 100,
                           "completam": r["completam"].mean(),
                           "B_n": r["B_n"].mean(), "B_m": r["B_m"].mean()})

df = pd.DataFrame(linhas)
Path("output/carga").mkdir(parents=True, exist_ok=True)
df.to_csv("output/carga/warning_summary.csv", index=False)
pd.set_option("display.width", 200)
print(df.round(3).to_string(index=False))
