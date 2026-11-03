# Agent guidelines — EON pre-disaster simulator

Undergraduate TCC: a SimPy/NetworkX simulator of an Elastic Optical Network (EON) in the **disaster warning window** (alert received, failure has not happened yet). Several ISPs share one topology, switch to disaster-aware RSA, and migrate a datacenter away from the forecasted failure.

This is **not** post-disaster restoration (DRAMA / Sahoo DCP–carrier). Do not describe the work as BGP/Internet-tier ISP routing.

## Layout

| Path | Role |
|---|---|
| `simulador/` | Live package. Extend this. |
| `simulador/main.py` | `Simulator` — SimPy loop |
| `simulador/config/settings.py` | Global constants |
| `simulador/config/simulation_settings.py` | Immutable `ScenarioConfig` (α, β, γ baked at generation) |
| `simulador/routing/` | RSA algorithms (`RoutingBase`) |
| `simulador/routing/weights.py` | α ISP-share, β migration-path, γ bridges |
| `simulador/coordination/` | Staggered ISP cooperation / weight refresh |
| `simulador/analysis/`, `simulador/visualization/` | Metrics and plots used by notebooks |
| `tests/test_critical_functions.py` | Regression tests — run after simulator changes |
| `topology/usa` | Weighted edgelist (24-node US backbone) |
| `experiment_worker.py` | Multiprocessing worker for weight sweeps (keep out of notebooks) |
| `overleaf/` | Article draft (template still contains leftover NLP sections) |

**Notebooks of record** (do not revive the old copies):

- `Analise_dados_refactored.ipynb` — run two scenarios and plot
- `compare_scenarios2.ipynb` — comparison GUI (batch-aware)
- `Experiment_best_weight_for_scenario.ipynb` — α/β/γ sweep
- `validate_weights.ipynb` — inspect weight geometry

Legacy / do not extend: `Analise_dados.ipynb`, `compare_scenarios.ipynb`, `modeloProblema.ipynb`, `apply_batch_changes.py`, `patch_compare_notebook.py`, unused routers `routing/disaster.py`, `disaster_aware_with_blocking.py`, `best_fit_sliding_window.py`. Root `README.md` still documents deleted `simuladorV2/` — prefer `simulador/README.md`.

`output/` is large local experiment data (csv/pkl gitignored). Do not commit it.

## How the model actually works

- RSA is contiguous **First-Fit** on k-shortest paths, with distance-dependent modulation. Request `class_type` is **not** used in routing.
- **Availability in this repo means `1 - blocking rate`**, not classical two-terminal availability. Say that explicitly.
- Disaster in current runs is typically **one node** (often 9) plus incident links, not Zou’s disk \(D(C_d,R_d)\).
- **Datacenter migration is routed with `FirstFitSubnet`, not the weighted disaster-aware router** (`entities/datacenter.py`). α/β/γ only affect other disaster-aware traffic. Disaster-aware graphs drop the failed node, so they cannot route migrations that **start** at that node without a dedicated variant.
- `MIGRATION_NETWORK_FRACTION` sizes how many migration requests are generated. It does **not** reserve spectrum.
- There is no preemption and no per-class RSA.
- Shared prefix: before the first discovery time all variants behave identically, so `experiment_worker.calcular_prefixo` simulates [0, tau_min) once per base (saved in `output/prefixos/`) and runs started with `prefixo=` resume from the connections active at tau_min. Verified bit-identical to full runs (demand-sized cooperative and First-Fit). Prefixes depend on the base scenario and on any modulation override; delete them if the base scenarios are regenerated.
- Migration destination: `ScenarioConfig.destino_migracao` = "saltos" (farthest node in hops, how the stored scenarios were generated) or "distancia" (farthest in km). `Scenario.redefinir_destinos_migracao` / worker `destino_migracao` / runner `--destino` retarget the pre-generated migration requests; results go to `..._dist` folders. The final experiment and the article use "distancia".
- `ScenarioConfig.pesos_cooperativos=False` (worker `sem_pesos=True`, runner `--sem-pesos`) drops the alpha/beta/gamma weights: routing is plain distance-ordered disaster-aware First-Fit and K only acts through corridor protection. This is the configuration of the final experiment (`Experiment_final.ipynb`, results in `output/cooperation_experiment_v3*`) and of the article (`overleaf/main.tex`, English). In that mode, variants that do not depend on K run once (K = empty set) and are expanded with `cooperation_metrics.expandir_para_todos_k`.
- Optional migration-corridor protection (`simulador/coordination/migration_protection.py`, `ScenarioConfig.protecao_*`): on links of a cooperator's first 3 migration paths that only K members use (mediator discloses sigma(e) = ISPs per link), background traffic is restricted in [tau_i, t_d) by slot reservation (`reserva`) or adaptive blocking (`adaptativo`). Scope `isolado` is the control (sigma(e)=1 links, no cooperation). Only the weighted router applies it. Run via `Experiment_migration_protection.ipynb` or `run_cooperation_experiment.py --protecao <name>`.
- Mode `reserva_demanda` (variants `demanda` / `demanda_isolado`, main path only) reserves per link the slots its owners still need to finish by t_d: ceil(h·(D−M(t))/((t_d−t)·f·12.5)), summed over owners, capped at the link size, 0 once an owner finishes. Experiment: `Experiment_demand_reservation.ipynb`.
- Variants `demanda_corredor` / `demanda_corredor_isolado` use the same sizing on every exclusive link of the first 3 corridor paths; each link uses the modulation factor of the owner's first corridor path through it (`MigrationProtection._fator_link`).
- Background load: `Scenario.reduzir_carga(c)` / worker `fator_carga` keeps a fraction c of the stored background requests (deterministic thinning by `req_id`, nested across c; migration untouched), so lower loads reuse the base scenarios. `run_load_experiment.py` repeats the final experiment at c = 0.5 and 0.75 (folders `..._carga<c>`, prefixes in `output/carga/prefixos/`); `make_load_analysis.py` summarizes all loads and draws `overleaf/figures/load.pdf`.
- Fixed-reservation control of the article: main path only, same links as `demanda_max` (`run_cooperation_experiment.nome_reserva_principal(ρ)`, folders `..._prot-reserva_principal_<ρ>[_carga<c>]`, used by `run_load_experiment.py`, `make_load_analysis.py` and `Experiment_final_v3.ipynb`). The earlier 3-path fixed control (`nome_reserva`) is no longer in the article: with equal scope the demand rule's gap at equal B_n is +1.2 pp, against +4.4 pp versus the 3-path one.
- Candidate paths: stored scenarios hold 3 normal paths per pair (`caminhos_internos_isp`, used before tau_i) and 10 disaster-aware ones. The First-Fit baseline of the article uses 10 normal paths from tau_i on: worker `caminhos_first_fit=10` sets `ISP.caminhos_internos_isp_janela`, which `ISP` swaps in at its discovery time (same 3-path routing before, so prefixes still apply). `run_first_fit_window.py` writes `output/cooperation_experiment_v3_dist_ff10[_carga<c>]/first_fit/`; `make_load_analysis.py` reads First-Fit from there. The old 3-path First-Fit (`..._v3_dist*/first_fit/`) gave +11.5 pp instead of +7.7 pp for disaster-aware routing.
- Network usage (`uso_da_rede` in cooperation_metrics.py) is integrated exactly over [tau_min, t_d) from the accepted connections (plus those restored from the shared prefix): `U`, `U_n` + `U_m` = `U`, `U_protegidos` (links protected at some point, `MigrationProtection.links_ja_protegidos`), `U_links` per link. `montar_tarefas` re-runs any saved run whose JSON lacks a field in `CAMPOS_OBRIGATORIOS`.
- Mode `reserva_feedback` (variants `feedback_l<λ>` / `feedback_isolado_l<λ>`, registered by `nome_feedback`): demand reserve times a per-owner gain g updated every second, g <- g·exp(κ·(atraso − λ·B_n_res − ociosa)). `atraso` is the schedule deficit (accepted vs needed to finish by t_d), not migration blocking: the datacenter offers ~2.7x what it needs, so blocking is high even on schedule. The need is split among the 3 corridor paths by where migration was accepted (moving average), and each link's reserve is capped at 50% (`protecao_reserva_max`). The router now calls `registra_migracao` after allocation with the chosen path (results of the other modes unchanged).
- Background path length `D_n_km` / `H_n` (`caminhos_fundo`): accepted background only, so shorter values can come from long requests being blocked.
- Modulation is distance-based (factor 1–4) unless overridden: `ScenarioConfig.fator_modulacao_fixo` / `Scenario.aplicar_modulacao_fixa(f)` fixes every path's factor (including paths recomputed during cooperation). `run_cooperation_experiment.py --modulacao-fixa f` writes to `output/cooperation_experiment_v2_mod<f>`.
- `FirstFitWeightedSubnetDisasterAware` tries the ISP's precomputed candidates in the order computed on the α/β/γ (cooperation) weighted graph. Before this fix it re-sorted them by static link-usage weights, so α/β/γ and cooperation only changed *which* paths were candidates; results in `output/best_weight_experiment` and `output/cooperation_experiment` predate the fix (v2 lives in `output/cooperation_experiment_v2`).

## Research claims (mandatory)

Current weight-sweep evidence: α/β/γ barely move blocking (~0.02 pp). Migration blocking stays ~59% vs ~32% for normal traffic. Disaster-aware vs not-disaster-aware **does** help migration more than weights do.

**Do not write** that the weighted heuristic prioritizes migration or “works” unless new experiments show a large, stable gap.

Safe claim: *we asked whether cooperative link weights in the warning window change blocking and migration completion; under this model they do not, for reasons X.*

If proposing priority, name a real mechanism: preemption, reserved slots, or routing migration on a (possibly inverted) weighted graph that still includes the source node. Inverted weights only change path order; they do not grant extra spectrum rights.

Literature spine: Rak 2021 (place work in **preparedness**), Zou DRAMA+ (post-disaster EON, contrast), Sahoo GLOBECOM 2022 (post-disaster DCP–carrier, contrast). Cite GLOBECOM as the main Sahoo paper; OFC 2022 is the short version of the same line.

## Coding conventions

- Python 3.12, Poetry (`.venv`), Ruff (double quotes, 88 cols). No wildcard imports.
- Domain class/method names stay **Portuguese** (`rotear_requisicao`, `Desastre`). New modules/files: English `snake_case`.
- New routers: subclass `RoutingBase`, implement `rotear_requisicao` / `rerotear_requisicao`, export in `routing/__init__.py`. Prefer sharing First-Fit allocation instead of copying another 200-line file.
- Scenario parameters that must be comparable across runs go in `ScenarioConfig`, not scattered notebook constants. Traffic is pre-generated; changing α/β/γ requires regenerating weighted paths.
- Keep multiprocessing workers in `.py` files (pickling). After behavior changes, run `pytest tests/test_critical_functions.py`.
- Do not hardcode `WANTED_DISASTER_NODE = 9` or `COMPONENTE_1/2` in new code (`utils/metrics.py` still has leftovers).

## Article (`overleaf/`)

Replace leftover NLP/hemophilia/Reddit sections. Title, abstract, and body must match **this** simulator. State the problem as given / find / such that / under (warning window, multi-ISP local views, staggered cooperation, DC migration, contiguous RSA). Do not invent positive weight-sweep results.
