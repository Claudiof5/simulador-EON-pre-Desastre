class Contador:


    instance = None

    def get_intance():
        if Contador.instance == None:
            Contador.instance = Contador()
        return Contador.instance
    
    def __init__(self) -> None:
        self.numero_requisicoes_por_classe = {1:0, 2:0, 3:0}
        self.numero_requisicoes_bloqueadas_por_classe = {1:0, 2:0, 3:0}
        self.numero_requisicoes_por_banda = { 100:0, 150:0, 200:0, 250:0, 300:0, 350:0, 400:0}
        self.numero_requisicoes_bloqueadas_por_banda = { 100:0, 150:0, 200:0, 250:0, 300:0, 350:0, 400:0}

        self.numero_requisicoes_afetadas_desastre = 0

        self.numero_reroteadas_por_classe = {1:0, 2:0, 3:0}
        self.numero_reroteadas_bloqueadas_por_classe = {1:0, 2:0, 3:0}
        self.numero_reroteadas_por_banda = { 100:0, 150:0, 200:0, 250:0, 300:0, 350:0, 400:0}
        self.numero_reroteadas_bloqueadas_por_banda = { 100:0, 150:0, 200:0, 250:0, 300:0, 350:0, 400:0}

        self.numero_requisicoes = 0
        self.numero_requisicoes_bloqueadas = 0
        self.numero_requisicoes_reroteadas = 0
        self.numero_requisicoes_reroteadas_bloqueadas = 0
        
             
    def conta_requisicao_banda(banda):

        contador = Contador.get_intance()
        
        contador.numero_requisicoes_por_banda[banda] += 1

    def conta_requisicao_classe(classe):
        contador = Contador.get_intance()
        contador.numero_requisicoes_por_classe[classe] += 1

    def conta_bloqueio_requisicao_banda( banda):

        contador = Contador.get_intance()
        contador.numero_requisicoes_bloqueadas_por_banda[banda] += 1

    def conta_bloqueio_requisicao_classe( classe):

        contador = Contador.get_intance()
        contador.numero_requisicoes_bloqueadas_por_classe(classe) += 1

    def conta_reroteadas_por_classe(classe):
        contador = Contador.get_intance()
        contador.numero_requisicoes_reroteadas[classe] += 1
    
    def conta_reroteadas_por_banda(banda):
        contador = Contador.get_intance()
        contador.numero_requisicoes_reroteadas[banda] += 1
    
    def conta_bloqueio_reroteadas_por_classe(classe):
        contador = Contador.get_intance()
        contador.conta_bloqueio_reroteadas_por_classe[classe] += 1

    def conta_bloqueio_reroteadas_por_banda(banda):
        contador = Contador.get_intance()
        contador.conta_bloqueio_reroteadas_por_banda[banda] += 1
        
    def incrementa_numero_requisicoes():
        contador = Contador.get_intance()
        contador.numero_requisicoes +=1

    def incrementa_numero_requisicoes_bloqueadas():
        contador = Contador.get_intance()
        contador.numero_requisicoes_bloqueadas +=1

    def incrementa_numero_requisicoes_reroteadas():
        contador = Contador.get_intance()
        contador.numero_requisicoes_reroteadas += 1
    
    def incrementa_numero_requisicoes_reroteadas_bloqueadas():
        contador = Contador.get_intance()
        contador.numero_requisicoes_reroteadas_bloqueadas += 1

    def printa_parametros():
        contador = Contador.get_intance()
        print("Numero de requisicoes por classe: ", contador.numero_requisicoes_por_classe)
        print("Numero de requisicoes bloqueadas por classe: ", contador.numero_requisicoes_bloqueadas_por_classe)
        print("Numero de requisicoes por banda: ", contador.numero_requisicoes_por_banda)
        print("Numero de requisicoes bloqueadas por banda: ", contador.numero_requisicoes_bloqueadas_por_banda)
        print("Numero de requisicoes afetadas por desastre: ", contador.numero_requisicoes_afetadas_desastre)
        print("Numero de requisicoes reroteadas por classe: ", contador.numero_reroteadas_por_classe)
        print("Numero de requisicoes reroteadas bloqueadas por classe: ", contador.numero_reroteadas_bloqueadas_por_classe)
        print("Numero de requisicoes reroteadas por banda: ", contador.numero_reroteadas_por_banda)
        print("Numero de requisicoes reroteadas bloqueadas por banda: ", contador.numero_reroteadas_bloqueadas_por_banda)
        print("Numero de requisicoes: ", contador.numero_requisicoes)
        print("Numero de requisicoes bloqueadas: ", contador.numero_requisicoes_bloqueadas)
        print("Numero de requisicoes reroteadas: ", contador.numero_requisicoes_reroteadas)
        print("Numero de requisicoes reroteadas bloqueadas: ", contador.numero_requisicoes_reroteadas_bloqueadas)
