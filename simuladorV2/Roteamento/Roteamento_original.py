from Requisicao.Requisicao import Requisicao
from Topologia import Topologia
from Contador import Contador
from Roteamento.iRoteamento import iRoteamento
import math
SLOT_SIZE = 12.5
class Roteamento(iRoteamento):



    def rotear_requisicao(self, requisicao: Requisicao, topology: Topologia):

        informacoes_dos_datapaths, capacidade_total_dos_datapaths = self.retorna_informacoes_datapaths(requisicao, topology)

        if capacidade_total_dos_datapaths >= requisicao.bandwidth:
            self.aloca_requisicao(requisicao, topology, informacoes_dos_datapaths)
            
        else:
            self.bloqueia_requisicao(requisicao)

    def bloqueia_requisicao(self, requisicao: Requisicao, topology: Topologia):
        requisicao.bloqueia_requisicao( topology.enviromment.now)
        Contador.conta_bloqueio_requisicao_banda(requisicao.bandwidth)
        Contador.conta_bloqueio_requisicao_classe(requisicao.class_type)
        Contador.incrementa_numero_requisicoes_bloqueadas()

    def aloca_requisicao(self, requisicao: Requisicao, topology: Topologia, informacoes_datapaths: dict):

        bandwidth_nescessaria = requisicao.bandwidth
        for informacoes_datapath in informacoes_datapaths:
            bandwidth_nescessaria = self.aloca_spectro_datapath(requisicao, topology, informacoes_datapath, bandwidth_nescessaria)
            if bandwidth_nescessaria == 0:
                break
    
    def aloca_spectro_datapath(self, requisicao: Requisicao, topology: Topologia, informacoes_datapath: dict, bandwidth_nescessaria: int):

        for lista_de_inicios_e_fins in informacoes_datapath["lista_de_inicios_e_fins"]:
            inicio, fim = lista_de_inicios_e_fins
            bandwidth_nescessaria = self.aloca_janela_datapath(inicio, fim, topology, informacoes_datapath, bandwidth_nescessaria, requisicao)
            if bandwidth_nescessaria == 0:
                break
        return bandwidth_nescessaria
    
    def aloca_janela_datapath(self, inicio, fim, topology: Topologia, informacoes_datapath, bandwidth_nescessaria, requisicao: Requisicao):

        tamanho_janela = fim - inicio + 1
        throughput_da_janela = informacoes_datapath["fator_de_modulacao"] * tamanho_janela
        caminho = informacoes_datapath["caminho"]
        if throughput_da_janela > bandwidth_nescessaria:
            bandwidth_nescessaria = bandwidth_nescessaria

        bandwidth_nescessaria -= throughput_da_janela

        Contador.incrementa_numero_requisicoes()
        topology.aloca_janela(caminho, [inicio, fim] )

        requisicao.processo_de_desalocacao = topology.desaloca_janela(caminho, [inicio, fim], requisicao.holding_time)
        
        requisicao.aceita_requisicao(  tamanho_janela, caminho, len(caminho), [inicio, fim], topology.enviromment.now,requisicao.holding_time, topology.distancia_caminho(caminho))

        return bandwidth_nescessaria

    def retorna_informacoes_datapaths(self, requisicao: Requisicao, topology: Topologia):

        caminhos = topology.k_paths[requisicao.src, requisicao.dst]
    

        lista_de_informacoes_datapath = []
        capacidade_total = 0
        for caminho in caminhos:
            distancia = topology.distancia_caminho(caminho)
            fator_de_modulacao = self.fator_de_modulacao(distancia, requisicao.bandwidth)
            numero_slots_necessarios = self.slots_nescessarios(distancia, requisicao.bandwidth)

            slots_livres, slots_livres_agrupados, lista_de_inicios_e_fins = self.informacoes_sobre_slots(caminho, topology)

            numero_de_slots_livres = len(slots_livres)
            capacidade_do_caminho = numero_de_slots_livres * fator_de_modulacao
            capacidade_total += capacidade_do_caminho

            dados_do_caminho = {"caminho": caminho, "distancia": distancia, "fator_de_modulacao": fator_de_modulacao, 
                                "numero_de_slots_livres": numero_de_slots_livres, "capacidade_do_caminho": capacidade_do_caminho,
                                 "slots_livres_agrupados": slots_livres_agrupados, "slots_livres": slots_livres, 
                                 "lista_de_inicios_e_fins": lista_de_inicios_e_fins, "numero_slots_necessarios": numero_slots_necessarios,
                                  }
            lista_de_informacoes_datapath.append(dados_do_caminho)
        return lista_de_informacoes_datapath, capacidade_total
        

    def informacoes_sobre_slots(self, caminho, topology: Topologia):
        
        slots_livres = self.retorna_slots_livres(caminho, topology)
        
        slots_livres_agrupados = self.agrupa_slots_consecutivos(slots_livres)

        lista_de_inicios_e_fins = self.retona_lista_de_inicios_e_fins(slots_livres_agrupados)

        return slots_livres, slots_livres_agrupados, lista_de_inicios_e_fins
        
    def retorna_slots_livres(self, caminho, topology: Topologia) ->list:
        
        slots_livres = []
        for i in range( topology.numero_de_slots):
            if self.checa_concurrency_slot(caminho, topology, i):
                slots_livres.append(i)
        return slots_livres
    
    def checa_concurrency_slot(self, caminho :list, topology: Topologia, indice: int):

        for i in range(0, (len(caminho)-1)):
            
            if topology.topology[caminho[i]][caminho[i+1]]['slots'][indice] != 0:
                return False
        return True
    
    def agrupa_slots_consecutivos(self, slots_livre: list[list]):
        slots_livres :list[list] = []
        for slot in slots_livre:
            if len(slots_livres) == 0:
                slots_livres.append([slot])
            else:
                if slots_livres[-1][-1] == slot - 1:
                    slots_livres[-1].append(slot)
                else:
                    slots_livres.append([slot])
        return slots_livres
    
    def retona_lista_de_inicios_e_fins(self, slots_livres_agrupados: list[list]):
        lista_de_inicios_e_fins = []
        for slots in slots_livres_agrupados:
            lista_de_inicios_e_fins.append([slots[0], slots[-1]])
        return lista_de_inicios_e_fins

    def slots_nescessarios( self, distancia, demanda):
        if distancia <= 500:
            return int(math.ceil(float(demanda) / float(4 * SLOT_SIZE)))
        elif 500 < distancia <= 1000:
            return int(math.ceil(float(demanda) / float(3 * SLOT_SIZE)))
        elif 1000 < distancia <= 2000:
            return int(math.ceil(float(demanda) / float(2 * SLOT_SIZE))) 
        else:
            return int(math.ceil(float(demanda) / float(1 * SLOT_SIZE)))
   
    def fator_de_modulacao( self, distancia):
        if distancia <= 500:
            return (float(4 * SLOT_SIZE))
        elif 500 < distancia <= 1000:
            return (float(3 * SLOT_SIZE))
        elif 1000 < distancia <= 2000:
            return (float(2 * SLOT_SIZE)) 
        else:
            return (float(1 * SLOT_SIZE))
