import simpy
import networkx as nx
from Simulador import Simulador
from ISP.ISP import ISP
from Requisicao.Requisicao import Requisicao

class Desastre:


    def __init__(self, start, duration, list_of_dict_node_per_start_time, list_of_dict_link_per_start_time) -> None:
        self.start = start
        self.duration = duration
        self.list_of_dict_node_per_start_time = list_of_dict_node_per_start_time
        self.list_of_dict_link_per_start_time = list_of_dict_link_per_start_time
        self.links_em_falha = [] 
        self.nodes_em_falha = []  
        
    def iniciar_desastre(self, simulador:Simulador) -> None:
        simulador.env.process(self.gerar_falhas(simulador))
        simulador.env.process(self.iniciar_migracao(simulador))

    def iniciar_migracao(self, simulador:Simulador):
        lista_ISP:list[ISP] = simulador.lista_de_ISPs
        for isp in lista_ISP:
            isp.define_datacenter(self, simulador.topology.topology)
            isp.iniciar_migracao(simulador)

    def gerar_falhas(self, simulador:Simulador):
        while True:
            for link_point in self.list_of_dict_link_per_start_time:
                if link_point not in self.links_em_falha and  simulador.env.now >= link_point["start_time"] + self.start:
                    self.FalhaNoLink(link_point['src'], link_point['dst'], simulador)
                    self.links_em_falha.append(link_point)
                    print("falha gerada", link_point )

            for node_point in self.list_of_dict_node_per_start_time:
                if node_point not in self.nodes_em_falha and  simulador.env.now >= node_point["start_time"] + self.start:
                    self.FalhaNoNo(node_point['node'], simulador)
                    self.nodes_em_falha.append(node_point)
                    print("falha gerada", node_point )

            if  simulador.env.now >= self.start + self.duration:
                for u, v in list(simulador.topology.topology.edges):
                    simulador.topology.topology[u][v]['failed'] = False
                if not self.mensagem_impressa:
                    print ("links reestabelecidos")

                    self.mensagem_impressa = True
            
            if simulador.simulacao_finalizada == True:
                break  
            yield  simulador.env.timeout(1) 

    def FalhaNoLink(self, node1, node2, simulador:Simulador):
        topology = simulador.topology
        if topology.topology.has_edge(node1, node2):
            
            topology.topology[node1][node2]['failed'] = True
            

            requisicoes_falhas :list[Requisicao] = self.Quem_falhou_link(node1, node2, simulador)

            
            for requisicao in requisicoes_falhas:
                requisicao.processo_de_desalocacao.interrupt()
                index_isp = requisicao.src_ISP_index
                topology._desalocate(requisicao.resultados_requisicao["path"], requisicao.resultados_requisicao["spectro"])
                requisicao.resultados_requisicao = None
                requisicao.bloqueada = None
                roteador = simulador.lista_de_ISPs[index_isp].roteamento
                roteador.rerotear_requisicao(simulador, requisicao, topology)

            
            print(f"Falha no link entre os nós {node1} e {node2}")

        else:
            
            print(f"Erro: O link entre os nós {node1} e {node2} não existe na topologia.")

    def FalhaNoNo(self, node, simulador:Simulador):
        topology = simulador.topology.topology
        
        if node in topology.nodes:

            for neighbor in topology.neighbors(node):
                
               self.FalhaNoLink(node, neighbor, simulador)
            print(f"Falha no nó {node}")

        else:
            
            print(f"Erro: O nó {node} não existe na topologia.")

    def Quem_falhou_link(self, pontaa, pontab, simulador:Simulador) -> list[Requisicao] :
        requisicoes_ativas_que_falharam_no_link:list[Requisicao] = []
        for req in simulador.requisicoes:
            if req.bloqueada == False and req.processo_de_desalocacao.is_alive and simulador.topology.caminho_passa_por_link(pontaa, pontab, req.resultados_requisicao["path"]):
                requisicoes_ativas_que_falharam_no_link.append(req)

        return requisicoes_ativas_que_falharam_no_link

