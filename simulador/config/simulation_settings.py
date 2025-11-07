"""Simulation configuration classes for parameterized experiments.

This module provides configuration for scenario generation:
- ScenarioConfig: All settings that define the scenario structure (immutable after generation)

Since traffic is pre-generated, ALL parameters including disaster timing, migration timing,
and routing weights (α, β, γ) are baked into the scenario at generation time and cannot
be changed afterward.

For pre-generated traffic scenarios, routing weights affect the precomputed weighted paths
stored in ISP objects. To test different weights, you must generate different scenarios.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any

# Import current defaults from settings.py
from simulador.config.settings import (
    ALPHA,
    BANDWIDTH,
    BETA,
    CLASS_TYPE,
    CLASS_WEIGHT,
    DURACAO_DESASTRE,
    GAMMA,
    HOLDING_TIME,
    INICIO_DESASTRE,
    NUMERO_DE_CAMINHOS,
    NUMERO_DE_REQUISICOES,
    NUMERO_DE_SLOTS,
    SIMULATION_DURATION,
    SLOT_SIZE,
    TAMANHO_DATACENTER,
    TEMPO_DE_REACAO,
    THROUGHPUT,
    TRAFFIC_WEIGHT_EDGES,
    TRAFFIC_WEIGHT_ISOLATION,
    TRAFFIC_WEIGHT_NODES,
    VARIANCIA_DURACAO_DESASTRE,
    VARIANCIA_INICIO_DESASTRE,
    VARIANCIA_TAMANHO_DATACENTER,
    VARIANCIA_TEMPO_DE_REACAO,
    VARIANCIA_THROUGHPUT,
    numero_de_isps,
)


@dataclass(frozen=True)  # Immutable - prevents accidental modification
class ScenarioConfig:
    """Configuration for scenario generation (immutable after creation).

    These settings affect the structure of the scenario and traffic generation.
    Once a scenario is generated with these settings, they cannot be changed.

    All defaults match simulador.config.settings values.

    Attributes:
        name: Identifier for this scenario configuration
        description: Human-readable description

        # Network topology
        numero_de_slots: Total slots per link
        numero_de_caminhos: Number of k-shortest paths
        slot_size: Size of each slot in Gbps
        numero_de_isps: Number of ISPs in the network

        # Traffic generation
        numero_de_requisicoes: Number of requests to generate
        simulation_duration: Total simulation time (seconds)
        holding_time: Average request holding time
        bandwidth_options: List of possible bandwidth values
        class_types: List of class type values
        class_weights: Probability weights for class types

        # Traffic distribution weights
        traffic_weight_edges: Weight on network capacity
        traffic_weight_nodes: Weight on network size
        traffic_weight_isolation: Weight on ISP isolation

        # Disaster parameters (baked into traffic generation)
        disaster_start: When disaster begins
        disaster_start_variance: Random variance in start time
        disaster_duration: How long disaster lasts
        disaster_duration_variance: Random variance in duration

        # Migration parameters (baked into traffic generation)
        datacenter_reaction_time: Delay before migration starts
        datacenter_reaction_variance: Random variance in reaction time
        datacenter_size: Datacenter storage capacity (cumulative Gbps)
        datacenter_size_variance: Variance in datacenter size
        datacenter_throughput: Migration throughput (slots/s)
        datacenter_throughput_variance: Variance in throughput
    """

    # Identification
    name: str = "default_scenario"
    description: str = "Default scenario configuration"

    # Metadata (for reproducibility and versioning)
    version: str = "1.0"  # Config schema version
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)  # User-defined metadata

    # Network topology
    numero_de_slots: int = NUMERO_DE_SLOTS
    numero_de_caminhos: int = NUMERO_DE_CAMINHOS
    slot_size: float = SLOT_SIZE
    numero_de_isps: int = numero_de_isps

    # Traffic generation
    numero_de_requisicoes: int = NUMERO_DE_REQUISICOES
    simulation_duration: float = SIMULATION_DURATION
    holding_time: float = HOLDING_TIME
    bandwidth_options: list[int] = field(default_factory=lambda: list(BANDWIDTH))
    class_types: list[float] = field(default_factory=lambda: list(CLASS_TYPE))
    class_weights: list[float] = field(default_factory=lambda: list(CLASS_WEIGHT))

    # Traffic distribution
    traffic_weight_edges: float = TRAFFIC_WEIGHT_EDGES
    traffic_weight_nodes: float = TRAFFIC_WEIGHT_NODES
    traffic_weight_isolation: float = TRAFFIC_WEIGHT_ISOLATION

    # Routing weights (used during path computation, baked into scenario)
    alpha: float = ALPHA  # ISP usage weight in weighted routing
    beta: float = BETA  # Migration traffic weight in weighted routing
    gamma: float = GAMMA  # Link criticality weight in weighted routing

    # Disaster parameters
    disaster_start: float = INICIO_DESASTRE
    disaster_start_variance: float = VARIANCIA_INICIO_DESASTRE
    disaster_duration: float = DURACAO_DESASTRE
    disaster_duration_variance: float = VARIANCIA_DURACAO_DESASTRE

    # Migration parameters
    datacenter_reaction_time: float = TEMPO_DE_REACAO
    datacenter_reaction_variance: float = VARIANCIA_TEMPO_DE_REACAO
    datacenter_size: float = TAMANHO_DATACENTER
    datacenter_size_variance: float = VARIANCIA_TAMANHO_DATACENTER
    datacenter_throughput: float = THROUGHPUT
    datacenter_throughput_variance: float = VARIANCIA_THROUGHPUT
    
    # Network analysis constants (could be made configurable in future)
    avg_path_length: float = 3.0  # Average hops per path
    avg_modulation_factor: float = 1.45  # Average modulation efficiency
    target_utilization: float = 0.5  # Target network utilization (0-1)
    numero_edges_topologia: int = 43  # Number of edges in topology

    def __post_init__(self):
        """Validate settings (immutable - no field modifications)."""
        # Validate network parameters
        if self.simulation_duration <= 0:
            raise ValueError(
                f"simulation_duration must be positive, got {self.simulation_duration}"
            )
        if self.numero_de_slots <= 0:
            raise ValueError(
                f"numero_de_slots must be positive, got {self.numero_de_slots}"
            )
        if self.numero_de_requisicoes < 0:
            raise ValueError(
                f"numero_de_requisicoes must be non-negative, got {self.numero_de_requisicoes}"
            )

        # Validate routing weights
        if not 0 <= self.alpha <= 1:
            raise ValueError(f"alpha must be in [0,1], got {self.alpha}")
        if not 0 <= self.beta <= 1:
            raise ValueError(f"beta must be in [0,1], got {self.beta}")
        if not 0 <= self.gamma <= 1:
            raise ValueError(f"gamma must be in [0,1], got {self.gamma}")

        # Validate timing parameters
        if self.disaster_start < 0:
            raise ValueError(
                f"disaster_start must be non-negative, got {self.disaster_start}"
            )
        if self.disaster_duration <= 0:
            raise ValueError(
                f"disaster_duration must be positive, got {self.disaster_duration}"
            )

    def copy_with(self, **kwargs) -> ScenarioConfig:
        """Create a copy with modified parameters.

        Args:
            **kwargs: Parameters to override

        Returns:
            New ScenarioConfig instance
        """
        return replace(self, **kwargs)

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary of all settings
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ScenarioConfig:
        """Create config from dictionary.

        Args:
            data: Dictionary with configuration parameters

        Returns:
            New ScenarioConfig instance
        """
        return cls(**data)

    def save_to_json(self, filepath: str | Path) -> None:
        """Save configuration to JSON file.

        Args:
            filepath: Path to save JSON file

        Example:
            >>> config.save_to_json("configs/experiment1.json")
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str | Path) -> ScenarioConfig:
        """Load configuration from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            ScenarioConfig instance

        Example:
            >>> config = ScenarioConfig.load_from_json("configs/experiment1.json")
        """
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)

    def diff(self, other: ScenarioConfig) -> dict[str, tuple[Any, Any]]:
        """Compare this config with another and return differences.

        Args:
            other: Another ScenarioConfig to compare with

        Returns:
            Dictionary of {field_name: (this_value, other_value)} for differences

        Example:
            >>> diff = config1.diff(config2)
            >>> print(diff)
            {'alpha': (0.6, 0.8), 'beta': (0.2, 0.1)}
        """
        differences = {}
        for field_name in self.__dataclass_fields__:
            my_value = getattr(self, field_name)
            other_value = getattr(other, field_name)
            if my_value != other_value:
                differences[field_name] = (my_value, other_value)
        return differences

    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"ScenarioConfig('{self.name}')\n"
            f"  Network: {self.numero_de_slots} slots, {self.numero_de_caminhos} paths, "
            f"{self.numero_de_isps} ISPs\n"
            f"  Traffic: {self.numero_de_requisicoes} requests, {self.simulation_duration}s\n"
            f"  Disaster: start={self.disaster_start}s, duration={self.disaster_duration}s\n"
            f"  Routing: α={self.alpha}, β={self.beta}, γ={self.gamma}"
        )
    
    # Computed properties - derived from config parameters
    
    @property
    def avg_bandwidth(self) -> float:
        """Average bandwidth across all bandwidth options.
        
        Returns:
            Average bandwidth in Gbps
        """
        return sum(self.bandwidth_options) / len(self.bandwidth_options)
    
    @property
    def avg_slots_per_link(self) -> float:
        """Average slots consumed per link.
        
        Returns:
            Average slots per link based on bandwidth and modulation
        """
        return self.avg_bandwidth / (self.avg_modulation_factor * self.slot_size)
    
    @property
    def avg_slots_per_request(self) -> float:
        """Average total slots consumed per request (across all hops).
        
        Returns:
            Average slot-hops per request
        """
        return self.avg_slots_per_link * self.avg_path_length
    
    @property
    def network_capacity(self) -> float:
        """Total network capacity in slot-hops.
        
        Returns:
            Total capacity = slots × edges
        """
        return self.numero_de_slots * self.numero_edges_topologia
    
    @property
    def erlangs(self) -> float:
        """Traffic load in Erlangs (average concurrent requests).
        
        Returns:
            Erlangs based on network capacity and target utilization
        """
        return (self.network_capacity * self.target_utilization) / self.avg_slots_per_request
    
    @property
    def requisicoes_por_segundo(self) -> float:
        """Request arrival rate in requests per second.
        
        Returns:
            Request rate based on Erlangs and holding time
        """
        return self.erlangs / self.holding_time
    
    @property
    def migration_network_fraction(self) -> float:
        """Fraction of network capacity allocated for migration traffic.
        
        Returns:
            Fraction (0-1) of total network capacity for ALL migration traffic
        """
        # Calculate from datacenter throughput if set, otherwise use default
        # This is a simplified calculation - could be made more sophisticated
        return 0.25  # Default: 25% of network for migration
    
    @property
    def per_isp_migration_rate(self) -> float:
        """Migration request rate per ISP in requests/second.
        
        Returns:
            Request rate for each ISP's migration
        """
        total_migration_rate = self.requisicoes_por_segundo * self.migration_network_fraction
        return total_migration_rate / self.numero_de_isps
    
    @property
    def time_available_for_migration(self) -> float:
        """Time window available for migration before disaster.
        
        Returns:
            Time in seconds between reaction start and disaster start
        """
        return self.disaster_start - self.datacenter_reaction_time


class ScenarioConfigBuilder:
    """Builder pattern for creating ScenarioConfig with incremental modifications.

    Useful for creating multiple config variations from a base configuration.

    Example:
        >>> builder = ScenarioConfigBuilder("experiment")
        >>> builder.with_routing_weights(alpha=0.8, beta=0.1, gamma=0.1)
        >>> builder.with_traffic_load(numero_de_requisicoes=10000)
        >>> config = builder.build()
    """

    def __init__(self, name: str = "custom", base_config: ScenarioConfig | None = None):
        """Initialize builder with optional base config.

        Args:
            name: Name for the configuration
            base_config: Optional base config to start from (defaults to DEFAULT_SCENARIO)
        """
        if base_config is None:
            self._params = {"name": name}
        else:
            self._params = base_config.to_dict()
            self._params["name"] = name

    def with_routing_weights(
        self,
        alpha: float | None = None,
        beta: float | None = None,
        gamma: float | None = None,
    ) -> ScenarioConfigBuilder:
        """Set routing weights."""
        if alpha is not None:
            self._params["alpha"] = alpha
        if beta is not None:
            self._params["beta"] = beta
        if gamma is not None:
            self._params["gamma"] = gamma
        return self

    def with_traffic_load(
        self,
        numero_de_requisicoes: int | None = None,
        simulation_duration: float | None = None,
    ) -> ScenarioConfigBuilder:
        """Set traffic load parameters."""
        if numero_de_requisicoes is not None:
            self._params["numero_de_requisicoes"] = numero_de_requisicoes
        if simulation_duration is not None:
            self._params["simulation_duration"] = simulation_duration
        return self

    def with_disaster_timing(
        self, start: float | None = None, duration: float | None = None
    ) -> ScenarioConfigBuilder:
        """Set disaster timing parameters."""
        if start is not None:
            self._params["disaster_start"] = start
        if duration is not None:
            self._params["disaster_duration"] = duration
        return self

    def with_network_capacity(
        self, numero_de_slots: int | None = None, numero_de_caminhos: int | None = None
    ) -> ScenarioConfigBuilder:
        """Set network capacity parameters."""
        if numero_de_slots is not None:
            self._params["numero_de_slots"] = numero_de_slots
        if numero_de_caminhos is not None:
            self._params["numero_de_caminhos"] = numero_de_caminhos
        return self

    def with_metadata(self, **metadata) -> ScenarioConfigBuilder:
        """Add custom metadata."""
        if "metadata" not in self._params:
            self._params["metadata"] = {}
        self._params["metadata"].update(metadata)
        return self

    def build(self) -> ScenarioConfig:
        """Build the final configuration."""
        return ScenarioConfig(**self._params)


# Pre-defined scenario configurations with routing weight variations

DEFAULT_SCENARIO = ScenarioConfig(
    name="default",
    description="Default settings from settings.py",
)

HIGH_ISP_WEIGHT_SCENARIO = ScenarioConfig(
    name="high_isp_weight",
    description="Prioritize ISP-internal routing (α=0.8)",
    alpha=0.8,
    beta=0.1,
    gamma=0.1,
)

HIGH_MIGRATION_WEIGHT_SCENARIO = ScenarioConfig(
    name="high_migration_weight",
    description="Avoid paths with migration traffic (β=0.5)",
    alpha=0.3,
    beta=0.5,
    gamma=0.2,
)

HIGH_CRITICALITY_WEIGHT_SCENARIO = ScenarioConfig(
    name="high_criticality_weight",
    description="Avoid critical links (γ=0.7)",
    alpha=0.2,
    beta=0.1,
    gamma=0.7,
)

BALANCED_WEIGHTS_SCENARIO = ScenarioConfig(
    name="balanced",
    description="Equal weight to all routing factors",
    alpha=0.33,
    beta=0.33,
    gamma=0.34,
)

# Export commonly used configs
PRESET_SCENARIO_CONFIGS = {
    "default": DEFAULT_SCENARIO,
    "high_isp": HIGH_ISP_WEIGHT_SCENARIO,
    "high_migration": HIGH_MIGRATION_WEIGHT_SCENARIO,
    "high_criticality": HIGH_CRITICALITY_WEIGHT_SCENARIO,
    "balanced": BALANCED_WEIGHTS_SCENARIO,
}
