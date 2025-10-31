"""Module for simulation metrics tracking and registration.

Contains the Metrics singleton class that manages statistics during network
simulation including request counting, blocking rates, and sliding window analysis.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Generator
from copy import deepcopy

import pandas as pd
import simpy

from simulador.core.request import Request

SLIDING_WINDOW_TIME = 10
REGISTER_TIME = 5
COMPONENTE_1 = [num for num in range(1, 9)]
COMPONENTE_2 = [num for num in range(10, 25)]
MAX_DIPONIBILITY_PROPORTION = 1.2
WANTED_DISASTER_NODE = 9


class Metrics:
    """Singleton class for tracking and registering simulation metrics.

    This class manages various statistics during network simulation including:
    - Request counting by class and bandwidth
    - Blocking rates and rerouting statistics
    - Sliding window analysis for traffic patterns
    - Artificial blocking mechanisms
    - Data migration tracking

    The class follows the singleton pattern to ensure consistent state
    across the entire simulation.
    """

    instance: Metrics | None = None

    def __init__(self) -> None:
        """Initialize the Metrics with default metrics and counters.

        Sets up all tracking dictionaries and lists for monitoring:
        - Request counts by class (1, 2, 3) and bandwidth (100-400 Gbps)
        - Blocking statistics for both regular and rerouted requests
        - Sliding window data structures for dynamic analysis
        - Artificial blocking parameters
        """
        self.numero_requisicoes_por_classe: dict[int, int] = {1: 0, 2: 0, 3: 0}
        self.numero_requisicoes_bloqueadas_por_classe: dict[int, int] = {
            1: 0,
            2: 0,
            3: 0,
        }
        self.numero_requisicoes_por_banda: dict[int, int] = {
            100: 0,
            150: 0,
            200: 0,
            250: 0,
            300: 0,
            350: 0,
            400: 0,
        }
        self.numero_requisicoes_bloqueadas_por_banda: dict[int, int] = {
            100: 0,
            150: 0,
            200: 0,
            250: 0,
            300: 0,
            350: 0,
            400: 0,
        }

        self.numero_requisicoes_afetadas_desastre: int = 0

        self.numero_reroteadas_por_classe: dict[int, int] = {1: 0, 2: 0, 3: 0}
        self.numero_reroteadas_bloqueadas_por_classe: dict[int, int] = {
            1: 0,
            2: 0,
            3: 0,
        }
        self.numero_reroteadas_por_banda: dict[int, int] = {
            100: 0,
            150: 0,
            200: 0,
            250: 0,
            300: 0,
            350: 0,
            400: 0,
        }
        self.numero_reroteadas_bloqueadas_por_banda: dict[int, int] = {
            100: 0,
            150: 0,
            200: 0,
            250: 0,
            300: 0,
            350: 0,
            400: 0,
        }

        self.numero_requisicoes_aceitas: int = 0
        self.numero_requisicoes_bloqueadas: int = 0
        self.numero_requisicoes_reroteadas: int = 0
        self.numero_requisicoes_reroteadas_bloqueadas: int = 0
        self.requisicoes: list[Request] = []

        self.tempo_de_migracao_concluida: dict[int, tuple[float, float]] = {}
        self.janela_deslizante_taxa_de_bloqueio_por_par_de_nodes: defaultdict[
            int, list[int]
        ] = defaultdict(lambda: [0, 0])
        self.media_taxa_de_disponibilidade_extra_componente: list[int] = [0, 0]
        self.registro_janela_deslizante: list[dict[int, float | None]] = []
        self.registro_media_taxa_de_disponibilidade_extra_componente: list[
            float | None
        ] = []
        self.current_bloqueio_artificial: dict[int, float] = {
            i: 0.0 for i in range(1, 25) if i != WANTED_DISASTER_NODE
        }
        self.registro_bloqueio_artificial: list[dict[int, float]] = []
        self.sim_finalizada: bool = False

    @staticmethod
    def get_intance() -> Metrics:
        """Get the singleton instance of Metrics.

        Creates a new instance if none exists, otherwise returns the existing one.

        Returns:
            Metrics: The singleton instance of the Metrics class.
        """
        if Metrics.instance is None:
            Metrics.instance = Metrics()
        return Metrics.instance

    @staticmethod
    def inicia_registro_janela_deslizante(env: simpy.Environment) -> Generator:
        """Start the sliding window registration process.

        Continuously monitors and updates sliding window metrics every REGISTER_TIME.
        Calculates availability rates, updates artificial blocking, and maintains
        historical records for analysis.

        Args:
            env (simpy.Environment): The simulation environment.

        Yields:
            simpy.Timeout: Periodic timeouts for registration intervals.
        """
        registrador: Metrics = Metrics.get_intance()
        while not registrador.sim_finalizada:
            yield env.timeout(REGISTER_TIME)
            ## Atualiza a janela deslizante
            new_sliding_window: dict[int, float | None] = {}
            for (
                key,
                value,
            ) in (
                registrador.janela_deslizante_taxa_de_bloqueio_por_par_de_nodes.items()
            ):
                accepted, blocked = value[0], value[1]
                if accepted + blocked != 0:
                    new_sliding_window[key] = accepted / (accepted + blocked)
                else:
                    new_sliding_window[key] = None
            registrador.registro_janela_deslizante.append(new_sliding_window)

            ## Atualiza a media da taxa de bloqueio extra componente
            current_state = deepcopy(
                registrador.media_taxa_de_disponibilidade_extra_componente
            )
            accepted, blocked = current_state[0], current_state[1]
            media_taxa_de_disponibilidade_extra_componente = None
            if accepted + blocked != 0:
                media_taxa_de_disponibilidade_extra_componente = accepted / (
                    accepted + blocked
                )
            registrador.registro_media_taxa_de_disponibilidade_extra_componente.append(
                media_taxa_de_disponibilidade_extra_componente
            )

            ## Atualiza o bloqueio artificial
            new_bloqueio_artificial = deepcopy(registrador.current_bloqueio_artificial)
            for key, _value in new_bloqueio_artificial.items():
                # Skip if media is None or window value is None
                if (
                    media_taxa_de_disponibilidade_extra_componente is None
                    or new_sliding_window.get(key) is None
                ):
                    new_bloqueio_artificial[key] = 0.0
                    continue

                window_value = new_sliding_window[key]
                if window_value is None:
                    new_bloqueio_artificial[key] = 0.0
                    continue

                if (
                    window_value
                    > media_taxa_de_disponibilidade_extra_componente
                    * MAX_DIPONIBILITY_PROPORTION
                ):
                    base_probabilidade = 1 - (
                        media_taxa_de_disponibilidade_extra_componente
                        * MAX_DIPONIBILITY_PROPORTION
                        / window_value
                    )
                    fator_ajuste = 1 + registrador.current_bloqueio_artificial.get(
                        key, 0.0
                    )
                    new_bloqueio_artificial[key] = min(
                        max(base_probabilidade * fator_ajuste, 0.0), 1.0
                    )
                else:
                    current_block = registrador.current_bloqueio_artificial.get(
                        key, 0.0
                    )
                    if current_block > 0:
                        ratio = window_value / (
                            media_taxa_de_disponibilidade_extra_componente
                        )
                        reduction_factor = min(1 - ratio, 0.5)
                        new_bloqueio_artificial[key] = max(
                            current_block * (1 - reduction_factor), 0.0
                        )
                    else:
                        new_bloqueio_artificial[key] = 0.0
            registrador.current_bloqueio_artificial = new_bloqueio_artificial
            registrador.registro_bloqueio_artificial.append(new_bloqueio_artificial)

    @staticmethod
    def get_last_registro_bloqueio_artificial_por_node(node: int) -> float:
        """Get the latest artificial blocking probability for a specific node.

        Args:
            node (int): The node ID to query.

        Returns:
            float: The current artificial blocking probability for the node.
        """
        registrador: Metrics = Metrics.get_intance()
        return registrador.registro_bloqueio_artificial[-1][node]

    @staticmethod
    def finaliza_registro_janela_deslizante() -> None:
        """Mark the sliding window registration as finished.

        Sets the simulation finished flag to stop the sliding window process.
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.sim_finalizada = True

    @staticmethod
    def adiciona_registro_janela_deslizante(
        registro: dict[int, float | None],
    ) -> None:
        """Add a sliding window registry entry.

        Args:
            registro: Registry data mapping node IDs to blocking rates.
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.registro_janela_deslizante.append(registro)

    @staticmethod
    def reseta_registrador() -> None:
        """Reset the singleton instance.

        Creates a new fresh instance of Metrics, effectively
        clearing all accumulated statistics.
        """
        Metrics.instance = Metrics()

    @staticmethod
    def porcentagem_de_dados_enviados(
        isp_id: int, time: int, percentual: float
    ) -> None:
        """Record data migration completion status.

        Args:
            isp_id (int): The ISP identifier.
            time (int): The time when migration completed.
            percentual (float): The percentage of data successfully migrated.
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.tempo_de_migracao_concluida[isp_id] = (time, percentual)

    @staticmethod
    def get_requisicoes() -> list[Request]:
        """Get all registered requests.

        Returns:
            list[Request]: List of all registered request objects.
        """
        registrador: Metrics = Metrics.get_intance()
        return registrador.requisicoes

    @staticmethod
    def registra_bloqueio_artificial(node: int, bloqueio: float) -> None:
        """Register artificial blocking probability for a node.

        Args:
            node (int): The node ID.
            bloqueio (float): The blocking probability to set (0.0 to 1.0).
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.current_bloqueio_artificial[node] = bloqueio

    @staticmethod
    def registra_requisicao_afetada(req: Request) -> None:
        """Register a request affected by disaster.

        Increments counters for disaster-affected requests and tracks
        rerouting statistics by class and bandwidth.

        Args:
            req (Request): The affected request object.
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.numero_requisicoes_afetadas_desastre += 1
        registrador.numero_reroteadas_por_classe[req.class_type] += 1
        registrador.numero_reroteadas_por_banda[req.bandwidth] += 1

    @staticmethod
    def adiciona_requisicao(requisicao: Request) -> None:
        """Add a request to the registry.

        Args:
            requisicao: The request object to add to the list.
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.requisicoes.append(requisicao)

    @staticmethod
    def conta_requisicao_banda(banda: int) -> None:
        """Count a request by its bandwidth requirement.

        Args:
            banda (int): The bandwidth requirement in Gbps.
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.numero_requisicoes_por_banda[banda] += 1

    @staticmethod
    def conta_requisicao_classe(classe: int) -> None:
        """Count a request by its class type.

        Args:
            classe (int): The request class (1, 2, or 3).
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.numero_requisicoes_por_classe[classe] += 1

    @staticmethod
    def atualiza_taxa_de_bloqueio_por_par_de_nodes(
        req: Request, env: simpy.Environment, blocked: bool = False
    ) -> Generator:
        """Update blocking rate tracking for node pairs with sliding window.

        Tracks blocking rates between component groups using a sliding window approach.
        Only processes traffic between COMPONENTE_1 (1-8) and COMPONENTE_2 (10-24).

        Args:
            req (Request): The request being processed.
            env (simpy.Environment): The simulation environment.
            blocked (bool, optional): Whether the request was blocked. Defaults to False.

        Yields:
            simpy.Timeout: Timeout for sliding window duration.
        """
        is_extra_component_traffic = (
            req.src in COMPONENTE_1 and req.dst in COMPONENTE_2
        ) or (req.src in COMPONENTE_2 and req.dst in COMPONENTE_1)
        if not is_extra_component_traffic:
            return
        registrador: Metrics = Metrics.get_intance()
        registrador.media_taxa_de_disponibilidade_extra_componente[blocked] += 1
        registrador.janela_deslizante_taxa_de_bloqueio_por_par_de_nodes[req.src][
            blocked
        ] += 1
        yield env.timeout(SLIDING_WINDOW_TIME)
        registrador.janela_deslizante_taxa_de_bloqueio_por_par_de_nodes[req.src][
            blocked
        ] -= 1
        registrador.media_taxa_de_disponibilidade_extra_componente[blocked] -= 1

    @staticmethod
    def incrementa_numero_requisicoes_aceitas(
        req: Request, env: simpy.Environment
    ) -> None:
        """Increment the count of accepted requests.

        Args:
            req (Request): The accepted request.
            env (simpy.Environment): The simulation environment.
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.numero_requisicoes_aceitas += 1
        env.process(Metrics.atualiza_taxa_de_bloqueio_por_par_de_nodes(req, env))

    @staticmethod
    def incrementa_numero_requisicoes_bloqueadas(
        req: Request, env: simpy.Environment
    ) -> None:
        """Increment the count of blocked requests.

        Tracks blocking by total count, bandwidth, and class type.

        Args:
            req (Request): The blocked request.
            env (simpy.Environment): The simulation environment.
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.numero_requisicoes_bloqueadas += 1
        registrador.numero_requisicoes_bloqueadas_por_banda[req.bandwidth] += 1
        registrador.numero_requisicoes_bloqueadas_por_classe[req.class_type] += 1
        env.process(Metrics.atualiza_taxa_de_bloqueio_por_par_de_nodes(req, env, True))

    @staticmethod
    def incrementa_numero_requisicoes_reroteadas_aceitas(
        req: Request, env: simpy.Environment
    ) -> None:
        """Increment the count of successfully rerouted requests.

        Args:
            req (Request): The rerouted request.
            env (simpy.Environment): The simulation environment.
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.numero_requisicoes_reroteadas += 1
        env.process(Metrics.atualiza_taxa_de_bloqueio_por_par_de_nodes(req, env))

    @staticmethod
    def incrementa_numero_requisicoes_reroteadas_bloqueadas(
        req: Request, env: simpy.Environment
    ) -> None:
        """Increment the count of blocked rerouted requests.

        Tracks rerouted requests that were ultimately blocked,
        categorized by bandwidth and class type.

        Args:
            req (Request): The blocked rerouted request.
            env (simpy.Environment): The simulation environment.
        """
        registrador: Metrics = Metrics.get_intance()
        registrador.numero_requisicoes_reroteadas_bloqueadas += 1
        registrador.numero_reroteadas_bloqueadas_por_banda[req.bandwidth] += 1
        registrador.numero_reroteadas_bloqueadas_por_classe[req.class_type] += 1
        env.process(Metrics.atualiza_taxa_de_bloqueio_por_par_de_nodes(req, env, True))

    @staticmethod
    def printa_parametros() -> None:
        """Print all accumulated simulation parameters and statistics.

        Outputs comprehensive statistics including:
        - Request counts by class and bandwidth
        - Blocking rates for regular and rerouted requests
        - Disaster-affected request counts
        - Data migration completion status
        """
        registrador: Metrics = Metrics.get_intance()
        print(
            "Numero de requisicoes por classe: ",
            registrador.numero_requisicoes_por_classe,
        )
        print(
            "Numero de requisicoes bloqueadas por classe: ",
            registrador.numero_requisicoes_bloqueadas_por_classe,
        )
        print(
            "Numero de requisicoes por banda: ",
            registrador.numero_requisicoes_por_banda,
        )
        print(
            "Numero de requisicoes bloqueadas por banda: ",
            registrador.numero_requisicoes_bloqueadas_por_banda,
        )
        print(
            "Numero de requisicoes reroteadas por classe: ",
            registrador.numero_reroteadas_por_classe,
        )
        print(
            "Numero de requisicoes reroteadas bloqueadas por classe: ",
            registrador.numero_reroteadas_bloqueadas_por_classe,
        )
        print(
            "Numero de requisicoes reroteadas por banda: ",
            registrador.numero_reroteadas_por_banda,
        )
        print(
            "Numero de requisicoes reroteadas bloqueadas por banda: ",
            registrador.numero_reroteadas_bloqueadas_por_banda,
        )
        print(
            "Numero de requisicoes: ",
            registrador.numero_requisicoes_aceitas
            + registrador.numero_requisicoes_bloqueadas,
        )
        print(
            "Numero de requisicoes bloqueadas: ",
            registrador.numero_requisicoes_bloqueadas,
        )
        print(
            "Numero de requisicoes afetadas por desastre: ",
            registrador.numero_requisicoes_afetadas_desastre,
        )
        print(
            "Numero de requisicoes reroteadas aceitas: ",
            registrador.numero_requisicoes_reroteadas,
        )
        print(
            "Numero de requisicoes reroteadas bloqueadas: ",
            registrador.numero_requisicoes_reroteadas_bloqueadas,
        )
        print(
            "Momentos da migração concluída: ", registrador.tempo_de_migracao_concluida
        )

    @staticmethod
    def criar_dataframe(nome: str) -> pd.DataFrame:
        """Create a DataFrame from all registered requests and save to CSV.

        Args:
            nome (str): The base filename for the CSV output.

        Returns:
            pd.DataFrame: DataFrame containing all request data.
        """
        registrador: Metrics = Metrics.get_intance()

        data = {}
        for req in registrador.requisicoes:
            data[req.req_id] = req.retorna_tupla_chave_dicionario_dos_atributos()[1]

        df = pd.DataFrame.from_dict(data, orient="index")
        df.reset_index(inplace=True)
        df.rename(columns={"index": "Index da Requisição"}, inplace=True)

        # Sort by tempo_criacao to ensure correct temporal order
        # The requisicoes list might not be in tempo_criacao order if requests were
        # added from multiple sources (main loop, runtime migrations, etc.)
        if "tempo_criacao" in df.columns:
            df = df.sort_values(by="tempo_criacao", na_position="last")

        df.to_csv(f"{nome}.csv")
        return df

    @staticmethod
    def cria_dataframe_janela_deslizante(nome: str) -> pd.DataFrame | None:
        """Create DataFrame from sliding window registry data.

        Args:
            nome (str): Base filename for the CSV output.

        Returns:
            pd.DataFrame: DataFrame with sliding window data over time.
        """
        registrador: Metrics = Metrics.get_intance()
        df = pd.DataFrame(registrador.registro_janela_deslizante)
        df.to_csv(f"{nome}_sliding_window.csv")
        return df

    @staticmethod
    def cria_dataframe_media_taxa_de_disponibilidade_extra_componente(
        nome: str,
    ) -> pd.DataFrame:
        """Create DataFrame from extra component availability rate data.

        Args:
            nome (str): Base filename for the CSV output.

        Returns:
            pd.DataFrame: DataFrame with availability rates over time.
        """
        registrador: Metrics = Metrics.get_intance()
        df = pd.DataFrame(
            registrador.registro_media_taxa_de_disponibilidade_extra_componente
        )
        df.to_csv(f"{nome}_media_taxa_de_disponibilidade_extra_componente.csv")
        return df

    @staticmethod
    def cria_dataframe_bloqueio_artificial(nome: str) -> pd.DataFrame:
        """Create DataFrame from artificial blocking data.

        Args:
            nome (str): Base filename for the CSV output.

        Returns:
            pd.DataFrame: DataFrame with artificial blocking probabilities over time.
        """
        registrador: Metrics = Metrics.get_intance()
        df = pd.DataFrame(registrador.registro_bloqueio_artificial)
        df.to_csv(f"{nome}_bloqueio_artificial.csv")
        return df

    @staticmethod
    def salva_resutados(caminho: str) -> None:
        """Save all results to a JSON file.

        Serializes the entire Metrics state to JSON format.

        Args:
            caminho (str): The file path where to save the JSON results.
        """
        registrador: Metrics = Metrics.get_intance()
        with open(f"{caminho}", "w", encoding="utf-8") as f:
            json.dump(registrador.__dict__, f, indent=4)
