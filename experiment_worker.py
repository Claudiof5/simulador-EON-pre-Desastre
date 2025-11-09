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
        args: Tuple of (scenario, scenario_index, total_scenarios, base_output_dir)

    Returns:
        tuple: (success: bool, alpha, beta, gamma, output_dir)
    """
    scenario, scenario_index, total_scenarios, base_output_dir = args

    # Get config values
    config = scenario.config
    alpha = config.alpha
    beta = config.beta
    gamma = config.gamma

    # Create directory name
    dir_name = f"{alpha:.1f}_{beta:.1f}_{gamma:.1f}"
    output_dir = Path(base_output_dir) / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # File paths
    scenario_path = output_dir / f"scenario_{alpha:.1f}_{beta:.1f}_{gamma:.1f}.pkl"
    dataframe_path = output_dir / f"dataframe_{alpha:.1f}_{beta:.1f}_{gamma:.1f}.csv"

    try:
        print(
            f"[{scenario_index + 1}/{total_scenarios}] Starting: α={alpha:.1f}, β={beta:.1f}, γ={gamma:.1f}"
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
            f"[{scenario_index + 1}/{total_scenarios}] ✓ Completed: α={alpha:.1f}, β={beta:.1f}, γ={gamma:.1f}"
        )

        return True, alpha, beta, gamma, str(output_dir)

    except Exception as e:
        print(
            f"[{scenario_index + 1}/{total_scenarios}] ✗ FAILED: α={alpha:.1f}, β={beta:.1f}, γ={gamma:.1f}"
        )
        print(f"    Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False, alpha, beta, gamma, str(output_dir)
