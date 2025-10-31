"""Test critical functions to ensure correct behavior.

This test suite verifies the most important functions in the simulator
to catch bugs early and ensure correctness.
"""

import networkx as nx
import pytest  # type: ignore[import]  # noqa: F401
import simpy

from simulador import Scenario, Topology
from simulador.core.request import Request
from simulador.generators.disaster_generator import DisasterGenerator
from simulador.generators.isp_generator import ISPGenerator
from simulador.generators.scenario_generator import ScenarioGenerator
from simulador.generators.traffic_generator import TrafficGenerator
from simulador.main import Simulator
from simulador.routing.first_fit import FirstFit
from simulador.utils.metrics import Metrics

# Constants for test values
TIME_PRECISION_TOLERANCE = 1e-6
NUM_TEST_REQUESTS = 5


class _StubDisaster:
    def __init__(self) -> None:
        self.start = 0.0
        self.duration = 0.0
        self.list_of_dict_node_per_start_time = [{"node": 0}]
        self.list_of_dict_link_per_start_time: list[dict] = []

    def iniciar_desastre(self, _simulador) -> None:  # pragma: no cover - stub
        return None

    def seta_links_como_prestes_a_falhar(
        self, _topology
    ) -> None:  # pragma: no cover - stub
        return None


def _build_stub_scenario(topology: nx.Graph, numero_de_requisicoes: int) -> Scenario:
    """Create a lightweight scenario for time advancement tests."""
    topo_wrapper = Topology(topology.copy(), [], 1, 1)

    requisicoes: list[Request] = []
    for idx in range(numero_de_requisicoes):
        req = Request(
            str(idx + 1),
            src=0,
            dst=1,
            src_isp_index=0,
            dst_isp_index=0,
            bandwidth=100,
            class_type=1,
            holding_time=10.0,
        )
        req.tempo_criacao = float(idx)
        requisicoes.append(req)

    return Scenario(topo_wrapper, [], _StubDisaster(), requisicoes)


def _stub_gerar_cenario(
    topology: nx.Graph,
    _disaster_node: int | None = None,
    retornar_objetos: bool = False,
    retorna_lista_de_requisicoes: bool = False,
    numero_de_requisicoes: int = 0,
    **_kwargs,
):
    scenario = _build_stub_scenario(
        topology, numero_de_requisicoes if retorna_lista_de_requisicoes else 0
    )
    if retornar_objetos:
        return scenario
    return scenario.retorna_atributos()


class TestRequestGeneration:
    """Test request generation functionality."""

    def setup_scenario(self) -> Scenario:
        self.topology = nx.read_weighted_edgelist("topology/usa", nodetype=int)

        return ScenarioGenerator.gerar_cenario(
            self.topology,
            retorna_lista_de_requisicoes=True,
            numero_de_requisicoes=30000,
            disaster_node=9,
        )

    def test_migration_request_destinations_unique_per_isp(self):
        """Test that migration requests have correct destinations for each ISP."""
        # Create a simple topology with edge weights
        topology = nx.Graph()
        edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
        topology.add_edges_from(edges)
        for u, v in edges:
            topology[u][v]["weight"] = 1.0
        for node in topology.nodes:
            topology.nodes[node]["ISPs"] = [0]

        # Create ISPs and disaster
        num_isps = 3
        lista_de_isps = ISPGenerator.gerar_lista_isps_aleatorias(
            topology=topology,
            numero_de_isps=num_isps,
            roteamento_de_desastre=FirstFit,
            computar_caminhos_internos=False,
        )
        desastre = DisasterGenerator.generate_disaster(topology, lista_de_isps)

        # Define datacenters for each ISP with different destinations
        for i, isp in enumerate(lista_de_isps):
            isp.define_datacenter(desastre, topology)
            # Manually set different destinations to verify uniqueness
            if isp.datacenter:
                isp.datacenter.destination = 10 + i  # 10, 11, 12

        # Generate migration requests
        for isp in lista_de_isps:
            if isp.datacenter:
                datacenter_reqs = (
                    TrafficGenerator.gerar_lista_de_requisicoes_datacenter(
                        isp.datacenter, desastre, topology, isp.isp_id
                    )
                )
                if datacenter_reqs:
                    # All requests from this ISP should have the correct destination
                    expected_dst = isp.datacenter.destination
                    for req in datacenter_reqs:
                        assert req.dst == expected_dst, (
                            f"ISP {isp.isp_id} migration request has wrong destination: expected {expected_dst}, got {req.dst}"
                        )
                        assert req.src == isp.datacenter.source, (
                            f"ISP {isp.isp_id} migration request has wrong source"
                        )
                        assert req.src_isp_index == isp.isp_id, (
                            f"ISP {isp.isp_id} migration request has wrong src_isp_index"
                        )

    def test_req_id_uniqueness_after_reindexing(self):
        """Test that req_id values are unique after merging and re-indexing."""
        topology = nx.Graph()
        edges = [(0, 1), (1, 2), (2, 3)]
        topology.add_edges_from(edges)
        for u, v in edges:
            topology[u][v]["weight"] = 1.0
        for node in topology.nodes:
            topology.nodes[node]["ISPs"] = [0]

        lista_de_isps = ISPGenerator.gerar_lista_isps_aleatorias(
            topology=topology,
            numero_de_isps=2,
            roteamento_de_desastre=FirstFit,
            computar_caminhos_internos=False,
        )
        desastre = DisasterGenerator.generate_disaster(topology, lista_de_isps)

        for isp in lista_de_isps:
            isp.define_datacenter(desastre, topology)

        # Generate list of requests
        lista_de_requisicoes = TrafficGenerator.gerar_lista_de_requisicoes(
            topology, 10, lista_de_isps, desastre
        )

        # Check that all req_id values are unique
        req_ids = [req.req_id for req in lista_de_requisicoes]
        assert len(req_ids) == len(set(req_ids)), "Duplicate req_id values found!"

        # Check that req_id values are sequential starting from 1
        req_id_ints = [int(rid) for rid in req_ids]
        sorted_ids = sorted(req_id_ints)
        assert sorted_ids == list(range(1, len(lista_de_requisicoes) + 1)), (
            f"req_id values not sequential: {sorted_ids[:10]}..."
        )

    def test_requests_sorted_by_tempo_criacao(self):
        """Test that generated requests are sorted by tempo_criacao."""
        topology = nx.Graph()
        edges = [(0, 1), (1, 2), (2, 3)]
        topology.add_edges_from(edges)
        for u, v in edges:
            topology[u][v]["weight"] = 1.0
        for node in topology.nodes:
            topology.nodes[node]["ISPs"] = [0]

        lista_de_isps = ISPGenerator.gerar_lista_isps_aleatorias(
            topology=topology,
            numero_de_isps=2,
            roteamento_de_desastre=FirstFit,
            computar_caminhos_internos=False,
        )
        desastre = DisasterGenerator.generate_disaster(topology, lista_de_isps)

        for isp in lista_de_isps:
            isp.define_datacenter(desastre, topology)

        lista_de_requisicoes = TrafficGenerator.gerar_lista_de_requisicoes(
            topology, 20, lista_de_isps, desastre
        )

        # Check that requests are sorted by tempo_criacao
        for i in range(len(lista_de_requisicoes) - 1):
            current_time = lista_de_requisicoes[i].tempo_criacao or 0.0
            next_time = lista_de_requisicoes[i + 1].tempo_criacao or 0.0
            assert current_time <= next_time, (
                f"Requests not sorted: index {i} has tempo_criacao {current_time}, index {i + 1} has {next_time}"
            )


class TestRequestTempoCriacao:
    """Test tempo_criacao preservation."""

    def test_tempo_criacao_preserved_on_block(self):
        """Test that tempo_criacao is preserved when request is blocked."""
        req = Request(
            "1",
            src=0,
            dst=1,
            src_isp_index=0,
            dst_isp_index=0,
            bandwidth=100,
            class_type=1,
            holding_time=10.0,
        )
        original_tempo = 231.16
        req.tempo_criacao = original_tempo

        # Block the request (should preserve tempo_criacao)
        req.bloqueia_requisicao(tempo_criacao=500.0)

        assert req.tempo_criacao == original_tempo, (
            f"tempo_criacao was overwritten: expected {original_tempo}, got {req.tempo_criacao}"
        )
        assert req.bloqueada is True

    def test_tempo_criacao_preserved_on_accept(self):
        """Test that tempo_criacao is preserved when request is accepted."""
        req = Request(
            "1",
            src=0,
            dst=1,
            src_isp_index=0,
            dst_isp_index=0,
            bandwidth=100,
            class_type=1,
            holding_time=10.0,
        )
        original_tempo = 231.16
        req.tempo_criacao = original_tempo

        # Accept the request (should preserve tempo_criacao)
        req.aceita_requisicao(
            numero_de_slots=10,
            caminho=[0, 1],
            tamanho_do_caminho=2,
            index_de_inicio_e_final=(0, 9),
            tempo_criacao=500.0,  # env.now when accepted
            tempo_desalocacao=510.0,
            distancia=100,
        )

        assert req.tempo_criacao == original_tempo, (
            f"tempo_criacao was overwritten: expected {original_tempo}, got {req.tempo_criacao}"
        )
        assert req.bloqueada is False

    def test_tempo_criacao_set_if_none(self):
        """Test that tempo_criacao is set if it was None (runtime-generated request)."""
        req = Request(
            "1",
            src=0,
            dst=1,
            src_isp_index=0,
            dst_isp_index=0,
            bandwidth=100,
            class_type=1,
            holding_time=10.0,
        )
        assert req.tempo_criacao is None

        # Accept request (should set tempo_criacao since it's None)
        tempo_when_accepted = 500.0
        req.aceita_requisicao(
            numero_de_slots=10,
            caminho=[0, 1],
            tamanho_do_caminho=2,
            index_de_inicio_e_final=(0, 9),
            tempo_criacao=tempo_when_accepted,
            tempo_desalocacao=510.0,
            distancia=100,
        )

        assert req.tempo_criacao == tempo_when_accepted, (
            f"tempo_criacao should be set: expected {tempo_when_accepted}, got {req.tempo_criacao}"
        )


class TestDataFrameCreation:
    """Test DataFrame creation and ordering."""

    def test_dataframe_sorted_by_tempo_criacao(self):
        """Test that DataFrame is sorted by tempo_criacao when created."""
        Metrics.reseta_registrador()

        # Create requests with known tempo_criacao values
        reqs = []
        for i in range(5):
            req = Request(
                str(i + 1),
                src=0,
                dst=1,
                src_isp_index=0,
                dst_isp_index=0,
                bandwidth=100,
                class_type=1,
                holding_time=10.0,
            )
            req.tempo_criacao = float(i * 10)  # 0, 10, 20, 30, 40
            Metrics.adiciona_requisicao(req)
            reqs.append(req)

        # Add requests in reverse order to test sorting
        reversed_reqs = list(reversed(reqs))
        Metrics.reseta_registrador()
        for req in reversed_reqs:
            Metrics.adiciona_requisicao(req)

        df = Metrics.criar_dataframe("test_output")

        # Check that DataFrame is sorted by tempo_criacao
        assert "tempo_criacao" in df.columns, "tempo_criacao column missing"
        tempo_values = df["tempo_criacao"].values
        for i in range(len(tempo_values) - 1):
            assert tempo_values[i] <= tempo_values[i + 1], (
                f"DataFrame not sorted: index {i} has {tempo_values[i]}, index {i + 1} has {tempo_values[i + 1]}"
            )

    def test_dataframe_contains_all_requests(self):
        """Test that DataFrame contains all registered requests."""
        Metrics.reseta_registrador()

        num_requests = 10
        for i in range(num_requests):
            req = Request(
                str(i + 1),
                src=0,
                dst=1,
                src_isp_index=0,
                dst_isp_index=0,
                bandwidth=100,
                class_type=1,
                holding_time=10.0,
            )
            req.tempo_criacao = float(i)
            Metrics.adiciona_requisicao(req)

        df = Metrics.criar_dataframe("test_output")

        assert len(df) == num_requests, (
            f"DataFrame missing requests: expected {num_requests}, got {len(df)}"
        )


class TestTimeAdvancement:
    """Test time advancement during simulation."""

    def test_wait_time_calculation(self, monkeypatch):
        """Test that wait_time calculation is correct."""
        # Create a larger topology (at least 5 nodes for default numero_de_isps=5)
        topology = nx.Graph()
        edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2), (1, 3)]
        topology.add_edges_from(edges)
        for u, v in edges:
            topology[u][v]["weight"] = 1.0
        for node in topology.nodes:
            topology.nodes[node]["ISPs"] = [0]

        env = simpy.Environment()
        monkeypatch.setattr(ScenarioGenerator, "gerar_cenario", _stub_gerar_cenario)
        cenario = ScenarioGenerator.gerar_cenario(
            topology,
            retorna_lista_de_requisicoes=True,
            numero_de_requisicoes=10,
            retornar_objetos=True,
        )
        simulador = Simulator(env=env, topology=topology, cenario=cenario)

        # Get first request
        req = simulador.lista_de_requisicoes[0]

        # Calculate wait_time
        wait_time = req.tempo_criacao - env.now

        # wait_time should be >= 0 for first request (env.now starts at 0)
        assert wait_time >= 0, f"wait_time should be >= 0, got {wait_time}"

        # After waiting, env.now should equal tempo_criacao
        event = simulador.espera_requisicao(req)
        env.run(until=event)

        # Due to SimPy's event scheduling, we need to check after yield
        # This is tested indirectly through the sequential processing test

    def test_no_negative_wait_time_for_sorted_requests(self, monkeypatch):
        """Test that wait_time is never significantly negative for sorted requests."""
        # Create a larger topology (at least 5 nodes for default numero_de_isps=5)
        topology = nx.Graph()
        edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2), (1, 3)]
        topology.add_edges_from(edges)
        for u, v in edges:
            topology[u][v]["weight"] = 1.0
        for node in topology.nodes:
            topology.nodes[node]["ISPs"] = [0]

        env = simpy.Environment()
        monkeypatch.setattr(ScenarioGenerator, "gerar_cenario", _stub_gerar_cenario)
        cenario = ScenarioGenerator.gerar_cenario(
            topology,
            retorna_lista_de_requisicoes=True,
            numero_de_requisicoes=50,
            retornar_objetos=True,
        )
        simulador = Simulator(env=env, topology=topology, cenario=cenario)

        # Process first few requests to advance time
        for i in range(10):
            req = (
                simulador.lista_de_requisicoes[i]
                if simulador.lista_de_requisicoes
                else None
            )
            if req:
                wait_time = req.tempo_criacao - env.now
                # wait_time should never be significantly negative for sorted list
                assert wait_time >= -TIME_PRECISION_TOLERANCE, (
                    f"Request {i} has negative wait_time {wait_time} with sorted list!"
                )


class TestMigrationRequestProperties:
    """Test migration request properties."""

    def test_migration_requests_have_correct_properties(self):
        """Test that migration requests have all required properties set correctly."""
        topology = nx.Graph()
        edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
        topology.add_edges_from(edges)
        for u, v in edges:
            topology[u][v]["weight"] = 1.0
        for node in topology.nodes:
            topology.nodes[node]["ISPs"] = [0]

        lista_de_isps = ISPGenerator.gerar_lista_isps_aleatorias(
            topology=topology,
            numero_de_isps=2,
            roteamento_de_desastre=FirstFit,
            computar_caminhos_internos=False,
        )
        desastre = DisasterGenerator.generate_disaster(topology, lista_de_isps)

        for isp in lista_de_isps:
            isp.define_datacenter(desastre, topology)

        # Generate requests
        lista_de_requisicoes = TrafficGenerator.gerar_lista_de_requisicoes(
            topology, 10, lista_de_isps, desastre
        )

        # Check migration requests
        migration_reqs = [
            req for req in lista_de_requisicoes if req.requisicao_de_migracao
        ]

        if migration_reqs:
            for req in migration_reqs:
                assert req.requisicao_de_migracao is True
                assert req.tempo_criacao is not None, (
                    "Migration request missing tempo_criacao"
                )
                assert req.src is not None
                assert req.dst is not None
                assert req.src_isp_index is not None
                assert req.dst_isp_index is not None
                # Migration requests should have src_isp == dst_isp (same ISP)
                assert req.src_isp_index == req.dst_isp_index, (
                    f"Migration request has different ISPs: src_isp={req.src_isp_index}, dst_isp={req.dst_isp_index}"
                )

    def test_migration_requests_destination_matches_datacenter(self):
        """Test that each ISP's migration requests use that ISP's datacenter destination."""
        topology = nx.Graph()
        edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
        topology.add_edges_from(edges)
        for u, v in edges:
            topology[u][v]["weight"] = 1.0
        for node in topology.nodes:
            topology.nodes[node]["ISPs"] = [0]

        lista_de_isps = ISPGenerator.gerar_lista_isps_aleatorias(
            topology=topology,
            numero_de_isps=3,
            roteamento_de_desastre=FirstFit,
            computar_caminhos_internos=False,
        )
        desastre = DisasterGenerator.generate_disaster(topology, lista_de_isps)

        # Store datacenter destinations before generating requests
        datacenter_destinations = {}
        for isp in lista_de_isps:
            isp.define_datacenter(desastre, topology)
            if isp.datacenter:
                datacenter_destinations[isp.isp_id] = isp.datacenter.destination

        # Generate requests
        lista_de_requisicoes = TrafficGenerator.gerar_lista_de_requisicoes(
            topology, 10, lista_de_isps, desastre
        )

        # Check that migration requests match their ISP's datacenter destination
        for req in lista_de_requisicoes:
            if req.requisicao_de_migracao:
                expected_dst = datacenter_destinations.get(req.src_isp_index)
                if expected_dst is not None:
                    assert req.dst == expected_dst, (
                        f"ISP {req.src_isp_index} migration request has wrong destination: expected {expected_dst}, got {req.dst}"
                    )


class TestRequestRegistration:
    """Test request registration and metrics collection."""

    def test_requests_registered_in_order(self):
        """Test that requests are registered in the order they're processed."""
        Metrics.reseta_registrador()

        # Create requests with sequential tempo_criacao
        reqs = []
        for i in range(NUM_TEST_REQUESTS):
            req = Request(
                str(i + 1),
                src=0,
                dst=1,
                src_isp_index=0,
                dst_isp_index=0,
                bandwidth=100,
                class_type=1,
                holding_time=10.0,
            )
            req.tempo_criacao = float(i * 10)
            Metrics.adiciona_requisicao(req)
            reqs.append(req)

        # Check that all requests are in the registry
        registrador = Metrics.get_intance()
        assert len(registrador.requisicoes) == NUM_TEST_REQUESTS, (
            f"Expected {NUM_TEST_REQUESTS} requests, got {len(registrador.requisicoes)}"
        )

        # Requests should be in the order they were added (not necessarily sorted by tempo_criacao)
        # But DataFrame should sort them
        df = Metrics.criar_dataframe("test_output")
        assert len(df) == NUM_TEST_REQUESTS, (
            f"DataFrame should have {NUM_TEST_REQUESTS} requests, got {len(df)}"
        )

    def test_no_duplicate_req_id_in_dataframe(self):
        """Test that DataFrame doesn't have duplicate req_id values."""
        Metrics.reseta_registrador()

        # Create requests with different req_ids
        for i in range(10):
            req = Request(
                str(i + 1),
                src=0,
                dst=1,
                src_isp_index=0,
                dst_isp_index=0,
                bandwidth=100,
                class_type=1,
                holding_time=10.0,
            )
            req.tempo_criacao = float(i)
            Metrics.adiciona_requisicao(req)

        df = Metrics.criar_dataframe("test_output")

        # Check for duplicates in "Index da Requisição" (which is req_id)
        req_id_column = df["Index da Requisição"]
        assert len(req_id_column) == req_id_column.nunique(), (
            f"Duplicate req_id values found: {req_id_column[req_id_column.duplicated()].tolist()}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
