from Requisicao.Requisicao import Requisicao

from Registrador import Registrador
from Roteamento.iRoteamento import iRoteamento
from Variaveis import *
import math
from simpy import Environment
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Topologia import Topologia
    from Simulador import Simulador

class RoteamentoBestFit(iRoteamento):


    def rotear_requisicao( requisicao: Requisicao, topology: 'Topologia', env: Environment ) -> bool:

        informacoes_dos_datapaths, menor_janela = RoteamentoBestFit.__retorna_informacoes_datapaths(requisicao, topology)
        if menor_janela != None:
            Registrador.incrementa_numero_requisicoes_aceitas()
            RoteamentoBestFit.__aloca_requisicao(requisicao, topology, informacoes_dos_datapaths, env, menor_janela)
            return True
        else:
            requisicao.bloqueia_requisicao( env.now)
            Registrador.conta_bloqueio_requisicao_banda(requisicao.bandwidth)
            Registrador.conta_bloqueio_requisicao_classe(requisicao.class_type)
            Registrador.incrementa_numero_requisicoes_bloqueadas()
            return False

    def rerotear_requisicao( requisicao: Requisicao, topology: 'Topologia', env: Environment ) -> bool:

        requisicao.dados_pre_reroteamento = requisicao.retorna_tupla_chave_dicionario_dos_atributos()
        informacoes_dos_datapaths, menor_janela = RoteamentoBestFit.__retorna_informacoes_datapaths(requisicao, topology)
        if menor_janela != None:
            Registrador.incrementa_numero_requisicoes_reroteadas_aceitas()
            RoteamentoBestFit.__aloca_requisicao(requisicao, topology, informacoes_dos_datapaths, env, menor_janela)
            return True
        else:
            requisicao.bloqueia_requisicao( env.now)
            Registrador.conta_bloqueio_reroteadas_por_banda(requisicao.bandwidth)
            Registrador.conta_bloqueio_reroteadas_por_classe(requisicao.class_type)
            Registrador.incrementa_numero_requisicoes_reroteadas_bloqueadas()
            return False

    def __aloca_requisicao( requisicao: Requisicao, topology: 'Topologia', informacoes_datapaths: dict, env: Environment, menor_janela: list[int, int]) -> None:

        for informacoes_datapath in informacoes_datapaths:
            if informacoes_datapath["melhor_janela_contigua"] == menor_janela:
                RoteamentoBestFit.__aloca_datapath(requisicao, topology, informacoes_datapath, env)
                break
        
    def __aloca_datapath( requisicao: Requisicao, topology: 'Topologia', informacoes_datapath: dict, env: Environment) -> None:
        inicio = informacoes_datapath['melhor_janela_contigua'][0]
        fim = informacoes_datapath['melhor_janela_contigua'][0] + informacoes_datapath["numero_slots_necessarios"] - 1
        caminho = informacoes_datapath["caminho"]

        topology.aloca_janela(caminho, [inicio, fim] )

        requisicao.processo_de_desalocacao = env.process(topology.desaloca_janela(caminho, [inicio, fim], requisicao.holding_time, env))


        requisicao.aceita_requisicao(informacoes_datapath["numero_slots_necessarios"], caminho, len(caminho), [inicio, fim],
                                            env.now, env.now + requisicao.holding_time, informacoes_datapath["distancia"])
        
    def __retorna_informacoes_datapaths( requisicao: Requisicao, topology: 'Topologia') -> tuple[list[dict], bool]:

        caminhos = topology.caminhos_mais_curtos_entre_links[int(requisicao.src)][ int(requisicao.dst)]
    

        lista_de_informacoes_datapath = []
        pelo_menos_uma_janela_habil = False

        
        menor_janela = None
        for caminho in caminhos:
            if not topology.caminho_em_funcionamento(caminho):
                continue
            
            distancia = topology.distancia_caminho(caminho)
            fator_de_modulacao = RoteamentoBestFit.__fator_de_modulacao(distancia)
            numero_slots_necessarios = RoteamentoBestFit.__slots_nescessarios(distancia, requisicao.bandwidth)

            slots_livres, slots_livres_agrupados, lista_de_inicios_e_fins = RoteamentoBestFit.__informacoes_sobre_slots(caminho, topology)

            #identifica menor janela
            melhor_janela_contigua_caminho = None
            for inicios_e_fins in lista_de_inicios_e_fins:

                if inicios_e_fins[1] - inicios_e_fins[0] + 1 >= numero_slots_necessarios and (melhor_janela_contigua_caminho == None or inicios_e_fins[1] - inicios_e_fins[0] + 1 < melhor_janela_contigua_caminho[1] - melhor_janela_contigua_caminho[0] + 1):
                    melhor_janela_contigua_caminho = inicios_e_fins
                    if melhor_janela_contigua_caminho[1] - melhor_janela_contigua_caminho[0] + 1 == numero_slots_necessarios:
                        break
                
            if menor_janela == None or (melhor_janela_contigua_caminho != None and melhor_janela_contigua_caminho[1] - melhor_janela_contigua_caminho[0] + 1 < menor_janela[1] - menor_janela[0] + 1):
                menor_janela = melhor_janela_contigua_caminho
            
            numero_de_slots_livres = len(slots_livres)
            
            capacidade_do_caminho = numero_de_slots_livres * fator_de_modulacao
            listas_de_tamanhos_das_janelas = [len(x) for x in slots_livres_agrupados]
            
            maior_janela =  max(listas_de_tamanhos_das_janelas) if len(listas_de_tamanhos_das_janelas) > 0 else 0
            if pelo_menos_uma_janela_habil == False:
                pelo_menos_uma_janela_habil = maior_janela >= numero_slots_necessarios

            dados_do_caminho = {"caminho": caminho, "distancia": distancia, "fator_de_modulacao": fator_de_modulacao, 
                                "numero_de_slots_livres": numero_de_slots_livres, "capacidade_do_caminho": capacidade_do_caminho,
                                 "slots_livres_agrupados": slots_livres_agrupados, "slots_livres": slots_livres, 
                                 "lista_de_inicios_e_fins": lista_de_inicios_e_fins, "numero_slots_necessarios": numero_slots_necessarios,
                                 "maior_janela_contigua_continua":maior_janela, "melhor_janela_contigua": melhor_janela_contigua_caminho
                                  }
            lista_de_informacoes_datapath.append(dados_do_caminho)

        return lista_de_informacoes_datapath, menor_janela
        
    def __informacoes_sobre_slots( caminho, topology: 'Topologia') -> tuple[list[int], list[list[int]], list[tuple[int, int]]]:
        
        slots_livres = RoteamentoBestFit.__retorna_slots_livres(caminho, topology)
        
        slots_livres_agrupados = RoteamentoBestFit.__agrupa_slots_consecutivos(slots_livres)

        lista_de_inicios_e_fins = RoteamentoBestFit.__retona_lista_de_inicios_e_fins(slots_livres_agrupados)

        return slots_livres, slots_livres_agrupados, lista_de_inicios_e_fins
        
    def __retorna_slots_livres( caminho, topology: 'Topologia') ->list:
        
        slots_livres = []
        for i in range( topology.numero_de_slots):
            if RoteamentoBestFit.__checa_concurrency_slot(caminho, topology, i):
                slots_livres.append(i)
        return slots_livres
    
    def __checa_concurrency_slot( caminho :list, topology: 'Topologia', indice: int) -> bool:

        for i in range(0, (len(caminho)-1)):
            
            if topology.topology[caminho[i]][caminho[i+1]]['slots'][indice] != 0:
                return False
        return True
    
    def __agrupa_slots_consecutivos( slots_livre: list[list]) -> list[list[int]]:
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
    
    def __retona_lista_de_inicios_e_fins( slots_livres_agrupados: list[list]) -> list[tuple[int, int]]:
        lista_de_inicios_e_fins = []
        for slots in slots_livres_agrupados:
            lista_de_inicios_e_fins.append([slots[0], slots[-1]])
        return lista_de_inicios_e_fins

    def __slots_nescessarios(  distancia, demanda) -> int:
        if distancia <= 500:
            return int(math.ceil(float(demanda) / float(4 * SLOT_SIZE)))
        elif 500 < distancia <= 1000:
            return int(math.ceil(float(demanda) / float(3 * SLOT_SIZE)))
        elif 1000 < distancia <= 2000:
            return int(math.ceil(float(demanda) / float(2 * SLOT_SIZE))) 
        else:
            return int(math.ceil(float(demanda) / float(1 * SLOT_SIZE)))
   
    def __fator_de_modulacao(  distancia) -> float:
        if distancia <= 500:
            return (float(4 * SLOT_SIZE))
        elif 500 < distancia <= 1000:
            return (float(3 * SLOT_SIZE))
        elif 1000 < distancia <= 2000:
            return (float(2 * SLOT_SIZE)) 
        else:
            return (float(1 * SLOT_SIZE))
