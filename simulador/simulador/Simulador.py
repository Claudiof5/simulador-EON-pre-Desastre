"""Main simulation module for EON pre-disaster simulation.

Contains the Simulador class that orchestrates the entire network simulation,
including traffic generation, routing, disaster events, and data collection.
"""

import random
from collections.abc import Generator

import networkx as nx
import simpy
from Cenario.Cenario import Cenario
from Cenario.GeradorDeCenarios import GeradorDeCenarios
from Desastre.Desastre import Desastre
from ISP.ISP import ISP
from logger import Logger
from registrador import Registrador
from Requisicao.GeradorDeTrafego import GeradorDeTrafego
from Requisicao.requisicao import Requisicao
from Roteamento.IRoteamento import IRoteamento
from Topology.Topologia import Topologia
from variaveis import NUMERO_DE_REQUISICOES, REQUISICOES_POR_SEGUNDO


class Simulador:
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
        cenario: Cenario | None = None,
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
        self, topology: nx.Graph, env: simpy.Environment, cenario: Cenario | None = None
    ) -> None:
        """Initialize simulation attributes from topology and scenario.

        Args:
            topology: NetworkX graph representing network topology
            env: SimPy simulation environment
            cenario: Optional pre-defined scenario

        """
        if cenario is None:
            topology, lista_de_isps, desastre, lista_de_requisicoes = (
                GeradorDeCenarios.gerar_cenario(topology)
            )
        else:
            topology, lista_de_isps, desastre, lista_de_requisicoes = (
                cenario.retorna_atributos()
            )

        self.env: simpy.Environment = env
        self.lista_de_isps: list[ISP] = lista_de_isps
        self.desastre: Desastre = desastre
        self.topology: Topologia = topology
        self.lista_de_requisicoes: list[Requisicao] = lista_de_requisicoes

    def run(self) -> None:
        """Start and run the complete simulation."""
        self.env.process(self._run())
        self.env.run()

    def _run(self) -> Generator:
        """Return Generator for the simulation execution."""
        self.desastre.iniciar_desastre(self)
        self.env.process(Registrador.inicia_registro_janela_deslizante(self.env))
        numero_de_requisicao = (
            len(self.lista_de_requisicoes)
            if self.lista_de_requisicoes is not None
            else NUMERO_DE_REQUISICOES
        )
        for index_requisicao in range(1, numero_de_requisicao + 1):
            yield from self.cria_e_roteia_requisicao(index_requisicao)

        Registrador.finaliza_registro_janela_deslizante()
        self.simulacao_finalizada = True

    def cria_e_roteia_requisicao(self, index_requisicao: int) -> Generator:
        """Create and route a single network request.

        Args:
            index_requisicao: Unique request identifier

        Yields:
            Generator: SimPy timeout events

        """
        requisicao: Requisicao = self.pegar_requisicao(self.topology, index_requisicao)
        yield self.espera_requisicao(requisicao)
        self.roteia_requisicao(requisicao)

        Logger.mensagem_acompanha_requisicoes(index_requisicao, self.env.now, 10000)

    def espera_requisicao(self, requisicao: Requisicao) -> simpy.events.Event:
        """Calculate and return waiting time for a request.

        Args:
            requisicao: The network request to schedule

        Returns:
            simpy.events.Event: Timeout event for request scheduling

        """
        if self.lista_de_requisicoes:
            return self.env.timeout(requisicao.tempo_criacao - self.env.now)
        return self.env.timeout(random.expovariate(REQUISICOES_POR_SEGUNDO))

    def pegar_requisicao(self, topology: Topologia, req_id: int) -> Requisicao:
        """Get the next request from predefined list or generate a new one.

        Args:
            topology: Network topology for request generation
            req_id: Unique request identifier

        Returns:
            Requisicao: The network request to process

        """
        if self.lista_de_requisicoes:
            requisicao = self.lista_de_requisicoes.pop(0)
            Registrador.adiciona_requisicao(requisicao)
            return requisicao
        requisicao = GeradorDeTrafego.gerar_requisicao(topology, req_id)
        Registrador.adiciona_requisicao(requisicao)
        return requisicao

    def pega_roteador(self, requisicao: Requisicao) -> IRoteamento:
        """Get the appropriate router for a request based on source ISP.

        Args:
            requisicao: Network request requiring routing

        Returns:
            IRoteamento: Router instance from the source ISP

        """
        return self.lista_de_isps[requisicao.src_isp_index].roteamento_atual

    def roteia_requisicao(self, requisicao: Requisicao) -> None:
        """Route a request using the appropriate ISP router.

        Args:
            requisicao: Network request to route

        """
        roteador: IRoteamento = self.pega_roteador(requisicao)

        roteador.rotear_requisicao(requisicao, self.topology, self.env)

    def salvar_dataframe(self, nome: str) -> None:
        """Save simulation results to CSV file.

        Args:
            nome: Base filename for the output file

        Returns:
            pd.DataFrame: DataFrame containing simulation results

        """
        return Registrador.criar_dataframe(nome)
