# Base scenarios

`cenario_disaster_aware<i>.pkl` and `cenario_nao_disaster_aware<i>.pkl`
(i = 0..9) are the 10 base scenarios of the article: topology, provider
overlays, disaster, discovery times and the pre-generated background and
migration traffic. The `nao_disaster_aware` copy holds the same traffic for
the First-Fit baseline. The scenario generator had no fixed seed, so these
files cannot be regenerated: keep them unchanged.

The unnumbered `cenario_disaster_aware.pkl` / `cenario_nao_disaster_aware.pkl`
are the single scenario used by `Analise_dados_refactored.ipynb` and
`validate_weights.ipynb`.

Everything else in `output/` is derived: the shared prefixes
(`prefixos/`, `carga/prefixos/`) are rebuilt by the runners on the first run,
and the summary CSVs by `make_load_analysis.py`, `make_warning_analysis.py`
and `Experiment_final_v3.ipynb` from the per-run JSONs.
