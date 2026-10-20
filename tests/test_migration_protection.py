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
