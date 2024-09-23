from Requisicao.Requisicao import Requisicao
import pandas as pd

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

        self.numero_requisicoes: int = 0
        self.numero_requisicoes_bloqueadas: int = 0
        self.numero_requisicoes_reroteadas: int = 0
        self.numero_requisicoes_reroteadas_bloqueadas: int = 0
        self.requisicoes :list[Requisicao] = []
    
        self.migracao_concluida: dict[tuple[float, float]] = {}

    def get_intance() -> 'Registrador':
        if Registrador.instance == None:
            Registrador.instance = Registrador()
        return Registrador.instance
    
    def porcentagem_de_dados_enviados(isp_id: int, time: int, percentual: float) -> None:
        registrador: Registrador = Registrador.get_intance()

        registrador.migracao_concluida[isp_id] = (time, percentual)

    def get_requisicoes() -> list[Requisicao]:
        registrador: Registrador = Registrador.get_intance()
        return registrador.requisicoes
    
    def registra_numero_de_afetadas( numero_de_afetadas: int) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_afetadas_desastre = numero_de_afetadas
    
    def adiciona_requisicao(requisicao: int ) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.requisicoes.append(requisicao)

    def conta_requisicao_banda(banda: int ) -> None:

        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_por_banda[banda] += 1

    def conta_requisicao_classe(classe: int ) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_por_classe[classe] += 1

    def conta_bloqueio_requisicao_banda( banda: int ) -> None:

        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_bloqueadas_por_banda[banda] += 1

    def conta_bloqueio_requisicao_classe( classe: int ) -> None:

        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_bloqueadas_por_classe[classe] += 1

    def conta_reroteadas_por_classe(classe: int ) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_reroteadas_por_classe[classe] += 1
    
    def conta_reroteadas_por_banda(banda: int ) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_reroteadas_por_banda[banda] += 1
    
    def conta_bloqueio_reroteadas_por_classe(classe: int ) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_reroteadas_bloqueadas_por_classe[classe] += 1

    def conta_bloqueio_reroteadas_por_banda(banda: int ) -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_reroteadas_bloqueadas_por_banda[banda] += 1
        
    def incrementa_numero_requisicoes() -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes +=1

    def incrementa_numero_requisicoes_bloqueadas() -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_bloqueadas +=1

    def incrementa_numero_requisicoes_reroteadas() -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_reroteadas += 1
    
    def incrementa_numero_requisicoes_reroteadas_bloqueadas() -> None:
        registrador: Registrador = Registrador.get_intance()
        registrador.numero_requisicoes_reroteadas_bloqueadas += 1

    def printa_parametros() -> None:
        registrador: Registrador = Registrador.get_intance()
        print("Numero de requisicoes por classe: ", registrador.numero_requisicoes_por_classe)
        print("Numero de requisicoes bloqueadas por classe: ", registrador.numero_requisicoes_bloqueadas_por_classe)
        print("Numero de requisicoes por banda: ", registrador.numero_requisicoes_por_banda)
        print("Numero de requisicoes bloqueadas por banda: ", registrador.numero_requisicoes_bloqueadas_por_banda)
        print("Numero de requisicoes afetadas por desastre: ", registrador.numero_requisicoes_afetadas_desastre)
        print("Numero de requisicoes reroteadas por classe: ", registrador.numero_reroteadas_por_classe)
        print("Numero de requisicoes reroteadas bloqueadas por classe: ", registrador.numero_reroteadas_bloqueadas_por_classe)
        print("Numero de requisicoes reroteadas por banda: ", registrador.numero_reroteadas_por_banda)
        print("Numero de requisicoes reroteadas bloqueadas por banda: ", registrador.numero_reroteadas_bloqueadas_por_banda)
        print("Numero de requisicoes: ", registrador.numero_requisicoes)
        print("Numero de requisicoes bloqueadas: ", registrador.numero_requisicoes_bloqueadas)
        print("Numero de requisicoes reroteadas: ", registrador.numero_requisicoes_reroteadas)
        print("Numero de requisicoes reroteadas bloqueadas: ", registrador.numero_requisicoes_reroteadas_bloqueadas)
        print("Momento da migração concluída: ", registrador.migracao_concluida)
    def criar_dataframe() -> None:
        registrador: Registrador = Registrador.get_intance()

        data = {}
        for req in registrador.requisicoes:
            data[req.id] = req.retorna_tupla_chave_dicionario_dos_atributos()[1]
        
        df = pd.DataFrame.from_dict(data, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'Index da Requisição'}, inplace=True)

        df.to_csv('_out/dataframe.csv')
        return df