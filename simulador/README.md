# EON Network Simulator (v2) - Clean Architecture

This is the refactored version of the EON (Elastic Optical Network) simulator with a modern, clean architecture following Python best practices.

## 📁 Directory Structure

```
simulador/
├── __init__.py              # Package exports
├── main.py                  # Application entry point
│
├── config/                  # Configuration & settings
│   ├── __init__.py
│   └── settings.py          # Global configuration constants
│
├── core/                    # Core network components
│   ├── __init__.py
│   ├── path_manager.py      # Path computation utilities
│   ├── topology.py          # Network topology management
│   └── request.py           # Request/requisition model
│
├── routing/                 # Routing algorithms
│   ├── __init__.py
│   ├── base.py              # Abstract routing interface
│   ├── first_fit.py         # First-Fit routing
│   ├── best_fit.py          # Best-Fit routing
│   ├── best_fit_disaster_aware.py
│   ├── best_fit_sliding_window.py
│   ├── first_fit_disaster_aware.py
│   ├── disaster_aware_with_blocking.py
│   ├── subnet.py
│   ├── subnet_disaster_aware.py
│   └── disaster.py
│
├── entities/                # Business domain entities
│   ├── __init__.py
│   ├── isp.py               # Internet Service Provider
│   ├── datacenter.py        # Datacenter entity
│   ├── disaster.py          # Disaster event
│   └── scenario.py          # Simulation scenario
│
├── generators/              # Factory classes for entities
│   ├── __init__.py
│   ├── scenario_generator.py
│   ├── traffic_generator.py
│   ├── disaster_generator.py
│   ├── datacenter_generator.py
│   └── isp_generator.py
│
└── utils/                   # Utilities
    ├── __init__.py
    ├── logger.py            # Logging utilities
    └── metrics.py           # Metrics/statistics collection
```

## 🚀 Usage

### Basic Import (Recommended)

```python
# Import from top-level package
from simulador import Topology, FirstFit, ISP, Datacenter
from simulador.config import NUMERO_DE_SLOTS, BANDWIDTH

# Or import from sub-packages
from simulador.core import Topology
from simulador.routing import FirstFit, BestFit
from simulador.entities import ISP, Datacenter
from simulador.generators import TrafficGenerator
```

### Running the Simulation

```python
from simulador import main

# Run simulation
main()
```

### Note on the migration rate

`config/settings.py` sizes each provider's migration at
`MIGRATION_NETWORK_FRACTION × background rate / 5 ≈ 7.8` requests/s and turns
it into `THROUGHPUT` with 41.4 slot-hops per request (3 hops, modulation 1.45).
`generators/traffic_generator.py` converts it back with 20 slots per request
(250 Gb/s ÷ 12.5 Gb/s), so the generated rate is about 2.07× the configured one
(~16 requests/s per provider). `TAMANHO_DATACENTER` is still computed from the
configured 7.8 requests/s, so the offered migration is about 2.8× the volume
needed instead of the intended 1/0.75. The stored scenarios and the article use
the generated values; the 25% fraction and the "75% completion" comment in
`settings.py` describe the intent, not what is simulated.

## 🔄 Key Changes from Original

### 1. **Organized by Function, Not Type**

- **Old**: `Topology/Topologia.py`, `ISP/ISP.py`
- **New**: `core/topology.py`, `entities/isp.py`

### 2. **Clear Separation of Concerns**

- **config/**: All configuration constants
- **core/**: Core network simulation logic
- **routing/**: Routing algorithms only
- **entities/**: Domain models
- **generators/**: Factory/generator patterns
- **utils/**: Cross-cutting utilities

### 3. **Package Exports**

Each `__init__.py` exports key classes for cleaner imports:

```python
# No need for full paths
from simulador import Topology

# Instead of
from simulador.core.topology import Topologia
```

### 4. **Snake_case File Names**

All files follow PEP 8:

- `GeradorDeTrafego.py` → `traffic_generator.py`
- `Roteamento.py` → `first_fit.py`

### 5. **No Wildcard Imports**

All imports are explicit:

```python
# ❌ Old
from variaveis import *

# ✅ New
from simulador.config import NUMERO_DE_SLOTS, BANDWIDTH
```

## 🎯 Benefits

1. **Better IDE Support**: Clear imports enable better autocomplete
2. **Easier Navigation**: Logical grouping makes code easy to find
3. **Modular**: Clear boundaries between components
4. **Type-Safe**: No import ambiguity for mypy
5. **Testable**: Each module can be tested independently
6. **Scalable**: Easy to add new routing algorithms or entities

## 🧪 Testing

Each module can be tested independently:

```python
# Test routing
from simulador.routing import FirstFit
from simulador.core import Topology

# Test generators
from simulador.generators import TrafficGenerator
```

## 📊 Migration from simulador/

| Old Path                        | New Path                           |
| ------------------------------- | ---------------------------------- |
| `variaveis.py`                  | `config/settings.py`               |
| `PathManager.py`                | `core/path_manager.py`             |
| `Topology/Topologia.py`         | `core/topology.py`                 |
| `Requisicao/requisicao.py`      | `core/request.py`                  |
| `ISP/ISP.py`                    | `entities/isp.py`                  |
| `Roteamento/Roteamento.py`      | `routing/first_fit.py`             |
| `Scenario/GeradorDeCenarios.py` | `generators/scenario_generator.py` |
| `logger.py`                     | `utils/logger.py`                  |
| `registrador.py`                | `utils/metrics.py`                 |

## 🔧 Development

### Adding a New Routing Algorithm

1. Create file in `routing/`:

   ```python
   # routing/my_algorithm.py
   from simulador.routing.base import IRoteamento

   class MyAlgorithm(IRoteamento):
       ...
   ```

2. Export in `routing/__init__.py`:

   ```python
   from simulador.routing.my_algorithm import MyAlgorithm
   __all__.append("MyAlgorithm")
   ```

3. Use it:
   ```python
   from simulador.routing import MyAlgorithm
   ```

## 📝 Notes

- Class names remain in Portuguese (can be translated incrementally)
- Both `simulador/` and `simulador/` can coexist during transition
- All imports use `simulador.` prefix to avoid conflicts
