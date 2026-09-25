"""Worker function for parallel scenario execution.

This module contains the worker function used by ProcessPoolExecutor
to run scenarios in parallel. It's in a separate file to avoid
multiprocessing pickling issues in Jupyter notebooks.
"""

import pickle
from pathlib import Path

from simpy import Environment

from simulador import Metrics
from simulador.main import Simulator


def run_scenario_experiment(args):
    """Run a single scenario and save results.

    Args:
        args: Tuple of (scenario, base_index, scenario_index, total_scenarios, base_output_dir)

    Returns:
        tuple: (success: bool, base_index, alpha, beta, gamma, output_dir)
    """
    scenario, base_index, scenario_index, total_scenarios, base_output_dir = args

    # Get config values
    config = scenario.config
    alpha = config.alpha
    beta = config.beta
    gamma = config.gamma

    # Create directory name
    dir_name = f"{alpha:.1f}_{beta:.1f}_{gamma:.1f}"
    output_dir = Path(base_output_dir) / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # File paths - include base_index in filename
    scenario_path = output_dir / f"scenario_{alpha:.1f}_{beta:.1f}_{gamma:.1f}_{base_index}.pkl"
    dataframe_path = output_dir / f"dataframe_{alpha:.1f}_{beta:.1f}_{gamma:.1f}_{base_index}.csv"

    try:
        print(
            f"[{scenario_index + 1}/{total_scenarios}] Starting: base={base_index}, α={alpha:.1f}, β={beta:.1f}, γ={gamma:.1f}"
        )

        # Reset metrics for this run
        Metrics.reseta_registrador()

        # Create environment and simulator
        env = Environment()
        simulador = Simulator(
            env=env,
            topology=scenario.topology.topology,
            status_logger=False,  # Disable logging for cleaner output
            cenario=scenario,
        )

        # Run simulation
        simulador.run()

        # Save scenario
        with open(scenario_path, "wb") as f:
            pickle.dump(scenario, f)

        # Save dataframe
        df = simulador.salvar_dataframe(str(dataframe_path.with_suffix("")))

        print(
            f"[{scenario_index + 1}/{total_scenarios}] ✓ Completed: base={base_index}, α={alpha:.1f}, β={beta:.1f}, γ={gamma:.1f}"
        )

        return True, base_index, alpha, beta, gamma, str(output_dir)

    except Exception as e:
        print(
            f"[{scenario_index + 1}/{total_scenarios}] ✗ FAILED: base={base_index}, α={alpha:.1f}, β={beta:.1f}, γ={gamma:.1f}"
        )
        print(f"    Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False, base_index, alpha, beta, gamma, str(output_dir)


def metrics_path(
    output_dir: str | Path,
    cooperantes,
    base_index: int,
    variante: str = "cooperacao",
) -> Path:
    """Path of the per-run metrics JSON written by run_cooperation_experiment."""
    from simulador.analysis.cooperation_metrics import rotulo_cooperantes

    rotulo = "first_fit" if variante == "first_fit" else rotulo_cooperantes(cooperantes)
    return Path(output_dir) / rotulo / f"metrics_{rotulo}_{base_index}.json"


def run_cooperation_experiment(args: dict) -> dict:
    """Run one (base scenario, cooperating set K) pair and return its metrics.

    The base scenario is loaded from disk inside the worker, so only a path
    crosses the process boundary (base pickles are ~60 MB each).

    Args:
        args: dict with keys
            base_path: path to the base scenario pickle
            base_index: index of the base scenario
            cooperantes: tuple of ISP IDs in K (may be empty)
            variante: "cooperacao" (default) applies K to a weighted
                disaster-aware scenario; "first_fit" runs the base scenario
                as is (FirstFitSubnet competitor, which ignores K)
            output_dir: directory for this experiment's results
            save_dataframe: also write the per-request CSV (large)
            run_index, total_runs: for progress messages

    Returns:
        dict with ``success``, ``base_index``, ``K``, ``summary`` and ``per_isp``.
        On success the same dict is written to ``metrics_path(...)``.
    """
    import contextlib
    import io

    from simulador import ScenarioGenerator
    from simulador.analysis.cooperation_metrics import (
        metricas_cooperacao,
        rotulo_cooperantes,
    )

    base_index = args["base_index"]
    variante = args.get("variante", "cooperacao")
    cooperantes = () if variante == "first_fit" else tuple(sorted(args["cooperantes"]))
    rotulo = "first_fit" if variante == "first_fit" else rotulo_cooperantes(cooperantes)
    progresso = f"[{args.get('run_index', 0) + 1}/{args.get('total_runs', '?')}]"
    output_dir = Path(args["output_dir"]) / rotulo
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_base = output_dir / f"dataframe_{rotulo}_{base_index}"

    try:
        with open(args["base_path"], "rb") as f:
            base = pickle.load(f)
        if variante == "first_fit":
            scenario = base
        else:
            scenario = ScenarioGenerator.gerar_cenario_com_cooperacao(
                base, cooperantes, copiar=False
            )

        # The weighted router caches link weights per isp_id at class level.
        # Pool workers run many scenarios, so clear it or ISP 0 of one base
        # scenario would be ranked with ISP 0's weights from another.
        from simulador.routing.subnet_weighted_disaster_aware import (
            FirstFitWeightedSubnetDisasterAware as _Weighted,
        )

        _Weighted._link_weights_cache = {}
        _Weighted._migration_weights_cache = None

        Metrics.reseta_registrador()
        env = Environment()
        simulador = Simulator(
            env=env,
            topology=scenario.topology.topology,
            status_logger=False,
            cenario=scenario,
        )
        # Silence the coordinator's per-event prints (hundreds of runs)
        with contextlib.redirect_stdout(io.StringIO()):
            simulador.run()

        if args.get("save_dataframe", False):
            df = simulador.salvar_dataframe(str(csv_base))
        else:
            # criar_dataframe always writes a CSV; send it to a temp file
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                df = simulador.salvar_dataframe(str(Path(tmp) / "df"))

        resumo, por_isp = metricas_cooperacao(df, scenario, cooperantes)
        resumo["base_index"] = base_index
        resumo["variante"] = variante
        for linha in por_isp:
            linha["base_index"] = base_index
            linha["variante"] = variante

        resultado = {
            "success": True,
            "base_index": base_index,
            "K": rotulo,
            "variante": variante,
            "cooperantes": list(cooperantes),
            "summary": resumo,
            "per_isp": por_isp,
        }
        # One small JSON per run so an interrupted sweep can be resumed
        import json

        destino = metrics_path(args["output_dir"], cooperantes, base_index, variante)
        with open(destino, "w") as f:
            json.dump(resultado, f, indent=1)

        print(
            f"{progresso} ✓ base={base_index} {rotulo}: "
            f"eta(K)={resumo['eta_K']:.3f} Gamma={resumo['Gamma']:.3f}"
        )
        return resultado

    except Exception as e:  # noqa: BLE001 - report and keep the sweep running
        import traceback

        print(f"{progresso} ✗ FAILED base={base_index} {rotulo}: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "base_index": base_index,
            "K": rotulo,
            "error": str(e),
        }
