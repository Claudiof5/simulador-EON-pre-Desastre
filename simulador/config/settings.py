"""Configuration constants for EON network simulation.

Contains simulation parameters for:
- Network requests (bandwidth, class types, holding time)
- Topology settings (slots, paths, capacity)
- Disaster scenarios (timing, duration)
- Datacenter configurations (throughput, reaction time)
"""

# Quanto as requisicoes
BANDWIDTH: list[int] = [100, 150, 200, 250, 300, 350, 400]
CLASS_TYPE: list[float] = [1, 2, 3]
CLASS_WEIGHT: list[float] = [0.15, 0.25, 0.60]

HOLDING_TIME: float = 1

# Quando a topologia
NUMERO_DE_SLOTS: int = 200
NUMERO_DE_CAMINHOS: int = 10
SLOT_SIZE: float = 12.5


_NUMERO_DE_EDGES_DA_TOPOLOGIA: int = 43
_CAPACIDADE_MAXIMA_DA_REDE: int = NUMERO_DE_SLOTS * _NUMERO_DE_EDGES_DA_TOPOLOGIA

# Traffic load calculation based on topology analysis
# Analysis results: avg path length = 3 hops, avg modulation = 1.45x
_AVG_BANDWIDTH = sum(BANDWIDTH) / len(BANDWIDTH)  # 250 Gbps
_AVG_PATH_LENGTH = 3.0  # Average hops per path (from topology analysis)
_AVG_MODULATION = 1.45  # Average modulation factor (from distance analysis)

# Formula: slots_per_request = (bandwidth / (modulation * SLOT_SIZE)) * path_length
# Higher modulation factor = fewer slots needed (better spectral efficiency)
_AVG_SLOTS_PER_LINK = _AVG_BANDWIDTH / (
    _AVG_MODULATION * SLOT_SIZE
)  # ~13.8 slots per link
_AVG_SLOTS_PER_REQUEST = _AVG_SLOTS_PER_LINK * _AVG_PATH_LENGTH  # ~41.4 slot-hops

# Target network utilization (0.6 = 60%, 0.7 = 70%, 0.8 = 80%)
_TARGET_UTILIZATION = 0.75  # Conservative: expect 10-20% blocking rate
# _TARGET_UTILIZATION = 0.7  # Moderate: expect 20-30% blocking rate
# _TARGET_UTILIZATION = 0.8  # High: expect 30-40% blocking rate

# Calculate Erlangs (average concurrent requests)
ERLANGS: float = (
    _CAPACIDADE_MAXIMA_DA_REDE * _TARGET_UTILIZATION
) / _AVG_SLOTS_PER_REQUEST
REQUISICOES_POR_SEGUNDO: float = ERLANGS / HOLDING_TIME

# Simulation duration (in seconds)
# The simulation will run until this time or all requests are processed
SIMULATION_DURATION: float = 1200  # 20 minutes (default)
# SIMULATION_DURATION: float = 900   # 15 minutes
# SIMULATION_DURATION: float = 1800  # 30 minutes

# Calculate number of requests based on simulation duration and request rate
# This ensures enough requests are generated to fill the simulation time
NUMERO_DE_REQUISICOES: int = int(SIMULATION_DURATION * REQUISICOES_POR_SEGUNDO)

numero_de_isps: int = 5


INICIO_DESASTRE: float = 600
VARIANCIA_INICIO_DESASTRE: float = INICIO_DESASTRE * 0.05
DURACAO_DESASTRE: float = 200
VARIANCIA_DURACAO_DESASTRE: float = DURACAO_DESASTRE * 0.1


# Quanto aos datacenters
# MIGRATION_NETWORK_FRACTION: What fraction of network capacity can ALL datacenters
# use for migration traffic (e.g., 0.2 = 20% of network capacity for migration)
MIGRATION_NETWORK_FRACTION: float = 0.25  # 20% of network for ALL migration traffic

# Calculate throughput in SLOTS per second for each datacenter
# Total migration capacity in requests/s
_TOTAL_MIGRATION_REQ_PER_SEC = REQUISICOES_POR_SEGUNDO * MIGRATION_NETWORK_FRACTION

# Each ISP gets equal share of migration capacity
_PER_ISP_MIGRATION_REQ_PER_SEC = _TOTAL_MIGRATION_REQ_PER_SEC / numero_de_isps

# Convert to slots/s using average slot consumption
# This represents how many slots per second each datacenter can push through the network
THROUGHPUT: float = _PER_ISP_MIGRATION_REQ_PER_SEC * _AVG_SLOTS_PER_REQUEST
VARIANCIA_THROUGHPUT: float = THROUGHPUT * 0.1

# Reaction time: how long before datacenter starts migration after disaster
TEMPO_DE_REACAO: int = 300  # seconds (5 minutes)
VARIANCIA_TEMPO_DE_REACAO: float = TEMPO_DE_REACAO * 0.15

# Datacenter storage capacity: cumulative bandwidth target (in Gbps)
#
# SIMPLIFIED APPROACH: Track migration by accumulating bandwidth of successful requests
# Each successful request contributes its bandwidth (Gbps) to the total.
# Migration completes when: sum(bandwidth) >= TAMANHO_DATACENTER
#
# This is simpler than tracking Gigabits (bandwidth × time), and more intuitive:
# "Need to allocate X Gbps total across all requests" vs "Need to transfer X Gigabits"
#
# Calculation:
# 1. Migration rate: _PER_ISP_MIGRATION_REQ_PER_SEC requests/second
# 2. Average bandwidth per request: _AVG_BANDWIDTH Gbps
# 3. Time available: INICIO_DESASTRE - TEMPO_DE_REACAO seconds
# 4. Success rate target: 0.75 (expecting 25% blocking)
#
# Formula: Total_Bandwidth = (req/s × Gbps/req) × time_available × success_target
_TIME_AVAILABLE_FOR_MIGRATION = INICIO_DESASTRE - TEMPO_DE_REACAO
_MIGRATION_SUCCESS_TARGET = 0.75  # Target 75% completion with expected blocking

# Total bandwidth target (cumulative Gbps across all successful requests)
TAMANHO_DATACENTER: float = (
    _PER_ISP_MIGRATION_REQ_PER_SEC
    * _AVG_BANDWIDTH
    * _TIME_AVAILABLE_FOR_MIGRATION
    * _MIGRATION_SUCCESS_TARGET
)
VARIANCIA_TAMANHO_DATACENTER: float = 0

# Modulation factors and distance thresholds
DISTANCIA_MODULACAO_4: int = 500  # Distance threshold for 4x modulation factor
DISTANCIA_MODULACAO_3: int = 1000  # Distance threshold for 3x modulation factor
DISTANCIA_MODULACAO_2: int = 2000  # Distance threshold for 2x modulation factor
FATOR_MODULACAO_4: int = 4  # Highest modulation factor
FATOR_MODULACAO_3: int = 3  # High modulation factor
FATOR_MODULACAO_2: int = 2  # Medium modulation factor
FATOR_MODULACAO_1: int = 1  # Lowest modulation factor

ALPHA: float = 0.5  # This is the weight of the ISP usage in the weighted paths
BETA: float = 0.5  # This is the weight of the migration traffic in the weighted paths
GAMMA: float = (
    0.5  # This is the weight of the criticality of the links in the weighted paths
)

# Traffic generation weights for hybrid ISP selection
TRAFFIC_WEIGHT_EDGES: float = 0.5  # 50% weight on network capacity (edges)
TRAFFIC_WEIGHT_NODES: float = 0.3  # 30% weight on network size (nodes)
TRAFFIC_WEIGHT_ISOLATION: float = 0.2  # 20% weight on ISP isolation
