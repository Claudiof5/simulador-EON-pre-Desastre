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


__NUMERO_DE_EDGES_DA_TOPOLOGIA: int = 43
__CAPACIDADE_MAXIMA_DA_REDE: int = NUMERO_DE_SLOTS * __NUMERO_DE_EDGES_DA_TOPOLOGIA

ERLANGS: float = 110
REQUISICOES_POR_SEGUNDO: float = ERLANGS / HOLDING_TIME
NUMERO_DE_REQUISICOES: int = 150000
numero_de_isps: int = 5


INICIO_DESASTRE: float = 600
VARIANCIA_INICIO_DESASTRE: float = INICIO_DESASTRE * 0.05
DURACAO_DESASTRE: float = 200
VARIANCIA_DURACAO_DESASTRE: float = DURACAO_DESASTRE * 0.1


# Quanto aos datacenters
# THROUGHPUT                   :float = REQUISITADO_DA_REDE_POR_SEGUNDO * 0.025
THROUGHPUT: float = __CAPACIDADE_MAXIMA_DA_REDE * 0.025
VARIANCIA_THROUGPUT: float = THROUGHPUT * 0.1
TEMPO_DE_REACAO: int = 300
VARIANCIA_TEMPO_DE_REACAO: float = TEMPO_DE_REACAO * 0.15
TAMANHO_DATACENTER: float = THROUGHPUT * TEMPO_DE_REACAO * 0.75
VARIANCIA_TAMANHO_DATACENTER: float = TAMANHO_DATACENTER * 0.1

# Modulation factors and distance thresholds
DISTANCIA_MODULACAO_4: int = 500  # Distance threshold for 4x modulation factor
DISTANCIA_MODULACAO_3: int = 1000  # Distance threshold for 3x modulation factor
DISTANCIA_MODULACAO_2: int = 2000  # Distance threshold for 2x modulation factor
FATOR_MODULACAO_4: int = 4  # Highest modulation factor
FATOR_MODULACAO_3: int = 3  # High modulation factor
FATOR_MODULACAO_2: int = 2  # Medium modulation factor
FATOR_MODULACAO_1: int = 1  # Lowest modulation factor
