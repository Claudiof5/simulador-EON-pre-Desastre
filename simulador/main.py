"""Main simulation module for EON pre-disaster simulation.

Contains the Simulator class that orchestrates the entire network simulation,
including traffic generation, routing, disaster events, and data collection.
"""

import random
from collections.abc import Generator
from typing import cast

import networkx as nx
import pandas as pd
import simpy

from simulador import Topology
from simulador.config.settings import NUMERO_DE_REQUISICOES, REQUISICOES_POR_SEGUNDO
from simulador.core.request import Request
from simulador.entities.disaster import Disaster
from simulador.entities.isp import ISP
from simulador.entities.scenario import Scenario
from simulador.generators.scenario_generator import ScenarioGenerator
from simulador.generators.traffic_generator import TrafficGenerator
from simulador.routing.base import RoutingBase
from simulador.utils.logger import Logger
from simulador.utils.metrics import Metrics


class Simulator:
    """Main simulation orchestrator for EON network simulation.

    Manages the complete simulation lifecycle including:
    - Network topology initialization
    - Traffic generation and routing
    - Disaster event coordination
    - Performance metrics collection

    Attributes:
        env: SimPy simulation environment
        topology: Network topology representation
        lista_de_isps: List of Internet Service Providers
        desastre: Disaster event handler
        lista_de_requisicoes: List of network requests
        simulacao_finalizada: Flag indicating simulation completion

    """

    def __init__(
        self,
        env: simpy.Environment,
        topology: nx.Graph,
        status_logger: bool = False,
        cenario: Scenario | None = None,
    ) -> None:
        """Initialize the simulator with environment and topology.

        Args:
            env: SimPy simulation environment
            topology: NetworkX graph representing the network topology
            status_logger: Enable logging for debugging
            cenario: Pre-defined scenario, if None generates a new one

        """
        Logger(status_logger)
        self.inicia_atributos(topology, env, cenario)
        self.simulacao_finalizada = False

    def inicia_atributos(
        self,
        topology: nx.Graph,
        env: simpy.Environment,
        cenario: Scenario | None = None,
    ) -> None:
        """Initialize simulation attributes from topology and scenario.

        Args:
            topology: NetworkX graph representing network topology
            env: SimPy simulation environment
            cenario: Optional pre-defined scenario

        """
        if cenario is None:
            cenario_gerado = cast(Scenario, ScenarioGenerator.gerar_cenario(topology))
            topology, lista_de_isps, desastre, lista_de_requisicoes = (
                cenario_gerado.retorna_atributos()
            )
        else:
            topology, lista_de_isps, desastre, lista_de_requisicoes = (
                cenario.retorna_atributos()
            )

        self.env: simpy.Environment = env
        self.lista_de_isps: list[ISP] = lista_de_isps
        self.desastre: Disaster = desastre
        self.topology: Topology = topology
        self.lista_de_requisicoes: list[Request] = lista_de_requisicoes or []

    def run(self) -> None:
        """Start and run the complete simulation."""
        self.env.process(self._run())
        self.env.run()

    def _run(self) -> Generator:
        """Return Generator for the simulation execution."""
        self.desastre.iniciar_desastre(self)
        self.env.process(Metrics.inicia_registro_janela_deslizante(self.env))
        numero_de_requisicao = (
            len(self.lista_de_requisicoes)
            if self.lista_de_requisicoes is not None
            else NUMERO_DE_REQUISICOES
        )
        for index_requisicao in range(1, numero_de_requisicao + 1):
            yield from self.cria_e_roteia_requisicao(index_requisicao)

        Metrics.finaliza_registro_janela_deslizante()
        self.simulacao_finalizada = True

    def cria_e_roteia_requisicao(self, index_requisicao: int) -> Generator:
        """Create and route a single network request.

        Args:
            index_requisicao: Unique request identifier

        Yields:
            Generator: SimPy timeout events

        """
        requisicao: Request = self.pegar_requisicao(self.topology, index_requisicao)
        yield self.espera_requisicao(requisicao)
        self.roteia_requisicao(requisicao)

        Logger.mensagem_acompanha_requisicoes(
            index_requisicao, int(self.env.now), 10000
        )

    def espera_requisicao(self, requisicao: Request) -> simpy.events.Event:
        """Calculate and return waiting time for a request.

        Args:
            requisicao: The network request to schedule

        Returns:
            simpy.events.Event: Timeout event for request scheduling

        """
        if self.lista_de_requisicoes and requisicao.tempo_criacao is not None:
            return self.env.timeout(requisicao.tempo_criacao - self.env.now)
        return self.env.timeout(random.expovariate(REQUISICOES_POR_SEGUNDO))

    def pegar_requisicao(self, topology: Topology, req_id: int) -> Request:
        """Get the next request from predefined list or generate a new one.

        Args:
            topology: Network topology for request generation
            req_id: Unique request identifier

        Returns:
            Request: The network request to process

        """
        if self.lista_de_requisicoes:
            requisicao = self.lista_de_requisicoes.pop(0)
            Metrics.adiciona_requisicao(requisicao)
            return requisicao
        requisicao = TrafficGenerator.gerar_requisicao(topology, req_id)
        Metrics.adiciona_requisicao(requisicao)
        return requisicao

    def pega_roteador(self, requisicao: Request) -> type[RoutingBase]:
        """Get the appropriate router for a request based on source ISP.

        Args:
            requisicao: Network request requiring routing

        Returns:
            type[RoutingBase]: Router class from the source ISP

        """
        return self.lista_de_isps[requisicao.src_isp_index].roteamento_atual

    def roteia_requisicao(self, requisicao: Request) -> None:
        """Route a request using the appropriate ISP router.

        Args:
            requisicao: Network request to route

        """
        roteador: type[RoutingBase] = self.pega_roteador(requisicao)

        roteador.rotear_requisicao(requisicao, self.topology, self.env)

    def salvar_dataframe(self, nome: str) -> pd.DataFrame:
        """Save simulation results to CSV file.

        Args:
            nome: Base filename for the output file

        Returns:
            pd.DataFrame: DataFrame containing simulation results

        """
        return Metrics.criar_dataframe(nome)
