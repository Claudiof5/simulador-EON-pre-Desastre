"""Tests for migration-corridor protection on links exclusive to K."""

import networkx as nx

from simulador.coordination.migration_protection import MigrationProtection


class _DC:
    def __init__(self, source: int, destination: int) -> None:
        self.source = source
        self.destination = destination


class _ISP:
    def __init__(self, isp_id: int, corredor: list[int]) -> None:
        self.isp_id = isp_id
        self.datacenter = _DC(corredor[0], corredor[-1])
        self.weighted_caminhos_internos_isp_durante_desastre = {
            corredor[0]: {corredor[-1]: [{"caminho": corredor}]}
        }


class _Req:
    def __init__(self, migracao: bool = False) -> None:
        self.requisicao_de_migracao = migracao


def _grafo() -> nx.Graph:
    # 0-1 used by ISPs 0 and 1; 1-2 only by ISP 0; 2-3 by ISPs 0 and 2
    g = nx.Graph()
    g.add_edge(0, 1, ISPs=[0, 1])
    g.add_edge(1, 2, ISPs=[0])
    g.add_edge(2, 3, ISPs=[0, 2])
    return g


def _protecao(modo="reserva", escopo="cooperacao", **kw) -> MigrationProtection:
    isps = [_ISP(0, [0, 1, 2, 3]), _ISP(1, [0, 1]), _ISP(2, [2, 3])]
    return MigrationProtection(
        isps, _grafo(), numero_de_slots=100, t_d=50.0, modo=modo,
        escopo=escopo, reserva_fracao=0.2, **kw
    )


def _dp(caminho, janelas, precisa=10) -> dict:
    return {
        "caminho": caminho,
        "lista_de_inicios_e_fins": janelas,
        "maior_janela_contigua_continua": max(f - i + 1 for i, f in janelas),
        "numero_slots_necessarios": precisa,
    }


def test_links_exclusive_to_k_on_corridor() -> None:
    prot = _protecao()
    prot.atualizar(0, {0})  # ISP 0 alone: only 1-2 is exclusive
    assert set(prot.protegidos) == {frozenset((1, 2))}
    prot.atualizar(1, {0, 1})  # with ISP 1, link 0-1 becomes exclusive too
    assert set(prot.protegidos) == {frozenset((1, 2)), frozenset((0, 1))}
    assert frozenset((2, 3)) not in prot.protegidos  # ISP 2 is not in K


def test_isolated_scope_ignores_cooperation() -> None:
    prot = _protecao(escopo="isolado")
    prot.atualizar(0, set())
    prot.atualizar(1, set())
    assert set(prot.protegidos) == {frozenset((1, 2))}  # only sigma == 1 links


def test_reservation_clips_background_but_not_migration() -> None:
    prot = _protecao()
    prot.atualizar(0, {0})
    dp = _dp([0, 1, 2], [(70, 99)])  # only free space is in the reserved top 20
    novos, habil = prot.aplicar(_Req(), [dp], agora=10.0)
    assert novos[0]["lista_de_inicios_e_fins"] == [(70, 79)]
    assert habil  # 10 slots still fit below the reserve
    novos, habil = prot.aplicar(_Req(), [_dp([0, 1, 2], [(75, 99)])], agora=10.0)
    assert not habil  # only 5 slots left below the reserve
    novos, habil = prot.aplicar(_Req(True), [_dp([0, 1, 2], [(75, 99)])], 10.0)
    assert habil and novos[0]["lista_de_inicios_e_fins"] == [(75, 99)]


def test_inactive_after_failure_and_on_unprotected_paths() -> None:
    prot = _protecao()
    prot.atualizar(0, {0})
    dp = _dp([0, 1, 2], [(75, 99)])
    assert prot.aplicar(_Req(), [dp], agora=60.0)[0] == [dp]  # after t_d
    livre = _dp([2, 3], [(75, 99)])
    assert prot.aplicar(_Req(), [livre], agora=10.0)[0] == [livre]


def test_adaptive_follows_migration_blocking() -> None:
    prot = _protecao(modo="adaptativo", p_max=1.0)
    prot.atualizar(0, {0})
    dp = _dp([0, 1, 2], [(0, 99)])
    assert prot.aplicar(_Req(), [dp], 10.0)[0] == [dp]  # no migration blocked yet
    for _ in range(10):
        prot.registra_migracao(0, bloqueada=True)
    novos, habil = prot.aplicar(_Req(), [dp], 10.0)
    assert novos == [] and not habil  # p = 1: kept off the protected link
    assert prot.normais_restringidas == 1


def _protecao_demanda(**kw) -> MigrationProtection:
    isps = [_ISP(0, [0, 1, 2, 3]), _ISP(1, [0, 1]), _ISP(2, [2, 3])]
    for isp in isps:
        isp.datacenter.tamanho_datacenter = 1250.0
    return MigrationProtection(
        isps, _grafo(), numero_de_slots=100, t_d=50.0, modo="reserva_demanda",
        caminhos_corredor=1, holding_time=1.0, slot_size=12.5, **kw
    )


def test_demand_reservation_follows_remaining_migration() -> None:
    prot = _protecao_demanda()
    prot.atualizar(0, {0})
    link = frozenset((1, 2))  # only ISP 0 uses it
    # 1250 left over 10 s = 125 per second -> 125 * 1 s / 12.5 = 10 slots
    assert prot.reserva_link(link, agora=40.0) == 10
    # Background request: only slots below 100 - 10 = 90 remain usable
    novos, _ = prot.aplicar(_Req(), [_dp([0, 1, 2], [(80, 99)])], agora=40.0)
    assert novos[0]["lista_de_inicios_e_fins"] == [(80, 89)]
    # Half migrated -> half the reserve; finished -> no reserve
    prot.registra_migracao(0, bloqueada=False, banda=625.0)
    assert prot.reserva_link(link, agora=40.0) == 5
    prot.registra_migracao(0, bloqueada=True, banda=625.0)  # blocked: not counted
    assert prot.reserva_link(link, agora=40.0) == 5
    prot.registra_migracao(0, bloqueada=False, banda=625.0)
    assert prot.reserva_link(link, agora=40.0) == 0


def test_demand_reservation_sums_owners_and_caps_at_link_size() -> None:
    prot = _protecao_demanda(margem=5.0)
    prot.atualizar(0, {0, 1})
    prot.atualizar(1, {0, 1})
    link = frozenset((0, 1))  # main path of ISPs 0 and 1, exclusive to {0, 1}
    assert prot.protegidos[link] == {0, 1}
    assert prot.reserva_link(link, agora=40.0) == 100  # 2 * 5 * 10 = 100, capped
    assert prot.reserva_link(link, agora=45.0) == 100  # would be 200: capped


def test_demand_corridor_reserves_on_backup_paths_with_their_modulation() -> None:
    # ISP 0 migrates 0 -> 3: main path 0-1-2-3 (factor 2), backup 0-4-3 (factor 1)
    g = _grafo()
    g.add_edge(0, 4, ISPs=[0])
    g.add_edge(4, 3, ISPs=[0])
    isp = _ISP(0, [0, 1, 2, 3])
    isp.datacenter.tamanho_datacenter = 1250.0
    isp.weighted_caminhos_internos_isp_durante_desastre = {
        0: {3: [{"caminho": [0, 1, 2, 3], "fator_de_modulacao": 2},
                {"caminho": [0, 4, 3], "fator_de_modulacao": 1}]}
    }
    kw = dict(numero_de_slots=100, t_d=50.0, modo="reserva_demanda",
              holding_time=1.0, slot_size=12.5)
    so_principal = MigrationProtection([isp], g, caminhos_corredor=1, **kw)
    so_principal.atualizar(0, {0})
    # 0-1 and 2-3 are shared with ISPs outside K: only 1-2 is protected
    assert set(so_principal.protegidos) == {frozenset((1, 2))}

    corredor = MigrationProtection([isp], g, caminhos_corredor=2, **kw)
    corredor.atualizar(0, {0})
    assert frozenset((0, 4)) in corredor.protegidos and frozenset((4, 3)) in corredor.protegidos
    # 125 Gb/s needed: 5 slots at factor 2 on the main path, 10 at factor 1 on the backup
    assert corredor.reserva_link(frozenset((1, 2)), agora=40.0) == 5
    assert corredor.reserva_link(frozenset((0, 4)), agora=40.0) == 10
    assert corredor.links_ja_protegidos == set(corredor.protegidos)


def _protecao_feedback(**kw) -> tuple[MigrationProtection, nx.Graph]:
    # ISP 0 migrates 0 -> 3: main 0-1-2-3 (factor 1), backup 0-4-3 (factor 1)
    g = _grafo()
    g.add_edge(0, 4, ISPs=[0])
    g.add_edge(4, 3, ISPs=[0])
    for _, _, d in g.edges(data=True):
        d["slots"] = [0] * 100
    isp = _ISP(0, [0, 1, 2, 3])
    isp.datacenter.tamanho_datacenter = 1250.0
    isp.weighted_caminhos_internos_isp_durante_desastre = {
        0: {3: [{"caminho": [0, 1, 2, 3], "fator_de_modulacao": 1},
                {"caminho": [0, 4, 3], "fator_de_modulacao": 1}]}
    }
    params = dict(numero_de_slots=100, t_d=50.0, modo="reserva_feedback",
                  caminhos_corredor=2, holding_time=1.0, slot_size=12.5,
                  feedback_kappa=1.0, feedback_intervalo=1.0)
    params.update(kw)
    prot = MigrationProtection([isp], g, **params)
    prot.atualizar(0, {0})
    return prot, g


def test_feedback_starts_as_demand_on_main_path() -> None:
    prot, _ = _protecao_feedback()
    # 125 Gb/s needed -> 10 slots, all on the main path at first
    assert prot.reserva_link(frozenset((1, 2)), agora=40.0) == 10
    assert prot.reserva_link(frozenset((0, 4)), agora=40.0) == 0


def test_feedback_gain_follows_migration_and_background_blocking() -> None:
    prot, g = _protecao_feedback()
    prot.aplicar(_Req(), [], agora=40.0)  # starts the clock
    # Behind schedule: needed 1250 / 10 s = 125 Gb in 1 s, only 50 accepted
    prot.registra_migracao(0, True, 100.0)
    prot.registra_migracao(0, False, 50.0, [0, 1, 2, 3])
    prot.aplicar(_Req(), [], agora=41.0)
    assert prot._ganho[0] > 1.0
    alto = prot._ganho[0]
    # Ahead of schedule and background blocked by the reserve: gain drops
    for _ in range(4):
        prot.registra_migracao(0, False, 100.0, [0, 1, 2, 3])
    prot.aplicar(_Req(), [_dp([0, 1, 2], [(85, 99)], precisa=10)], agora=41.5)
    for link in [(0, 1), (1, 2), (2, 3)]:  # reserve region fully used: not idle
        u, v = link
        g[u][v]["slots"] = [1] * 100
    prot.aplicar(_Req(), [], agora=42.0)
    assert prot._ganho[0] < alto
    assert len(prot.historico_ganho) == 2


def test_feedback_shifts_need_to_paths_migration_uses_and_respects_cap() -> None:
    prot, _ = _protecao_feedback(reserva_max=0.5)
    prot.aplicar(_Req(), [], agora=40.0)
    prot.registra_migracao(0, False, 100.0, [0, 4, 3])  # all accepted on the backup
    prot.aplicar(_Req(), [], agora=41.0)
    principal, reserva = prot._uso_caminho[0]
    assert principal == reserva == 0.5
    assert prot.reserva_link(frozenset((0, 4)), agora=41.0) > 0
    prot._ganho[0] = 20.0
    assert prot.reserva_link(frozenset((1, 2)), agora=41.0) == 50  # capped at 50%


def test_feedback_ignores_blocking_when_on_schedule() -> None:
    prot, g = _protecao_feedback()
    for _, _, d in g.edges(data=True):
        d["slots"] = [1] * 100  # reserve fully used: no idle term
    prot.aplicar(_Req(), [], agora=40.0)
    # Many requests blocked, but 125 Gb accepted = exactly what was needed
    for _ in range(10):
        prot.registra_migracao(0, True, 100.0)
    prot.registra_migracao(0, False, 125.0, [0, 1, 2, 3])
    prot.aplicar(_Req(), [], agora=41.0)
    assert abs(prot._ganho[0] - 1.0) < 1e-9


def test_corridor_weighted_reserve_adds_up_on_shared_links() -> None:
    # Main 0-1-2-3, backups 0-1-4-3 and 0-5-3: link 0-1 is on paths 1 and 2
    g = nx.Graph()
    for u, v in [(0, 1), (1, 2), (2, 3), (1, 4), (4, 3), (0, 5), (5, 3)]:
        g.add_edge(u, v, ISPs=[0], slots=[0] * 100)
    isp = _ISP(0, [0, 1, 2, 3])
    isp.weighted_caminhos_internos_isp_durante_desastre = {
        0: {3: [{"caminho": [0, 1, 2, 3]}, {"caminho": [0, 1, 4, 3]}, {"caminho": [0, 5, 3]}]}
    }
    kw = dict(numero_de_slots=100, t_d=50.0, caminhos_corredor=3,
              reserva_fracao=0.2, reserva_max=0.85)
    pos = MigrationProtection([isp], g, modo="reserva_corredor", **kw)
    pos.atualizar(0, {0})
    assert pos.reserva_link(frozenset((0, 1)), 40.0) == 30   # 20 * (1 + 1/2)
    assert pos.reserva_link(frozenset((1, 2)), 40.0) == 20   # main path only
    assert pos.reserva_link(frozenset((1, 4)), 40.0) == 10   # 20 * 1/2
    assert pos.reserva_link(frozenset((0, 5)), 40.0) == 7    # 20 * 1/3

    uso = MigrationProtection([isp], g, modo="reserva_corredor_uso", **kw)
    uso.atualizar(0, {0})
    # Starts all on the main path: backups reserve nothing
    assert uso.reserva_link(frozenset((0, 5)), 40.0) == 0
    assert uso.reserva_link(frozenset((0, 1)), 40.0) == 20
    uso.aplicar(_Req(), [], agora=40.0)
    uso.registra_migracao(0, False, 100.0, [0, 5, 3])  # all accepted on path 3
    uso.aplicar(_Req(), [], agora=41.0)
    # shares 0.5 / 0 / 0.5 -> weights 1 / 0 / 1
    assert uso.reserva_link(frozenset((0, 5)), 41.0) == 20
    assert uso.reserva_link(frozenset((1, 4)), 41.0) == 0

    teto = MigrationProtection([isp], g, modo="reserva_corredor",
                               **{**kw, "reserva_fracao": 0.7})
    teto.atualizar(0, {0})
    assert teto.reserva_link(frozenset((0, 1)), 40.0) == 85  # 105 capped at 85%


def test_demand_max_aggregation_keeps_largest_need() -> None:
    soma = _protecao_demanda(margem=1.0)
    maior = _protecao_demanda(margem=1.0, agregacao="max")
    for prot in (soma, maior):
        prot.atualizar(0, {0, 1})
        prot.atualizar(1, {0, 1})
    link = frozenset((0, 1))  # main path of ISPs 0 and 1, both need 10 slots
    assert soma.reserva_link(link, agora=40.0) == 20
    assert maior.reserva_link(link, agora=40.0) == 10
    maior.registra_migracao(0, bloqueada=False, banda=625.0)  # ISP 0 now needs 5
    assert maior.reserva_link(link, agora=40.0) == 10  # ISP 1 still needs 10


def test_demand_split_by_use_starts_on_main_path_and_follows_migration() -> None:
    prot, _ = _protecao_feedback()  # graph with a backup path 0-4-3
    prot.modo, prot._usa_uso = "reserva_demanda", True
    assert prot.reserva_link(frozenset((1, 2)), agora=40.0) == 10
    assert prot.reserva_link(frozenset((0, 4)), agora=40.0) == 0
    prot.aplicar(_Req(), [], agora=40.0)
    prot.registra_migracao(0, False, 100.0, [0, 4, 3])
    prot.aplicar(_Req(), [], agora=41.0)  # shares 0.5 / 0.5
    assert prot._ganho[0] == 1.0  # no gain correction outside the feedback mode
    assert prot.reserva_link(frozenset((0, 4)), agora=41.0) > 0


def test_diversify_exits_reorders_migration_paths() -> None:
    from simulador.entities.scenario import Scenario

    caminhos = [{"caminho": p} for p in ([9, 11, 19], [9, 12, 11, 19], [9, 12, 16, 19], [9, 6, 11, 19])]

    class _S:
        lista_de_isps = [_ISP(0, [9, 11, 19])]

    s = _S()
    s.lista_de_isps[0].weighted_caminhos_internos_isp_durante_desastre = {9: {19: list(caminhos)}}
    assert Scenario.diversificar_saidas_migracao(s, 3) == {0: 3}
    nova = [c["caminho"] for c in s.lista_de_isps[0].weighted_caminhos_internos_isp_durante_desastre[9][19]]
    assert nova == [[9, 11, 19], [9, 12, 11, 19], [9, 6, 11, 19], [9, 12, 16, 19]]


def test_last_fit_for_migration_only() -> None:
    from simulador.routing.subnet_weighted_disaster_aware import (
        FirstFitWeightedSubnetDisasterAware as R,
    )

    class _Topo:
        migracao_last_fit = True
        def __init__(self): self.alocado = None
        def aloca_janela(self, caminho, janela): self.alocado = janela
        def desaloca_janela(self, *a): return None

    class _Env:
        now = 0.0
        def process(self, x): return None

    class _R:
        holding_time = 1.0
        def __init__(self, mig): self.requisicao_de_migracao = mig
        def aceita_requisicao(self, *a): pass

    dp = {"caminho": [0, 1], "numero_slots_necessarios": 4, "distancia": 100,
          "lista_de_inicios_e_fins": [(0, 9), (20, 22), (50, 79)]}
    aloca = R._FirstFitWeightedSubnetDisasterAware__aloca_datapath
    t = _Topo(); aloca(_R(True), t, dp, _Env())
    assert t.alocado == (76, 79)          # migration: top of the highest window that fits
    t = _Topo(); aloca(_R(False), t, dp, _Env())
    assert t.alocado == (0, 3)            # background: First-Fit
    t = _Topo(); t.migracao_last_fit = False; aloca(_R(True), t, dp, _Env())
    assert t.alocado == (0, 3)            # option off: First-Fit for everyone
