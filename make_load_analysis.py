# Summarizes the final experiment at each background load (run_load_experiment.py)
# and draws overleaf/figures/load.pdf (tables in output/carga/).
# Usage: .venv/bin/python make_load_analysis.py overleaf/figures 0.5 0.75 1
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from run_load_experiment import pastas  # noqa: E402
from run_first_fit_window import pasta as ff_pasta  # noqa: E402
from simulador.analysis.cooperation_metrics import expandir_para_todos_k  # noqa: E402

OUT = Path(sys.argv[1])
CARGAS = [float(c) for c in sys.argv[2:]] or [0.5, 0.75, 1.0]
ERLANGS = 156  # offered background load at fator_carga = 1 (h = 1 s)
T9 = 2.262  # t quantile 0.975, 9 degrees of freedom
I = 5


def ler_carga(carga: float) -> pd.DataFrame:
    linhas = []
    fontes = list(pastas(carga).items()) + [("First-Fit", ff_pasta(carga))]
    for mec, pasta in fontes:
        for arq in sorted(pasta.glob("*/metrics_*.json")):
            r = json.loads(arq.read_text())
            if mec == "sem reserva" and r["K"] == "first_fit":
                continue  # 3-path First-Fit; the paper uses the 10-path re-run
            mec_r = mec
            if mec_r in ("sem reserva", "First-Fit", "demanda individual"):
                if r["K"] not in ("K_none", "first_fit"):
                    continue
                ids = sorted(p["isp_id"] for p in r["per_isp"])
                resumos, _ = expandir_para_todos_k(r, ids)
            else:
                resumos = [r["summary"]]
            linhas += [{**s, "mecanismo": mec_r, "carga": carga} for s in resumos]
    df = pd.DataFrame(linhas)
    ref = df[df.mecanismo == "sem reserva"].set_index(["base_index", "K"])
    for col in ["eta_todos", "B_n", "B_m", "B"]:
        df["d_" + col] = df[col].values - ref.loc[list(zip(df.base_index, df.K)), col].values
    return df


def ic(x):
    x = np.asarray(x, float)
    m, h = x.mean(), T9 * x.std(ddof=1) / np.sqrt(len(x))
    return m, m - h, m + h


def gap_curva_fixa(df: pd.DataFrame) -> pd.Series:
    """eta of cooperative K = I minus the piecewise-linear fixed curve at its B_n.

    The curve joins the reference and the three fixed reservations; beyond the
    largest rho its last segment is extended (np.interp would hold it flat).
    """
    kI = df[df.k == I]
    gaps = {}
    for b, g in kI.groupby("base_index"):
        pts = g[g.mecanismo.isin(["sem reserva", "fixa 25%", "fixa 55%", "fixa 85%"])]
        pts = pts.sort_values("B_n")
        coop = g[g.mecanismo == "demanda cooperativa"].iloc[0]
        x, y = pts.B_n.values, pts.eta_todos.values
        if coop.B_n > x[-1]:  # beyond the largest rho: extend the last segment
            curva = y[-1] + (coop.B_n - x[-1]) * (y[-1] - y[-2]) / (x[-1] - x[-2])
        else:
            curva = np.interp(coop.B_n, x, y)
        gaps[b] = coop.eta_todos - curva
    return pd.Series(gaps)


def adesao(carga: float) -> dict:
    """Joining: provider i in K versus the same run without i, by |K| (Table 3).

    Returns {|K|: (mean delta eta_i, mean delta B_n,i, share of cases where eta_i falls)}.
    """
    eta, bn = {}, {}
    for arq in pastas(carga)["demanda cooperativa"].glob("K_*/metrics_*.json"):
        r = json.loads(arq.read_text())
        grupo = frozenset(r["cooperantes"])
        for p in r["per_isp"]:
            chave = (r["base_index"], grupo, p["isp_id"])
            eta[chave], bn[chave] = p["eta_i"], p["B_n_i"]
    casos = [(len(g), e - eta[(b, g - {i}, i)], bn[(b, g, i)] - bn[(b, g - {i}, i)])
             for (b, g, i), e in eta.items() if i in g]
    d = pd.DataFrame(casos, columns=["k", "d_eta", "d_B_n"]).groupby("k")
    return {k: (g.d_eta.mean(), g.d_B_n.mean(), (g.d_eta < 0).mean()) for k, g in d}


tabela, por_k = [], []
for carga in CARGAS:
    df = ler_carga(carga)
    n = df.groupby("mecanismo").base_index.nunique().to_dict()
    kI = df[df.k == I].set_index(["mecanismo", "base_index"])
    coop, ind, ref = (kI.loc[m] for m in ("demanda cooperativa", "demanda individual", "sem reserva"))
    linha = {"carga": carga, "erlangs": ERLANGS * carga, "n_bases": n}
    for nome, serie in {
        "ref_eta": ref.eta_todos, "ref_B": ref.B, "ref_B_n": ref.B_n, "ref_B_m": ref.B_m,
        "ref_U": ref.U,
        "coop_eta": coop.eta_todos,
        "d_eta_coop": coop.d_eta_todos, "d_B_n_coop": coop.d_B_n,
        "d_eta_ind": ind.d_eta_todos, "coop_menos_ind": coop.eta_todos - ind.eta_todos,
        "d_eta_ff": kI.loc["First-Fit"].d_eta_todos,
        "gap_fixa": gap_curva_fixa(df),
    }.items():
        m, lo, hi = ic(serie)
        linha[nome], linha[nome + "_lo"], linha[nome + "_hi"] = m, lo, hi
    linha["coop_maior_ref"] = int((coop.d_eta_todos > 0).sum())
    linha["coop_maior_ind"] = int((coop.eta_todos > ind.eta_todos).sum())
    linha["gap_positivo"] = int((gap_curva_fixa(df) > 0).sum())
    alem = kI.loc["demanda cooperativa"].B_n > kI.loc["fixa 85%"].B_n
    linha["coop_alem_rho85"] = int(alem.sum())
    curvas = df[(df.k == I) & df.mecanismo.isin(["sem reserva", "fixa 25%", "fixa 55%", "fixa 85%"])]
    concavas = 0
    for _, g in curvas.groupby("base_index"):
        g = g.sort_values("B_n")
        inclin = np.diff(g.eta_todos.values) / np.diff(g.B_n.values)
        concavas += bool(np.all(np.diff(inclin) <= 0))
    linha["curva_fixa_concava"] = concavas
    for k, (de, dbn, cai) in adesao(carga).items():
        linha[f"adesao_d_eta_k{k}"], linha[f"adesao_d_B_n_k{k}"] = de, dbn
        linha[f"adesao_cai_k{k}"] = cai
    tabela.append(linha)
    g = (df[df.mecanismo.isin(["demanda cooperativa", "demanda individual"])]
         .groupby(["mecanismo", "base_index", "k"]).d_eta_todos.mean()
         .groupby(["mecanismo", "k"]).agg(["mean", "std"]).reset_index())
    g["carga"] = carga
    por_k.append(g)

tabela = pd.DataFrame(tabela)
por_k = pd.concat(por_k)
pd.set_option("display.width", 200)
cols = ["carga", "erlangs", "ref_eta", "ref_B", "ref_B_n", "ref_B_m", "ref_U", "d_eta_coop",
        "d_eta_coop_lo", "d_eta_coop_hi", "d_B_n_coop", "d_B_n_coop_lo", "d_B_n_coop_hi",
        "d_eta_ind", "d_eta_ind_lo", "d_eta_ind_hi", "coop_menos_ind", "coop_menos_ind_lo",
        "coop_menos_ind_hi", "d_eta_ff", "gap_fixa", "gap_fixa_lo", "gap_fixa_hi",
        "coop_maior_ref", "coop_maior_ind", "gap_positivo", "curva_fixa_concava"]
print(tabela[["n_bases"]].to_string())
print(tabela[cols].round(4).T.to_string())
print(por_k.pivot_table(index=["mecanismo", "k"], columns="carga", values="mean").mul(100).round(2))
Path("output/carga").mkdir(parents=True, exist_ok=True)
tabela.to_csv("output/carga/load_summary.csv", index=False)
por_k.to_csv("output/carga/load_gain_by_k.csv", index=False)

# Figure: gain vs |K| per load (the K = I numbers are in the paper's Table 4)
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.labelsize": 9,
                     "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "pdf.fonttype": 42, "mathtext.fontset": "cm", "font.serif": ["cmr10"],
                     "axes.formatter.use_mathtext": True, "axes.unicode_minus": False})
TXT, GRID = "#3d3c39", "#e5e4df"
CORES = {0.5: "#6baed6", 0.75: "#2171b5", 1.0: "#08306b"}

fig, ax = plt.subplots(figsize=(3.95, 2.7))
ax.axhline(0, color=TXT, lw=0.8)
for carga in CARGAS:
    cor = CORES.get(carga, "#2a78d6")
    marca = {0.5: "^", 0.75: "s", 1.0: "o"}.get(carga, "o")
    for mec, ls, mk in (("demanda cooperativa", "-", marca), ("demanda individual", "--", None)):
        s = por_k[(por_k.carga == carga) & (por_k.mecanismo == mec)]
        ax.plot(s.k, s["mean"] * 100, ls, color=cor, lw=1.6, marker=mk, ms=3.5,
                label=f"{ERLANGS * carga:.0f} Erlangs" if mec == "demanda cooperativa" else None)
ax.set_xticks(range(I + 1))
ax.legend(frameon=False, loc="upper left", title="cooperative (solid)\nindividual (dashed)",
          title_fontsize=8)
ax.set_xlabel(r"$|K|$ (cooperating providers)", color=TXT)
ax.set_ylabel(r"$\Delta\eta$ (pp)", color=TXT)
ax.tick_params(colors=TXT)
ax.grid(axis="y", color=GRID, lw=0.7)
for lado in ("top", "right"):
    ax.spines[lado].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "load.pdf", bbox_inches="tight")
