import os
import pickle
from copy import deepcopy

from Desastre.Desastre import Desastre
from ISP.ISP import ISP
from Requisicao.requisicao import Requisicao
from Roteamento.IRoteamento import IRoteamento
from Topology.Topologia import Topologia


class Cenario:
    def __init__(
        self,
        topology: Topologia,
        lista_de_isps: list[ISP],
        desastre: Desastre,
        lista_de_requisicoes: list[Requisicao] | None = None,
    ) -> None:
        """Initialize the Cenario class.

        Args:
            topology: The topology of the scenario
            lista_de_isps: The list of ISPs in the scenario
            desastre: The disaster of the scenario
            lista_de_requisicoes: The list of requests in the scenario
        """
        self.topology: Topologia = topology
        self.lista_de_isps: list[ISP] = lista_de_isps
        self.desastre: Desastre = desastre
        self.lista_de_requisicoes: list[Requisicao] = lista_de_requisicoes

    def retorna_atributos(
        self,
    ) -> tuple[Topologia, list[ISP], Desastre, list[Requisicao]]:
        return deepcopy(
            (
                self.topology,
                self.lista_de_isps,
                self.desastre,
                self.lista_de_requisicoes,
            )
        )

    def imprime_atributos(self) -> None:
        self.topology.imprime_topologia()
        print("")
        self.desastre.imprime_desastre()
        print("")
        for isp in self.lista_de_isps:
            isp.imprime_isp()
            print("")

    def troca_roteamento_lista_de_desastre(self, roteamento: "IRoteamento") -> None:
        for isp in self.lista_de_isps:
            isp.troca_roteamento_desastre(roteamento)

    def salva_cenario(self, nome: str) -> None:
        with open(f".cenario/cenarios/{nome}.pkl", "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def carrega_cenario(caminho: str) -> "Cenario":
        print(os.getcwd())
        with open(f"{caminho}", "rb") as f:
            return pickle.load(f)
