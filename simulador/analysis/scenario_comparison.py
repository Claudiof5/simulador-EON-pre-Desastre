"""Scenario comparison analysis utilities.

This module provides functions for loading and comparing simulation scenarios,
including data loading, filtering, and metric calculations.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from simulador.analysis import dataframe_filters

if TYPE_CHECKING:
    from simulador.entities.scenario import Scenario


def load_scenario_pair(scenario1_name: str, scenario2_name: str) -> dict:
    """Load both scenarios and their corresponding dataframes.

    Args:
        scenario1_name: Name of first scenario (without .pkl extension)
        scenario2_name: Name of second scenario (without .pkl extension)

    Returns:
        Dictionary containing:
            - scenario1: First Scenario object
            - scenario2: Second Scenario object
            - df1: First scenario's dataframe
            - df2: Second scenario's dataframe
            - disaster_start: Disaster start time
            - disaster_end: Disaster end time
            - migration_times: Dict mapping ISP ID to migration start time
            - disaster_node: Node affected by disaster
    """
    output_path = Path("output")

    # Load scenarios
    scenario1_path = output_path / f"{scenario1_name}.pkl"
    scenario2_path = output_path / f"{scenario2_name}.pkl"

    with open(scenario1_path, "rb") as f:
        scenario1: Scenario = pickle.load(f)

    with open(scenario2_path, "rb") as f:
        scenario2: Scenario = pickle.load(f)

    # Load dataframes
    df1_path = output_path / f"df_{scenario1_name}.csv"
    df2_path = output_path / f"df_{scenario2_name}.csv"

    df1 = pd.read_csv(df1_path, index_col=0, low_memory=False)
    df2 = pd.read_csv(df2_path, index_col=0, low_memory=False)

    # Extract timing information from scenario 1 (both scenarios should have same timing)
    disaster_start = scenario1.desastre.start
    disaster_end = scenario1.desastre.start + scenario1.desastre.duration

    # Extract migration start times for each ISP
    migration_times = {}
    for isp in scenario1.lista_de_isps:
        if isp.datacenter is not None:
            migration_times[isp.isp_id] = isp.datacenter.tempo_de_reacao

    # Get disaster node
    disaster_node = None
    if scenario1.desastre.list_of_dict_node_per_start_time:
        disaster_node = scenario1.desastre.list_of_dict_node_per_start_time[0]["node"]

    return {
        "scenario1": scenario1,
        "scenario2": scenario2,
        "df1": df1,
        "df2": df2,
        "disaster_start": disaster_start,
        "disaster_end": disaster_end,
        "migration_times": migration_times,
        "disaster_node": disaster_node,
    }


def apply_filter(df: pd.DataFrame, filter_type: str, **kwargs) -> pd.DataFrame:
    """Apply selected filter to dataframe.

    Args:
        df: Input dataframe
        filter_type: Type of filter to apply ('No Filter', 'Migration Traffic Only',
                    'Exclude Migration Traffic', 'By ISP', 'By Node')
        **kwargs: Additional filter parameters (isp_id, node)

    Returns:
        Filtered dataframe
    """
    if filter_type == "No Filter":
        return df.copy()

    if filter_type == "Migration Traffic Only":
        return df[df["requisicao_de_migracao"]].copy()

    if filter_type == "Exclude Migration Traffic":
        return df[~df["requisicao_de_migracao"]].copy()

    if filter_type == "By ISP":
        isp_id = kwargs.get("isp_id")
        return df[
            (df["src_isp_index"] == isp_id) | (df["dst_isp_index"] == isp_id)
        ].copy()

    if filter_type == "By Node":
        node = kwargs.get("node")
        return dataframe_filters.filter_by_node(df, node)

    return df.copy()


def calculate_blocking_probability_over_time(
    df: pd.DataFrame, bucket_size: float
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate blocking probability in time buckets.

    Args:
        df: Dataframe with 'tempo_criacao' and 'bloqueada' columns
        bucket_size: Size of time buckets

    Returns:
        Tuple of (bucket_centers, blocking_rates)
    """
    if len(df) == 0:
        return np.array([]), np.array([])

    min_time = df["tempo_criacao"].min()
    max_time = df["tempo_criacao"].max()

    bins = np.arange(min_time, max_time + bucket_size, bucket_size)

    bucket_centers = []
    blocking_rates = []

    for i in range(len(bins) - 1):
        bucket_df = df[
            (df["tempo_criacao"] >= bins[i]) & (df["tempo_criacao"] < bins[i + 1])
        ]
        if len(bucket_df) > 0:
            blocked = bucket_df["bloqueada"].sum()
            total = len(bucket_df)
            blocking_rate = blocked / total
            bucket_centers.append((bins[i] + bins[i + 1]) / 2)
            blocking_rates.append(blocking_rate)

    return np.array(bucket_centers), np.array(blocking_rates)


def calculate_availability_per_bucket(
    df: pd.DataFrame, bucket_size: float
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate availability (acceptance rate) per time bucket.

    Args:
        df: Dataframe with 'tempo_criacao' and 'bloqueada' columns
        bucket_size: Size of time buckets

    Returns:
        Tuple of (bucket_centers, availability_rates)
    """
    bucket_centers, blocking_rates = calculate_blocking_probability_over_time(
        df, bucket_size
    )
    availability_rates = 1 - blocking_rates
    return bucket_centers, availability_rates


def create_comparison_data(
    scenario1,
    scenario2,
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    disaster_start: float,
    disaster_end: float,
    scenario1_name: str = "Scenario 1",
    scenario2_name: str = "Scenario 2",
) -> dict:
    """Create structured comparison data between two scenarios.

    Args:
        scenario1: First Scenario object
        scenario2: Second Scenario object
        df1: First scenario's dataframe (already filtered if needed)
        df2: Second scenario's dataframe (already filtered if needed)
        disaster_start: Disaster start time
        disaster_end: Disaster end time
        scenario1_name: Display name for first scenario
        scenario2_name: Display name for second scenario

    Returns:
        Dictionary with comparison metrics organized by category:
            {
                'performance_metrics': [
                    {
                        'name': str,
                        'scenario1_value': float,
                        'scenario2_value': float,
                        'absolute_diff': float,
                        'percent_diff': float | str
                    },
                    ...
                ],
                'config_parameters': [...],
                'scenario1_name': str,
                'scenario2_name': str
            }
    """
    from simulador.analysis.metrics_calculator import (
        calculate_availability,
        calculate_blocking_rate,
    )

    # Calculate performance metrics
    # Overall metrics
    avail1 = calculate_availability(df1)
    avail2 = calculate_availability(df2)

    block1 = calculate_blocking_rate(df1)
    block2 = calculate_blocking_rate(df2)

    # Find earliest migration start time
    migration_start1 = min(
        (
            isp.datacenter.tempo_de_reacao
            for isp in scenario1.lista_de_isps
            if isp.datacenter is not None
        ),
        default=disaster_start,
    )
    migration_start2 = min(
        (
            isp.datacenter.tempo_de_reacao
            for isp in scenario2.lista_de_isps
            if isp.datacenter is not None
        ),
        default=disaster_start,
    )
    migration_start = min(migration_start1, migration_start2)

    # Phase-based availability with proper time windows
    # Pre-disaster migration: from first migration start to disaster start
    pre_disaster1 = df1[
        (df1["tempo_criacao"] >= migration_start)
        & (df1["tempo_criacao"] < disaster_start)
    ]
    pre_disaster2 = df2[
        (df2["tempo_criacao"] >= migration_start)
        & (df2["tempo_criacao"] < disaster_start)
    ]

    # Disaster phase: from disaster start to disaster end
    disaster_phase1 = df1[
        (df1["tempo_criacao"] >= disaster_start) & (df1["tempo_criacao"] < disaster_end)
    ]
    disaster_phase2 = df2[
        (df2["tempo_criacao"] >= disaster_start) & (df2["tempo_criacao"] < disaster_end)
    ]

    # After disaster: from disaster end onwards
    after1 = df1[df1["tempo_criacao"] >= disaster_end]
    after2 = df2[df2["tempo_criacao"] >= disaster_end]

    # Calculate availability for each phase
    pre_disaster_avail1 = (
        calculate_availability(pre_disaster1) if len(pre_disaster1) > 0 else 0.0
    )
    pre_disaster_avail2 = (
        calculate_availability(pre_disaster2) if len(pre_disaster2) > 0 else 0.0
    )

    disaster_avail1 = (
        calculate_availability(disaster_phase1) if len(disaster_phase1) > 0 else 0.0
    )
    disaster_avail2 = (
        calculate_availability(disaster_phase2) if len(disaster_phase2) > 0 else 0.0
    )

    after_avail1 = calculate_availability(after1) if len(after1) > 0 else 0.0
    after_avail2 = calculate_availability(after2) if len(after2) > 0 else 0.0

    # Helper function to calculate differences
    def calc_diff(val1: float, val2: float) -> tuple[float, float | str]:
        """Calculate absolute and percentage difference."""
        abs_diff = val2 - val1
        if val1 == 0:
            if val2 == 0:
                pct_diff = "0%"
            else:
                pct_diff = "N/A"
        else:
            pct_diff = f"{(abs_diff / val1) * 100:.1f}%"
        return abs_diff, pct_diff

    # Build performance metrics list
    performance_metrics = []

    # Overall availability
    abs_diff, pct_diff = calc_diff(avail1, avail2)
    # Count difference = difference in number of accepted requests
    accepted1 = int(avail1 * len(df1))
    accepted2 = int(avail2 * len(df2))
    performance_metrics.append(
        {
            "name": "Overall Availability",
            "scenario1_value": avail1,
            "scenario2_value": avail2,
            "scenario1_count": len(df1),
            "scenario2_count": len(df2),
            "count_diff": accepted2 - accepted1,
            "absolute_diff": abs_diff,
            "percent_diff": pct_diff,
            "format": "percentage",
        }
    )

    # Overall blocking rate
    abs_diff, pct_diff = calc_diff(block1, block2)
    # Count difference = difference in number of blocked requests
    blocked1 = int(block1 * len(df1))
    blocked2 = int(block2 * len(df2))
    performance_metrics.append(
        {
            "name": "Overall Blocking Rate",
            "scenario1_value": block1,
            "scenario2_value": block2,
            "scenario1_count": len(df1),
            "scenario2_count": len(df2),
            "count_diff": blocked2 - blocked1,
            "absolute_diff": abs_diff,
            "percent_diff": pct_diff,
            "format": "percentage",
        }
    )

    # Availability pre-disaster migration
    abs_diff, pct_diff = calc_diff(pre_disaster_avail1, pre_disaster_avail2)
    # Count difference = difference in number of accepted requests
    accepted_pre1 = int(pre_disaster_avail1 * len(pre_disaster1))
    accepted_pre2 = int(pre_disaster_avail2 * len(pre_disaster2))
    performance_metrics.append(
        {
            "name": "Availability (Pre-disaster Migration)",
            "scenario1_value": pre_disaster_avail1,
            "scenario2_value": pre_disaster_avail2,
            "scenario1_count": len(pre_disaster1),
            "scenario2_count": len(pre_disaster2),
            "count_diff": accepted_pre2 - accepted_pre1,
            "absolute_diff": abs_diff,
            "percent_diff": pct_diff,
            "format": "percentage",
        }
    )

    # Availability disaster phase
    abs_diff, pct_diff = calc_diff(disaster_avail1, disaster_avail2)
    # Count difference = difference in number of accepted requests
    accepted_disaster1 = int(disaster_avail1 * len(disaster_phase1))
    accepted_disaster2 = int(disaster_avail2 * len(disaster_phase2))
    performance_metrics.append(
        {
            "name": "Availability (Disaster Phase)",
            "scenario1_value": disaster_avail1,
            "scenario2_value": disaster_avail2,
            "scenario1_count": len(disaster_phase1),
            "scenario2_count": len(disaster_phase2),
            "count_diff": accepted_disaster2 - accepted_disaster1,
            "absolute_diff": abs_diff,
            "percent_diff": pct_diff,
            "format": "percentage",
        }
    )

    # Availability after disaster
    abs_diff, pct_diff = calc_diff(after_avail1, after_avail2)
    # Count difference = difference in number of accepted requests
    accepted_after1 = int(after_avail1 * len(after1))
    accepted_after2 = int(after_avail2 * len(after2))
    performance_metrics.append(
        {
            "name": "Availability (After Disaster)",
            "scenario1_value": after_avail1,
            "scenario2_value": after_avail2,
            "scenario1_count": len(after1),
            "scenario2_count": len(after2),
            "count_diff": accepted_after2 - accepted_after1,
            "absolute_diff": abs_diff,
            "percent_diff": pct_diff,
            "format": "percentage",
        }
    )

    # Build config parameters list
    config_parameters = []

    # Extract config if available
    config1 = getattr(scenario1, "config", None)
    config2 = getattr(scenario2, "config", None)

    if config1 and config2:
        # Alpha
        alpha1 = config1.alpha
        alpha2 = config2.alpha
        abs_diff, pct_diff = calc_diff(alpha1, alpha2)
        config_parameters.append(
            {
                "name": "Alpha (α) - ISP Usage Weight",
                "scenario1_value": alpha1,
                "scenario2_value": alpha2,
                "absolute_diff": abs_diff,
                "percent_diff": pct_diff,
                "format": "decimal",
            }
        )

        # Beta
        beta1 = config1.beta
        beta2 = config2.beta
        abs_diff, pct_diff = calc_diff(beta1, beta2)
        config_parameters.append(
            {
                "name": "Beta (β) - Migration Traffic Weight",
                "scenario1_value": beta1,
                "scenario2_value": beta2,
                "absolute_diff": abs_diff,
                "percent_diff": pct_diff,
                "format": "decimal",
            }
        )

        # Gamma
        gamma1 = config1.gamma
        gamma2 = config2.gamma
        abs_diff, pct_diff = calc_diff(gamma1, gamma2)
        config_parameters.append(
            {
                "name": "Gamma (γ) - Link Criticality Weight",
                "scenario1_value": gamma1,
                "scenario2_value": gamma2,
                "absolute_diff": abs_diff,
                "percent_diff": pct_diff,
                "format": "decimal",
            }
        )

        # Target utilization
        target_util1 = config1.target_utilization
        target_util2 = config2.target_utilization
        abs_diff, pct_diff = calc_diff(target_util1, target_util2)
        config_parameters.append(
            {
                "name": "Target Network Usage",
                "scenario1_value": target_util1,
                "scenario2_value": target_util2,
                "absolute_diff": abs_diff,
                "percent_diff": pct_diff,
                "format": "percentage",
            }
        )

        # Migration network fraction
        mig_frac1 = config1.migration_network_fraction
        mig_frac2 = config2.migration_network_fraction
        abs_diff, pct_diff = calc_diff(mig_frac1, mig_frac2)
        config_parameters.append(
            {
                "name": "Target Migration Network Usage",
                "scenario1_value": mig_frac1,
                "scenario2_value": mig_frac2,
                "absolute_diff": abs_diff,
                "percent_diff": pct_diff,
                "format": "percentage",
            }
        )

    return {
        "performance_metrics": performance_metrics,
        "config_parameters": config_parameters,
        "scenario1_name": scenario1_name,
        "scenario2_name": scenario2_name,
    }


def create_multi_scenario_comparison_data(
    scenarios: dict[str, object],
    dataframes: dict[str, pd.DataFrame],
    disaster_start: float,
    disaster_end: float,
) -> dict:
    """Create comparison data structure for N scenarios.
    
    Args:
        scenarios: dict mapping scenario_name -> scenario object
        dataframes: dict mapping scenario_name -> dataframe
        disaster_start: Disaster start time
        disaster_end: Disaster end time
    
    Returns:
        Dictionary with structure for multi-scenario table:
        {
            'scenario_names': list[str],
            'performance_metrics': list[dict],
            'config_parameters': list[dict]
        }
    """
    scenario_names = list(scenarios.keys())
    
    # Calculate metrics for each scenario
    performance_metrics = []
    
    # Overall Availability
    availabilities = {}
    total_requests = {}
    blocked_requests = {}
    
    for name, df in dataframes.items():
        total = len(df)
        blocked = df['bloqueada'].sum()
        availabilities[name] = 1 - (blocked / total) if total > 0 else 0
        total_requests[name] = total
        blocked_requests[name] = int(blocked)
    
    performance_metrics.append({
        'name': 'Overall Availability',
        'values': availabilities,
        'counts': total_requests,
        'format': 'percentage'
    })
    
    # Overall Blocking Rate
    blocking_rates = {name: 1 - availabilities[name] for name in scenario_names}
    performance_metrics.append({
        'name': 'Overall Blocking Rate',
        'values': blocking_rates,
        'counts': blocked_requests,
        'format': 'percentage'
    })
    
    # Migration Availability
    migration_availabilities = {}
    migration_totals = {}
    migration_blocked = {}
    
    for name, df in dataframes.items():
        migration_df = df[df['requisicao_de_migracao'] == True]
        total = len(migration_df)
        blocked = migration_df['bloqueada'].sum() if total > 0 else 0
        migration_availabilities[name] = 1 - (blocked / total) if total > 0 else 0
        migration_totals[name] = total
        migration_blocked[name] = int(blocked)
    
    performance_metrics.append({
        'name': 'Migration Availability',
        'values': migration_availabilities,
        'counts': migration_totals,
        'format': 'percentage'
    })
    
    # Migration Blocking Rate
    migration_blocking = {name: 1 - migration_availabilities[name] for name in scenario_names}
    performance_metrics.append({
        'name': 'Migration Blocking Rate',
        'values': migration_blocking,
        'counts': migration_blocked,
        'format': 'percentage'
    })
    
    # Before Disaster Availability
    before_availabilities = {}
    before_totals = {}
    before_blocked = {}
    
    for name, df in dataframes.items():
        before_df = df[df['tempo_criacao'] < disaster_start]
        total = len(before_df)
        blocked = before_df['bloqueada'].sum() if total > 0 else 0
        before_availabilities[name] = 1 - (blocked / total) if total > 0 else 0
        before_totals[name] = total
        before_blocked[name] = int(blocked)
    
    performance_metrics.append({
        'name': 'Before Disaster Availability',
        'values': before_availabilities,
        'counts': before_totals,
        'format': 'percentage'
    })
    
    # During Disaster Availability
    during_availabilities = {}
    during_totals = {}
    during_blocked = {}
    
    for name, df in dataframes.items():
        during_df = df[(df['tempo_criacao'] >= disaster_start) & (df['tempo_criacao'] < disaster_end)]
        total = len(during_df)
        blocked = during_df['bloqueada'].sum() if total > 0 else 0
        during_availabilities[name] = 1 - (blocked / total) if total > 0 else 0
        during_totals[name] = total
        during_blocked[name] = int(blocked)
    
    performance_metrics.append({
        'name': 'During Disaster Availability',
        'values': during_availabilities,
        'counts': during_totals,
        'format': 'percentage'
    })
    
    # After Disaster Availability
    after_availabilities = {}
    after_totals = {}
    after_blocked = {}
    
    for name, df in dataframes.items():
        after_df = df[df['tempo_criacao'] >= disaster_end]
        total = len(after_df)
        blocked = after_df['bloqueada'].sum() if total > 0 else 0
        after_availabilities[name] = 1 - (blocked / total) if total > 0 else 0
        after_totals[name] = total
        after_blocked[name] = int(blocked)
    
    performance_metrics.append({
        'name': 'After Disaster Availability',
        'values': after_availabilities,
        'counts': after_totals,
        'format': 'percentage'
    })
    
    # Configuration Parameters
    config_parameters = []
    for name, scenario in scenarios.items():
        config = {
            'scenario': name,
            'alpha': scenario.config.alpha,
            'beta': scenario.config.beta,
            'gamma': scenario.config.gamma,
            'routing': scenario.config.routing_algorithm.__name__ if hasattr(scenario.config, 'routing_algorithm') else 'N/A'
        }
        config_parameters.append(config)
    
    return {
        'scenario_names': scenario_names,
        'performance_metrics': performance_metrics,
        'config_parameters': config_parameters
    }
