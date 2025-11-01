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
