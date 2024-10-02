import simpy
import networkx as nx
from ISP.ISP import ISP
from Requisicao.Requisicao import Requisicao
from Roteamento.iRoteamento import iRoteamento
from Logger import Logger
from Registrador import Registrador
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Simulador import Simulador
class Desastre:


    def __init__(self, start, duration, list_of_dict_node_per_start_time, list_of_dict_link_per_start_time) -> None:
        self.start = start
        self.duration = duration
        self.list_of_dict_node_per_start_time = list_of_dict_node_per_start_time
        self.list_of_dict_link_per_start_time = list_of_dict_link_per_start_time
        self.links_em_falha = [] 
        self.nodes_em_falha = []  
        
    def imprime_desastre(self) -> None:
        print("Início do desastre: ", self.start)
        print("Duração do desastre: ", self.duration)
        print("Nós em falha: ", self.list_of_dict_node_per_start_time)
        print("Links em falha: ", self.list_of_dict_link_per_start_time)
        
    def iniciar_desastre(self, simulador:'Simulador') -> None:
        simulador.env.process(self.gerar_falhas(simulador))

        for isp in simulador.lista_de_ISPs:
            simulador.env.process(isp.iniciar_migracao(simulador))

    def gerar_falhas(self, simulador:'Simulador'):
        while True:
            for link_point in self.list_of_dict_link_per_start_time:
                if link_point not in self.links_em_falha and  simulador.env.now >= link_point["start_time"] + self.start:
                    self.FalhaNoLink(link_point['src'], link_point['dst'], simulador)
                    self.links_em_falha.append(link_point)

                    Logger.mensagem_acompanha_link_desastre(link_point['src'], link_point['dst'], simulador.env.now)
                    

            for node_point in self.list_of_dict_node_per_start_time:
                if node_point not in self.nodes_em_falha and  simulador.env.now >= node_point["start_time"] + self.start:
                    self.FalhaNoNo(node_point['node'], simulador)
                    self.nodes_em_falha.append(node_point)
                    
                    Logger.mensagem_acompanha_node_desastre(node_point['node'], simulador.env.now)
                    
            if  simulador.env.now >= self.start + self.duration:
                for u, v in list(simulador.topology.topology.edges):
                    simulador.topology.topology[u][v]['failed'] = False
                Logger.mensagem_desastre_finalizado(simulador.env.now)
                break

            if simulador.simulacao_finalizada == True:
                break  
            yield  simulador.env.timeout(1) 

    def FalhaNoLink(self, node1, node2, simulador:'Simulador'):
        topology = simulador.topology
        if topology.topology.has_edge(node1, node2) and not topology.topology[node1][node2]['failed']:
            
            topology.topology[node1][node2]['failed'] = True
            

            requisicoes_falhas :list[Requisicao] = self.Quem_falhou_link(node1, node2, simulador)

            
            for requisicao in requisicoes_falhas:
                if requisicao.afetada_por_desastre == False:
                    Registrador.conta_reroteadas_por_banda(requisicao.bandwidth)
                    Registrador.conta_reroteadas_por_classe(requisicao.class_type)
                    Registrador.adiciona_numero_de_afetadas(1)

                    requisicao.processo_de_desalocacao.interrupt()
                    index_isp = requisicao.src_ISP_index
                    topology._desalocate(requisicao.caminho, requisicao.index_de_inicio_e_final)
                    requisicao.afetada_por_desastre = True
                    roteador: iRoteamento = simulador.lista_de_ISPs[index_isp].roteamento
                    roteador.rerotear_requisicao(requisicao, topology, simulador.env)
                    requisicao.afetada_por_desastre = True

    def FalhaNoNo(self, node, simulador:'Simulador'):
        topology = simulador.topology.topology
        
        if node in topology.nodes:

            for neighbor in topology.neighbors(node):
                
               self.FalhaNoLink(node, neighbor, simulador)


    def Quem_falhou_link(self, pontaa, pontab, simulador:'Simulador') -> list[Requisicao] :
        requisicoes_ativas_que_falharam_no_link:list[Requisicao] = []
        requisicoes = Registrador.get_requisicoes()

        for req in requisicoes:
            if (req.bloqueada == False and simulador.topology.caminho_passa_por_link(pontaa, pontab, req.caminho) and
                 simulador.env.now >= req.tempo_criacao and simulador.env.now < req.tempo_desalocacao):
                
                req.dados_pre_reroteamento = req.retorna_tupla_chave_dicionario_dos_atributos()[1]
                requisicoes_ativas_que_falharam_no_link.append(req)
            
        return requisicoes_ativas_que_falharam_no_link

