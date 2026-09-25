"""Tests for restricting cooperation to a subset K of ISPs."""

import math

import pandas as pd

from simulador.analysis.cooperation_metrics import (
    eta_por_isp,
    metricas_cooperacao,
    rotulo_cooperantes,
)
from simulador.coordination import CooperationCoordinator


class _FakeISP:
    def __init__(self, isp_id: int, tamanho: float = 100.0, tau: float = 10.0):
        self.isp_id = isp_id
        self.updates: list[list[int]] = []
        self.datacenter = type(
            "DC", (), {"tamanho_datacenter": tamanho, "tempo_de_reacao": tau}
        )()

    def update_cooperative_weights(self, coop, _topology, _node, _config) -> None:
        self.updates.append(sorted(isp.isp_id for isp in coop))


def test_only_isps_in_k_cooperate() -> None:
    isps = [_FakeISP(i) for i in range(3)]
    coord = CooperationCoordinator(isps, None, 0, None, allowed_isps={0, 2})

    assert coord.register_cooperation(1, 1.0) is False
    assert coord.register_cooperation(0, 2.0) is True
    assert coord.register_cooperation(2, 3.0) is True

    assert coord.cooperating_isps == {0, 2}
    assert isps[1].updates == []  # isolated ISP never gets shared weights
    assert isps[0].updates[-1] == [0, 2]
    assert coord.get_cooperating_isps_for(1) == [isps[1]]


def test_default_allows_everyone() -> None:
    isps = [_FakeISP(i) for i in range(2)]
    coord = CooperationCoordinator(isps, None, 0, None)
    assert coord.register_cooperation(0, 1.0)
    assert coord.register_cooperation(1, 2.0)
    assert coord.cooperating_isps == {0, 1}


def test_empty_k_isolates_everyone() -> None:
    isps = [_FakeISP(i) for i in range(2)]
    coord = CooperationCoordinator(isps, None, 0, None, allowed_isps=set())
    assert not coord.register_cooperation(0, 1.0)
    assert coord.cooperating_isps == set()


def _fake_scenario(isps, t_d=100.0):
    desastre = type("D", (), {"start": t_d})()
    return type("S", (), {"lista_de_isps": isps, "desastre": desastre})()


def test_eta_and_gamma() -> None:
    isps = [_FakeISP(0), _FakeISP(1)]
    scenario = _fake_scenario(isps)
    df = pd.DataFrame(
        {
            "src_isp_index": [0, 0, 1, 1, 0],
            "requisicao_de_migracao": [True, True, True, True, False],
            "bloqueada": [False, False, False, True, True],
            "bandwidth": [60, 60, 50, 50, 10],
            # last migration of ISP 0 is before t_d; background after
            "tempo_criacao": [20.0, 30.0, 40.0, 50.0, 60.0],
        }
    )
    etas = eta_por_isp(df, scenario)
    assert etas == {0: 1.0, 1: 0.5}  # ISP 0 capped at 1

    resumo, por_isp = metricas_cooperacao(df, scenario, [0])
    assert resumo["K"] == "K_0"
    assert math.isclose(resumo["Gamma"], 0.5)
    assert math.isclose(resumo["B_m"], 0.25)
    assert math.isclose(resumo["B_n"], 1.0)
    assert [row["em_K"] for row in por_isp] == [True, False]

    todos, _ = metricas_cooperacao(df, scenario, [0, 1])
    assert math.isnan(todos["Gamma"])  # I \ K empty


def test_rotulo() -> None:
    assert rotulo_cooperantes([]) == "K_none"
    assert rotulo_cooperantes([3, 1]) == "K_1-3"


def test_weighted_router_keeps_isp_path_order(monkeypatch) -> None:
    """The router must try paths in the ISP's (cooperation-weighted) order."""
    from simulador.routing.subnet_weighted_disaster_aware import (
        FirstFitWeightedSubnetDisasterAware as Router,
    )

    monkeypatch.setattr(
        Router,
        "informacoes_sobre_slots",
        staticmethod(lambda _c, _t: ([(0, 199)], 200)),
    )
    # Static router weights that would have flipped the order: the first path
    # is 500 * 1.2 = 600 "weighted", the second 550 * 1.0 = 550.
    monkeypatch.setattr(
        Router,
        "_get_link_weights",
        staticmethod(lambda _i, _t: {(0, 1): 1.2, (1, 2): 1.2}),
    )
    monkeypatch.setattr(Router, "_get_migration_weights", staticmethod(lambda _t: {}))

    topologia = type("T", (), {"caminho_em_funcionamento": lambda _s, _c: True})()
    requisicao = type("R", (), {"src_isp": 0, "bandwidth": 100})()
    caminhos = [
        {"caminho": [0, 1, 2], "distancia": 500, "fator_de_modulacao": 1},
        {"caminho": [0, 3, 2], "distancia": 550, "fator_de_modulacao": 1},
    ]

    ordem, habil = Router._processar_caminhos_isp(caminhos, requisicao, topologia)

    assert habil
    assert [d["caminho"] for d in ordem] == [[0, 1, 2], [0, 3, 2]]
