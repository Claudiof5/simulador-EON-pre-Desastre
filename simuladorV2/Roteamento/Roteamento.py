from Requisicao.Requisicao import Requisicao

from Registrador import Registrador
from Roteamento.iRoteamento import iRoteamento
from Variaveis import *
import math

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Topologia import Topologia
    
class Roteamento(iRoteamento):


    def rotear_requisicao( requisicao: Requisicao, topology: 'Topologia') -> bool:

        informacoes_dos_datapaths, pelo_menos_uma_janela_habil = Roteamento.retorna_informacoes_datapaths(requisicao, topology)
        if pelo_menos_uma_janela_habil:
            Roteamento.aloca_requisicao(requisicao, topology, informacoes_dos_datapaths)
            return True
        else:
            requisicao.bloqueia_requisicao( topology.enviromment.now)
            Registrador.conta_bloqueio_requisicao_banda(requisicao.bandwidth)
            Registrador.conta_bloqueio_requisicao_classe(requisicao.class_type)
            Registrador.incrementa_numero_requisicoes_bloqueadas()
            return False

    def rerotear_requisicao( requisicao: Requisicao, topology: 'Topologia') -> bool:

        informacoes_dos_datapaths, pelo_menos_uma_janela_habil = Roteamento.retorna_informacoes_datapaths(requisicao, topology)
        if pelo_menos_uma_janela_habil:
            Roteamento.aloca_requisicao(requisicao, topology, informacoes_dos_datapaths)
            return True
        else:
            requisicao.bloqueia_requisicao( topology.enviromment.now)
            Registrador.conta_bloqueio_reroteadas_por_banda(requisicao.bandwidth)
            Registrador.conta_bloqueio_reroteadas_por_classe(requisicao.class_type)
            Registrador.incrementa_numero_requisicoes_reroteadas_bloqueadas()
            return False

    def aloca_requisicao( requisicao: Requisicao, topology: 'Topologia', informacoes_datapaths: dict) -> None:

        for informacoes_datapath in informacoes_datapaths:
            if informacoes_datapath["maior_janela_contigua_continua"] >= informacoes_datapath["numero_slots_necessarios"]:
                Roteamento.aloca_datapath(requisicao, topology, informacoes_datapath)
                break
        
    def aloca_datapath( requisicao: Requisicao, topology: 'Topologia', informacoes_datapath: dict) -> None:
        
        #janelas_possiveis = [ janela for janela in informacoes_datapath["slots_livres_agrupados"] if len(janela) >= informacoes_datapath["numero_slots_necessarios"]]
        primeira_janela_disponivel = next( (janela for janela in informacoes_datapath["slots_livres_agrupados"] if len(janela) >= informacoes_datapath["numero_slots_necessarios"]), None)
        
        inicio = primeira_janela_disponivel[0]
        fim = primeira_janela_disponivel[0] + informacoes_datapath["numero_slots_necessarios"] - 1
        caminho = informacoes_datapath["caminho"]

        Registrador.incrementa_numero_requisicoes()
        topology.aloca_janela(caminho, [inicio, fim] )

        requisicao.processo_de_desalocacao = topology.enviromment.process( topology.desaloca_janela(caminho, [inicio, fim], requisicao.holding_time) )

        requisicao.aceita_requisicao(informacoes_datapath["numero_slots_necessarios"], caminho, len(caminho), [inicio, fim], topology.enviromment.now, topology.enviromment.now+requisicao.holding_time, topology.distancia_caminho(caminho))
        
    def retorna_informacoes_datapaths( requisicao: Requisicao, topology: 'Topologia') -> tuple[list[dict], bool]:

        caminhos = topology.caminhos_mais_curtos_entre_links[requisicao.src][ requisicao.dst]
    

        lista_de_informacoes_datapath = []
        pelo_menos_uma_janela_habil = False
        for caminho in caminhos:
            if not topology.caminho_em_funcionamento(caminho):
                continue
            
            distancia = topology.distancia_caminho(caminho)
            fator_de_modulacao = Roteamento.fator_de_modulacao(distancia)
            numero_slots_necessarios = Roteamento.slots_nescessarios(distancia, requisicao.bandwidth)

            slots_livres, slots_livres_agrupados, lista_de_inicios_e_fins = Roteamento.informacoes_sobre_slots(caminho, topology)

            numero_de_slots_livres = len(slots_livres)
            
            capacidade_do_caminho = numero_de_slots_livres * fator_de_modulacao
            listas_de_tamanhos_das_janelas = [len(x) for x in slots_livres_agrupados]
            
            maior_janela =  max(listas_de_tamanhos_das_janelas) if len(listas_de_tamanhos_das_janelas) > 0 else 0
            pelo_menos_uma_janela_habil = maior_janela >= numero_slots_necessarios

            dados_do_caminho = {"caminho": caminho, "distancia": distancia, "fator_de_modulacao": fator_de_modulacao, 
                                "numero_de_slots_livres": numero_de_slots_livres, "capacidade_do_caminho": capacidade_do_caminho,
                                 "slots_livres_agrupados": slots_livres_agrupados, "slots_livres": slots_livres, 
                                 "lista_de_inicios_e_fins": lista_de_inicios_e_fins, "numero_slots_necessarios": numero_slots_necessarios,
                                 "maior_janela_contigua_continua":maior_janela
                                  }
            lista_de_informacoes_datapath.append(dados_do_caminho)

        return lista_de_informacoes_datapath, pelo_menos_uma_janela_habil
        
    def informacoes_sobre_slots( caminho, topology: 'Topologia') -> tuple[list[int], list[list[int]], list[tuple[int, int]]]:
        
        slots_livres = Roteamento.retorna_slots_livres(caminho, topology)
        
        slots_livres_agrupados = Roteamento.agrupa_slots_consecutivos(slots_livres)

        lista_de_inicios_e_fins = Roteamento.retona_lista_de_inicios_e_fins(slots_livres_agrupados)

        return slots_livres, slots_livres_agrupados, lista_de_inicios_e_fins
        
    def retorna_slots_livres( caminho, topology: 'Topologia') ->list:
        
        slots_livres = []
        for i in range( topology.numero_de_slots):
            if Roteamento.checa_concurrency_slot(caminho, topology, i):
                slots_livres.append(i)
        return slots_livres
    
    def checa_concurrency_slot( caminho :list, topology: 'Topologia', indice: int) -> bool:

        for i in range(0, (len(caminho)-1)):
            
            if topology.topology[caminho[i]][caminho[i+1]]['slots'][indice] != 0:
                return False
        return True
    
    def agrupa_slots_consecutivos( slots_livre: list[list]) -> list[list[int]]:
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
    
    def retona_lista_de_inicios_e_fins( slots_livres_agrupados: list[list]) -> list[tuple[int, int]]:
        lista_de_inicios_e_fins = []
        for slots in slots_livres_agrupados:
            lista_de_inicios_e_fins.append([slots[0], slots[-1]])
        return lista_de_inicios_e_fins

    def slots_nescessarios(  distancia, demanda) -> int:
        if distancia <= 500:
            return int(math.ceil(float(demanda) / float(4 * SLOT_SIZE)))
        elif 500 < distancia <= 1000:
            return int(math.ceil(float(demanda) / float(3 * SLOT_SIZE)))
        elif 1000 < distancia <= 2000:
            return int(math.ceil(float(demanda) / float(2 * SLOT_SIZE))) 
        else:
            return int(math.ceil(float(demanda) / float(1 * SLOT_SIZE)))
   
    def fator_de_modulacao(  distancia) -> float:
        if distancia <= 500:
            return (float(4 * SLOT_SIZE))
        elif 500 < distancia <= 1000:
            return (float(3 * SLOT_SIZE))
        elif 1000 < distancia <= 2000:
            return (float(2 * SLOT_SIZE)) 
        else:
            return (float(1 * SLOT_SIZE))
