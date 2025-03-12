import simpy
import networkx as nx
from ISP.ISP import ISP
from Requisicao.Requisicao import Requisicao
from Roteamento.iRoteamento import iRoteamento
from Logger import Logger
from Registrador import Registrador
from typing import TYPE_CHECKING, Generator
if TYPE_CHECKING:
    from Simulador import Simulador
    from Topology.Topologia import Topologia
    
class Desastre:

    def __init__(self, start, duration, list_of_dict_node_per_start_time, list_of_dict_link_per_start_time, eventos) -> None:
        self.start = start
        self.duration = duration
        self.eventos_nao_iniciados: list[dict] = eventos
        self.list_of_dict_node_per_start_time = list_of_dict_node_per_start_time
        self.list_of_dict_link_per_start_time = list_of_dict_link_per_start_time
        
    def imprime_desastre(self) -> None:
        print("Início do desastre: ", self.start)
        print("Duração do desastre: ", self.duration)
        print("Eventos: ", self.eventos_nao_iniciados)
        
    def iniciar_desastre(self, simulador:'Simulador') -> None:
        simulador.env.process(self.__gerar_falhas(simulador))

        for isp in simulador.lista_de_ISPs:
            simulador.env.process(isp.iniciar_migracao(simulador))

    def seta_links_como_prestes_a_falhar(self, topology:'Topologia') -> None:
        for dict_link in self.list_of_dict_link_per_start_time:
            src = dict_link['src']
            dst = dict_link['dst']
            topology.topology[src][dst]['vai falhar'] = True
            print("Link ", src, dst, " vai falhar")
        
        for dict_node in self.list_of_dict_node_per_start_time:
            node = dict_node['node']
            for neighbor in topology.topology.neighbors(node):
                topology.topology[node][neighbor]['vai falhar'] = True  
                print("Link ", node, neighbor, " vai falhar")

    def __gerar_falhas(self, simulador:'Simulador') -> Generator:

        while self.eventos_nao_iniciados != []:
            tempo_pro_proximo_evento = ( self.eventos_nao_iniciados[0]['start_time'] + self.start) - simulador.env.now 
            yield simulador.env.timeout( tempo_pro_proximo_evento )
            evento = self.eventos_nao_iniciados.pop(0)
            self.__ativa_evento(evento, simulador)
            simulador.env.process(self.__desativa_evento(evento, simulador))
            
        yield simulador.env.timeout( self.start + self.duration - simulador.env.now )
        Logger.mensagem_desastre_finalizado(simulador.env.now)
    
    def __ativa_evento(self, informacoes_evento, simulador: 'Simulador') -> None:

        if informacoes_evento['tipo'] == 'node':
            self.__FalhaNoNo(informacoes_evento['node'], simulador)
            Logger.mensagem_acompanha_node_desastre(informacoes_evento['node'], simulador.env.now)

        elif informacoes_evento['tipo'] == "link":
            self.__FalhaNoLink(informacoes_evento['src'], informacoes_evento['dst'], simulador)
            Logger.mensagem_acompanha_link_desastre(informacoes_evento['src'], informacoes_evento['dst'], simulador.env.now)

    def __desativa_evento(self, informacoes_evento, simulador: 'Simulador') -> Generator:
            
        yield simulador.env.timeout(self.start + self.duration - simulador.env.now)
            
        if informacoes_evento['tipo'] == 'node':
            self.__restaura_no(informacoes_evento, simulador)
            Logger.mensagem_acompanha_node_desastre(informacoes_evento['node'], simulador.env.now)

        elif informacoes_evento['tipo'] == "link":
            self.__restaura_link(informacoes_evento, simulador)
            Logger.mensagem_acompanha_link_desastre(informacoes_evento['src'], informacoes_evento['dst'], simulador.env.now)
            
    def __restaura_link(self, informacoes_evento: dict, simulador: 'Simulador') -> None:
        src = informacoes_evento['src']
        dst = informacoes_evento['dst']
        if simulador.topology.topology.has_edge(src, dst) and simulador.topology.topology[src][dst]['failed']:
            simulador.topology.topology[src][dst]['failed'] = False
            simulador.topology.topology[src][dst]['vai falhar'] = False
    
    def __restaura_no(self, informacoes_evento, simulador: 'Simulador') -> None:
        node = informacoes_evento['node']
        if node in simulador.topology.topology.nodes:
            for neighbor in simulador.topology.topology.neighbors(node):
                self.__restaura_link({'src':node, 'dst':neighbor}, simulador)

    def __FalhaNoLink(self, node1, node2, simulador:'Simulador') -> None:
        topology = simulador.topology
        if topology.topology.has_edge(node1, node2) and not topology.topology[node1][node2]['failed']:
            
            topology.topology[node1][node2]['failed'] = True
            

            requisicoes_falhas :list[Requisicao] = self.__Quem_falhou_link(node1, node2, simulador)

            
            for requisicao in requisicoes_falhas:
                if requisicao.afetada_por_desastre == False:
                    Registrador.conta_reroteadas_por_banda(requisicao.bandwidth)
                    Registrador.conta_reroteadas_por_classe(requisicao.class_type)
                    Registrador.adiciona_numero_de_afetadas(1)

                    requisicao.processo_de_desalocacao.interrupt()
                    index_isp = requisicao.src_ISP_index
                    topology.desalocate(requisicao.caminho, requisicao.index_de_inicio_e_final)
                    requisicao.afetada_por_desastre = True
                    roteador: iRoteamento = simulador.lista_de_ISPs[index_isp].roteamento_atual
                    roteador.rerotear_requisicao(requisicao, topology, simulador.env)
                    requisicao.afetada_por_desastre = True

    def __FalhaNoNo(self, node, simulador:'Simulador') -> None:
        topology = simulador.topology.topology
        
        if node in topology.nodes:
            for neighbor in topology.neighbors(node):
                
               self.__FalhaNoLink(node, neighbor, simulador)

    def __Quem_falhou_link(self, pontaa, pontab, simulador:'Simulador') -> list[Requisicao] :
        requisicoes_ativas_que_falharam_no_link:list[Requisicao] = []
        requisicoes = Registrador.get_requisicoes()

        for req in requisicoes:
            if (req.bloqueada == False and simulador.topology.caminho_passa_por_link(pontaa, pontab, req.caminho) and
                 simulador.env.now >= req.tempo_criacao and simulador.env.now < req.tempo_desalocacao):
                
                req.dados_pre_reroteamento = req.retorna_tupla_chave_dicionario_dos_atributos()[1]
                requisicoes_ativas_que_falharam_no_link.append(req)
            
        return requisicoes_ativas_que_falharam_no_link

