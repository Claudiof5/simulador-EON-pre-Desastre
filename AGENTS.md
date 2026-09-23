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
