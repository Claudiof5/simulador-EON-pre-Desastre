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
            fator_modulacao_fixo: fixed modulation factor for every path, or
                None (default) for distance-based modulation
            protecao: dict of ScenarioConfig ``protecao_*`` overrides enabling
                migration-corridor protection, or None (default) for none
            sem_pesos: True drops the cooperative alpha/beta/gamma weights
                (plain distance-ordered disaster-aware First-Fit)
            recortar_janela: True ends the simulation at t_d (drops the
                requests created afterwards; faster, same metrics)
            prefixo: path of a prefix file from calcular_prefixo; the run then
                starts at the first discovery time from the saved state
                (same results, shorter run)
            caminhos_first_fit: with variante "first_fit", number of candidate
                paths each ISP uses from its discovery time on (None keeps the
                stored 3)
            aviso_compartilhado: True makes every ISP react at the first
                discovery time (Scenario.aviso_compartilhado)
            fator_carga: keep this fraction of the background requests
                (Scenario.reduzir_carga), or None (default) for all of them
            destino_migracao: "saltos" or "distancia" re-chooses each ISP's
                migration destination (farthest in hops or in km); None keeps
                the destination stored in the scenario
            run_index, total_runs: for progress messages

    Returns:
        dict with ``success``, ``base_index``, ``K``, ``summary`` and ``per_isp``.
        On success the same dict is written to ``metrics_path(...)``.
    """
    import contextlib
    import io

    from simulador import ScenarioGenerator
    from simulador.analysis.cooperation_metrics import (
        caminhos_fundo,
        metricas_cooperacao,
        rotulo_cooperantes,
        uso_da_rede,
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
        if args.get("recortar_janela"):
            # Stop at the failure: metrics ignore later requests
            base.recortar_janela()
        fator_carga = args.get("fator_carga")
        if fator_carga is not None:
            base.reduzir_carga(fator_carga)
        destino = args.get("destino_migracao")
        if destino is not None:
            base.redefinir_destinos_migracao(destino)
        if args.get("aviso_compartilhado"):
            # First ISP to discover warns the others: all react at tau_min
            base.aviso_compartilhado(semente=base_index)
        fator_fixo = args.get("fator_modulacao_fixo")
        if fator_fixo is not None:
            base.aplicar_modulacao_fixa(fator_fixo)
        overrides = dict(args.get("protecao") or {})
        if args.get("sem_pesos"):
            overrides["pesos_cooperativos"] = False
        if overrides and variante != "first_fit":
            from simulador.config.simulation_settings import ScenarioConfig

            base.config = (base.config or ScenarioConfig()).copy_with(**overrides)
        if variante == "first_fit":
            scenario = base
            k_janela = args.get("caminhos_first_fit")
            if k_janela:
                # Same First-Fit before tau_i; k_janela candidates from tau_i on
                grafo = scenario.topology.topology
                for isp in scenario.lista_de_isps:
                    antes = isp.caminhos_internos_isp
                    isp.computar_caminhos_internos(grafo, k_janela)
                    isp.caminhos_internos_isp_janela = isp.caminhos_internos_isp
                    isp.caminhos_internos_isp = antes
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

        # Read by the router (Topology object shared with the simulator)
        scenario.topology.migracao_last_fit = bool(
            getattr(scenario.config, "migracao_last_fit", False)
        )
        saidas = getattr(scenario.config, "migracao_saidas_distintas", None)
        saidas_distintas = (
            scenario.diversificar_saidas_migracao(saidas) if saidas else None
        )

        prefixo = None
        if args.get("prefixo"):
            # Resume from the shared prefix: start at tau_min with the
            # connections that were active then (see calcular_prefixo)
            with open(args["prefixo"], "rb") as f:
                prefixo = pickle.load(f)
            _checar_prefixo(prefixo, scenario, fator_fixo, fator_carga)
            scenario.lista_de_requisicoes = [
                r
                for r in scenario.lista_de_requisicoes or []
                if r.tempo_criacao >= prefixo["tau_min"]
            ]

        Metrics.reseta_registrador()
        env = Environment(initial_time=prefixo["tau_min"] if prefixo else 0)
        simulador = Simulator(
            env=env,
            topology=scenario.topology.topology,
            status_logger=False,
            cenario=scenario,
        )
        if prefixo:
            _restaurar_conexoes(simulador, prefixo)
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
        resumo["fator_modulacao_fixo"] = fator_fixo
        resumo["sem_pesos"] = bool(args.get("sem_pesos"))
        resumo["destino_migracao"] = destino or "saltos"
        resumo["recortar_janela"] = bool(args.get("recortar_janela"))
        resumo["prefixo"] = bool(prefixo)
        resumo["fator_carga"] = fator_carga
        resumo["aviso_compartilhado"] = bool(args.get("aviso_compartilhado"))
        resumo["caminhos_first_fit"] = args.get("caminhos_first_fit")
        prot = getattr(simulador.topology, "protecao_migracao", None)
        resumo["protecao"] = (
            None if prot is None else f"{prot.modo}/{prot.escopo}"
        )
        resumo["migracao_last_fit"] = bool(getattr(scenario.topology, "migracao_last_fit", False))
        resumo["saidas_distintas"] = (
            None if saidas_distintas is None else {str(k): v for k, v in saidas_distintas.items()}
        )
        resumo["prot_max_links"] = None if prot is None else prot.max_links_protegidos
        resumo["prot_normais_restringidas"] = (
            None if prot is None else prot.normais_restringidas
        )
        resumo["prot_reserva_media_slots"] = (
            None if prot is None else prot.reserva_media_slots
        )
        # Spectrum usage in [tau_min, t_d), counting connections restored from
        # the shared prefix so resumed and full runs give the same value
        tau_min = min(
            isp.datacenter.tempo_de_reacao
            for isp in scenario.lista_de_isps
            if isp.datacenter is not None
        )
        uso = uso_da_rede(
            Metrics.get_intance().requisicoes,
            simulador.topology.topology,
            tau_min,
            scenario.desastre.start,
            conexoes_iniciais=prefixo["ativas"] if prefixo else (),
            links_protegidos=() if prot is None else prot.links_ja_protegidos,
        )
        resumo["U_links"] = uso.pop("U_links")
        resumo.update(uso)
        taus = {
            isp.isp_id: isp.datacenter.tempo_de_reacao
            for isp in scenario.lista_de_isps
            if isp.datacenter is not None
        }
        resumo.update(
            caminhos_fundo(
                Metrics.get_intance().requisicoes, taus, scenario.desastre.start
            )
        )
        resumo["prot_ganho_medio"] = None if prot is None else prot.ganho_medio
        resumo["prot_historico_ganho"] = (
            None
            if prot is None or not prot.historico_ganho
            else [[t, {str(k): g for k, g in gs.items()}] for t, gs in prot.historico_ganho]
        )
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

# ---------------------------------------------------------------------------
# Shared prefix: every variant behaves the same before the first ISP reacts
# (same traffic, plain First-Fit, no cooperation or reservation). It is
# simulated once per base scenario; each run then starts at tau_min with the
# connections that were active at that instant. Metrics only use requests
# created after the discovery times, so results are unchanged.
# ---------------------------------------------------------------------------


def _assinatura(scenario) -> dict:
    reqs = scenario.lista_de_requisicoes or []
    taus = [
        isp.datacenter.tempo_de_reacao
        for isp in scenario.lista_de_isps
        if isp.datacenter is not None
    ]
    return {
        "tau_min": min(taus),
        "t_d": scenario.desastre.start,
        "isps": [sorted(isp.nodes) for isp in scenario.lista_de_isps],
    }


def calcular_prefixo(
    base_path: str | Path,
    destino: str | Path,
    fator_modulacao_fixo: float | None = None,
    fator_carga: float | None = None,
) -> Path:
    """Simulate [0, tau_min) once and save the connections active at tau_min.

    Args:
        base_path: base scenario pickle (cenario_disaster_aware{i}.pkl)
        destino: where to write the prefix file
        fator_modulacao_fixo: must match the runs that will use the prefix
        fator_carga: background fraction kept; must match the runs too

    Returns:
        Path of the prefix file.
    """
    with open(base_path, "rb") as f:
        base = pickle.load(f)
    if fator_modulacao_fixo is not None:
        base.aplicar_modulacao_fixa(fator_modulacao_fixo)
    if fator_carga is not None:
        base.reduzir_carga(fator_carga)
    assinatura = _assinatura(base)
    tau_min = assinatura["tau_min"]
    n_total = len(base.lista_de_requisicoes or [])
    base.lista_de_requisicoes = [
        r for r in base.lista_de_requisicoes or [] if r.tempo_criacao < tau_min
    ]

    Metrics.reseta_registrador()
    env = Environment()
    simulador = Simulator(
        env=env, topology=base.topology.topology, status_logger=False, cenario=base
    )
    import contextlib
    import io

    with contextlib.redirect_stdout(io.StringIO()):
        env.process(simulador._run())
        env.run(until=tau_min)

    ativas = [
        (
            list(r.caminho),
            tuple(r.index_de_inicio_e_final),
            float(r.tempo_desalocacao),
        )
        for r in Metrics.get_intance().requisicoes
        if r.bloqueada is False
        and r.tempo_desalocacao is not None
        and r.tempo_desalocacao > tau_min
    ]

    # The saved connections must explain the occupancy exactly
    g = simulador.topology.topology
    ocupacao = {
        frozenset((u, v)): [0] * len(d["slots"]) for u, v, d in g.edges(data=True)
    }
    for caminho, (ini, fim), _ in ativas:
        for u, v in zip(caminho, caminho[1:]):
            for slot in range(ini, fim + 1):
                ocupacao[frozenset((u, v))][slot] = 1
    for u, v, d in g.edges(data=True):
        if list(d["slots"]) != ocupacao[frozenset((u, v))]:
            raise RuntimeError(f"prefix occupancy mismatch on link {(u, v)}")

    prefixo = {
        **assinatura,
        "n_requisicoes_total": n_total,
        "fator_modulacao_fixo": fator_modulacao_fixo,
        "fator_carga": fator_carga,
        "ativas": ativas,
    }
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "wb") as f:
        pickle.dump(prefixo, f)
    return destino


def _checar_prefixo(
    prefixo: dict, scenario, fator_modulacao_fixo, fator_carga=None
) -> None:
    assinatura = _assinatura(scenario)
    for chave in ("tau_min", "t_d", "isps"):
        if prefixo[chave] != assinatura[chave]:
            raise ValueError(f"prefix does not match this scenario ({chave})")
    if prefixo.get("fator_modulacao_fixo") != fator_modulacao_fixo:
        raise ValueError("prefix was computed with a different modulation setting")
    if prefixo.get("fator_carga") != fator_carga:
        raise ValueError("prefix was computed with a different background load")


def _restaurar_conexoes(simulador, prefixo: dict) -> None:
    """Re-create the connections active at tau_min, released at their own time."""
    topologia = simulador.topology
    env = simulador.env
    for caminho, (ini, fim), t_fim in prefixo["ativas"]:
        topologia.aloca_janela(caminho, (ini, fim))
        env.process(
            topologia.desaloca_janela(caminho, (ini, fim), t_fim - env.now, env)
        )


def prefixo_path(
    output_root: str | Path, base_index: int, fator=None, fator_carga=None
) -> Path:
    """Default location of the prefix file of a base scenario."""
    sufixo = "" if fator is None else f"_mod{fator:g}"
    if fator_carga is not None:
        sufixo += f"_carga{fator_carga:g}"
    return Path(output_root) / "prefixos" / f"prefixo_base{base_index}{sufixo}.pkl"
