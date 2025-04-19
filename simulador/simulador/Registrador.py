from Requisicao.Requisicao import Requisicao
import pandas as pd
import json
from collections import defaultdict
import simpy
from typing import Generator
from copy import deepcopy

SLIDING_WINDOW_TIME = 10
REGISTER_TIME = 5
COMPONENTE_1 = [ num for num in range(1, 9)]
COMPONENTE_2 = [ num for num in range(10, 25)]
MAX_DIPONIBILITY_PROPORTION = 1.1

class Registrador:

    instance: 'Registrador' = None
    
    def __init__(self) -> None:
        self.numero_requisicoes_por_classe: dict[int, int] = {1:0, 2:0, 3:0}
        self.numero_requisicoes_bloqueadas_por_classe: dict[int, int] = {1:0, 2:0, 3:0}
        self.numero_requisicoes_por_banda: dict[int, int] = { 100:0, 150:0, 200:0, 250:0, 300:0, 350:0, 400:0}
        self.numero_requisicoes_bloqueadas_por_banda: dict[int, int] = { 100:0, 150:0, 200:0, 250:0, 300:0, 350:0, 400:0}

        self.numero_requisicoes_afetadas_desastre: int = 0

        self.numero_reroteadas_por_classe: dict[int, int] = {1:0, 2:0, 3:0}
        self.numero_reroteadas_bloqueadas_por_classe: dict[int, int] = {1:0, 2:0, 3:0}
        self.numero_reroteadas_por_banda: dict[int, int] = { 100:0, 150:0, 200:0, 250:0, 300:0, 350:0, 400:0}
        self.numero_reroteadas_bloqueadas_por_banda: dict[int, int] = { 100:0, 150:0, 200:0, 250:0, 300:0, 350:0, 400:0}

        self.numero_requisicoes_aceitas: int = 0
        self.numero_requisicoes_bloqueadas: int = 0
        self.numero_requisicoes_reroteadas: int = 0
        self.numero_requisicoes_reroteadas_bloqueadas: int = 0
        self.requisicoes :list[Requisicao] = []
    
        self.migracao_concluida: dict[tuple[float, float]] = {}
        self.janela_deslizante_taxa_de_bloqueio_por_par_de_nodes: defaultdict[int, list[int]] = defaultdict(lambda: [0, 0])
        self.media_taxa_de_disponibilidade_extra_componente: list[int] = [0, 0]
        self.registro_janela_deslizante: list[dict[int, float]] = []
        self.registro_media_taxa_de_disponibilidade_extra_componente: list[int] = []
        self.current_bloqueio_artificial: dict[int, int] = {
            i: 0 for i in range(1, 25) if i != 9
        }
        self.registro_bloqueio_artificial: list[dict[int, float]] = []
        self.sim_finalizada: bool = False

    @staticmethod
    def get_intance() -> 'Registrador':
        if Registrador.instance == None:
            Registrador.instance = Registrador()
        return Registrador.instance
    
    @staticmethod
    def inicia_registro_janela_deslizante(env: simpy.Environment) -> Generator:
        registrador: Registrador = Registrador.get_intance()
        while (not registrador.sim_finalizada):
            yield env.timeout(REGISTER_TIME)
            ## Atualiza a janela deslizante
            new_sliding_window = {}
            for key, value in registrador.janela_deslizante_taxa_de_bloqueio_por_par_de_nodes.items():
                accepted, blocked = value[0], value[1]
                if accepted + blocked != 0:
                    new_sliding_window[key] = accepted/(accepted + blocked)
                else:
                    new_sliding_window[key] = None
            registrador.registro_janela_deslizante.append(new_sliding_window)

            ## Atualiza a media da taxa de bloqueio extra componente
            current_state = deepcopy(registrador.media_taxa_de_disponibilidade_extra_componente)
            accepted, blocked = current_state[0], current_state[1]
            media_taxa_de_disponibilidade_extra_componente = None
            if accepted + blocked != 0:
                media_taxa_de_disponibilidade_extra_componente = accepted/(accepted + blocked)
            registrador.registro_media_taxa_de_disponibilidade_extra_componente.append(media_taxa_de_disponibilidade_extra_componente)

            ## Atualiza o bloqueio artificial
            new_bloqueio_artificial = deepcopy(registrador.current_bloqueio_artificial)
            for key, value in new_bloqueio_artificial.items():
                if new_sliding_window[key] > media_taxa_de_disponibilidade_extra_componente * MAX_DIPONIBILITY_PROPORTION:
                    base_probabilidade = 1 - (media_taxa_de_disponibilidade_extra_componente * MAX_DIPONIBILITY_PROPORTION / new_sliding_window[key])
                    fator_ajuste = 1 + registrador.current_bloqueio_artificial.get(key, 0)
                    new_bloqueio_artificial[key] = min(max(base_probabilidade * fator_ajuste, 0), 1)
                else:
                    current_block = registrador.current_bloqueio_artificial.get(key, 0)
                    if current_block > 0:
                        ratio = new_sliding_window[key] / (media_taxa_de_disponibilidade_extra_componente)
                        reduction_factor = min(1 - ratio, 0.5)
                        new_bloqueio_artificial[key] = max(current_block * (1 - reduction_factor), 0)
                    else:
                        new_bloqueio_artificial[key] = 0

            registrador.registro_bloqueio_artificial.append(new_bloqueio_artificial)

    @staticmethod
    def get_last_registro_bloqueio_artificial_por_node(node: int) -> float:
        registrador: Registrador = Registrador.get_intance()
        return registrador.registro_bloqueio_artificial[-1][node]
            

    @staticmethod
    def finaliza_registro_janela_deslizante() -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.sim_finalizada = True

    @staticmethod
    def adiciona_registro_janela_deslizante(registro: dict[tuple[int, int], (int, int)]) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.registro_janela_deslizante.append(registro)
    
    @staticmethod
    def reseta_registrador() -> None:
        Registrador.instance = Registrador()

    @staticmethod
    def porcentagem_de_dados_enviados(isp_id: int, time: int, percentual: float) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.migracao_concluida[isp_id] = (time, percentual)

    @staticmethod
    def get_requisicoes() -> list[Requisicao]:
        registrador: Registrador = Registrador.get_intance()
        return registrador.requisicoes
        
    @staticmethod
    def registra_bloqueio_artificial(node: int, bloqueio: float) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.current_bloqueio_artificial[node] = bloqueio
    
    @staticmethod
    def registra_requisicao_afetada( req: Requisicao) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_afetadas_desastre += 1
        registrador.numero_reroteadas_por_classe[req.class_type] += 1
        registrador.numero_reroteadas_por_banda[req.bandwidth] += 1

    
    @staticmethod
    def adiciona_requisicao(requisicao: int ) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.requisicoes.append(requisicao)

    @staticmethod
    def conta_requisicao_banda(banda: int ) -> None:

        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_por_banda[banda] += 1

    @staticmethod
    def conta_requisicao_classe(classe: int ) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_por_classe[classe] += 1

    @staticmethod
    def atualiza_taxa_de_bloqueio_por_par_de_nodes( req: Requisicao, env: simpy.Environment, blocked: bool = False) -> Generator:
        is_extra_component_traffic = (req.src in COMPONENTE_1 and req.dst in COMPONENTE_2) or (req.src in COMPONENTE_2 and req.dst in COMPONENTE_1)
        if not(is_extra_component_traffic):
            return
        registrador: Registrador = Registrador.get_intance()
        registrador.media_taxa_de_disponibilidade_extra_componente[blocked] += 1
        registrador.janela_deslizante_taxa_de_bloqueio_por_par_de_nodes[req.src][blocked] += 1
        yield env.timeout(SLIDING_WINDOW_TIME)
        registrador.janela_deslizante_taxa_de_bloqueio_por_par_de_nodes[req.src][blocked] -= 1
        registrador.media_taxa_de_disponibilidade_extra_componente[blocked] -= 1


    @staticmethod
    def incrementa_numero_requisicoes_aceitas( req: Requisicao, env: simpy.Environment) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_aceitas +=1
        env.process(Registrador.atualiza_taxa_de_bloqueio_por_par_de_nodes(req, env))
    

    @staticmethod
    def incrementa_numero_requisicoes_bloqueadas( req: Requisicao, env: simpy.Environment) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_bloqueadas += 1
        registrador.numero_requisicoes_bloqueadas_por_banda[req.bandwidth] += 1
        registrador.numero_requisicoes_bloqueadas_por_classe[req.class_type] += 1
        env.process(Registrador.atualiza_taxa_de_bloqueio_por_par_de_nodes(req, env, True))

    @staticmethod
    def incrementa_numero_requisicoes_reroteadas_aceitas( req: Requisicao, env: simpy.Environment) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_reroteadas += 1  
        env.process(Registrador.atualiza_taxa_de_bloqueio_por_par_de_nodes(req, env))

    @staticmethod
    def incrementa_numero_requisicoes_reroteadas_bloqueadas( req: Requisicao, env: simpy.Environment) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_reroteadas_bloqueadas += 1
        registrador.numero_reroteadas_bloqueadas_por_banda[req.bandwidth] += 1
        registrador.numero_reroteadas_bloqueadas_por_classe[req.class_type] += 1
        env.process(Registrador.atualiza_taxa_de_bloqueio_por_par_de_nodes(req, env, True))

    @staticmethod
    def printa_parametros() -> None:
        registrador: Registrador = Registrador.get_intance()
        print("Numero de requisicoes por classe: ", registrador.numero_requisicoes_por_classe)
        print("Numero de requisicoes bloqueadas por classe: ", registrador.numero_requisicoes_bloqueadas_por_classe)
        print("Numero de requisicoes por banda: ", registrador.numero_requisicoes_por_banda)
        print("Numero de requisicoes bloqueadas por banda: ", registrador.numero_requisicoes_bloqueadas_por_banda)
        print("Numero de requisicoes reroteadas por classe: ", registrador.numero_reroteadas_por_classe)
        print("Numero de requisicoes reroteadas bloqueadas por classe: ", registrador.numero_reroteadas_bloqueadas_por_classe)
        print("Numero de requisicoes reroteadas por banda: ", registrador.numero_reroteadas_por_banda)
        print("Numero de requisicoes reroteadas bloqueadas por banda: ", registrador.numero_reroteadas_bloqueadas_por_banda)
        print("Numero de requisicoes: ", registrador.numero_requisicoes_aceitas + registrador.numero_requisicoes_bloqueadas)
        print("Numero de requisicoes bloqueadas: ", registrador.numero_requisicoes_bloqueadas)
        print("Numero de requisicoes afetadas por desastre: ", registrador.numero_requisicoes_afetadas_desastre)
        print("Numero de requisicoes reroteadas aceitas: ", registrador.numero_requisicoes_reroteadas)
        print("Numero de requisicoes reroteadas bloqueadas: ", registrador.numero_requisicoes_reroteadas_bloqueadas)
        print("Momentos da migração concluída: ", registrador.migracao_concluida)
        
    @staticmethod
    def criar_dataframe( nome: str) -> None:
        registrador: Registrador = Registrador.get_intance()

        data = {}
        for req in registrador.requisicoes:
            data[req.id] = req.retorna_tupla_chave_dicionario_dos_atributos()[1]
        
        df = pd.DataFrame.from_dict(data, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'Index da Requisição'}, inplace=True)

        df.to_csv(f'{nome}.csv')
        return df
    
    @staticmethod
    def cria_dataframe_janela_deslizante(nome: str) -> pd.DataFrame:
        registrador: Registrador = Registrador.get_intance()
        df = pd.DataFrame(registrador.registro_janela_deslizante)
        df.to_csv(f'{nome}_sliding_window.csv')
        return df
    
    @staticmethod
    def cria_dataframe_media_taxa_de_disponibilidade_extra_componente(nome: str) -> pd.DataFrame:
        registrador: Registrador = Registrador.get_intance()
        df = pd.DataFrame(registrador.registro_media_taxa_de_disponibilidade_extra_componente)
        df.to_csv(f'{nome}_media_taxa_de_disponibilidade_extra_componente.csv')
        return df
    @staticmethod
    def cria_dataframe_bloqueio_artificial(nome: str) -> pd.DataFrame:
        registrador: Registrador = Registrador.get_intance()
        df = pd.DataFrame(registrador.registro_bloqueio_artificial)
        df.to_csv(f'{nome}_bloqueio_artificial.csv')
        return df
    
    @staticmethod
    def salva_resutados(self, caminho: str) -> None:
        with open(f'{caminho}', 'w') as f:
            json.dump(self.__dict__, f, indent=4)