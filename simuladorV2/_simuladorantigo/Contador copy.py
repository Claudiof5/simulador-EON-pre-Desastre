class Contador:


    instance = None

    def get_intance():
        if Contador.instance == None:
            Contador.instance = Contador()
        return Contador.instance
    
    def __init__(self) -> None:
        self.Numero_Requisicoes_por_classe = {1:0, 2:0, 3:0}
        self.NumReq_classe1 = 0
        self.NumReq_classe2 = 0
        self.NumReq_classe3 = 0
        self.NumReqBlocked_classe1 = 0
        self.NumReqBlocked_classe2 = 0
        self.NumReqBlocked_classe3 = 0
        self.total_req_afetadas_od_cos1 = 0
        self.total_req_afetadas_od_cos2 = 0
        self.total_req_afetadas_od_cos3 = 0
        self.total_req_afetadas_od_100 = 0
        self.total_req_afetadas_od_150 = 0
        self.total_req_afetadas_od_200 = 0
        self.total_req_afetadas_od_250 = 0
        self.total_req_afetadas_od_300 = 0
        self.total_req_afetadas_od_350 = 0
        self.total_req_afetadas_od_400 = 0
        self.NumReq_100 = 0
        self.NumReq_150 = 0
        self.NumReq_200 = 0
        self.NumReq_250 = 0
        self.NumReq_300 = 0
        self.NumReq_350 = 0
        self.NumReq_400 = 0
        self.NumReqBlocked_100 = 0
        self.NumReqBlocked_150 = 0
        self.NumReqBlocked_200 = 0
        self.NumReqBlocked_250 = 0
        self.NumReqBlocked_300 = 0
        self.NumReqBlocked_350 = 0
        self.NumReqBlocked_400 = 0
        self.bloqueio_rerroteamento_cos1_pr = 0
        self.bloqueio_rerroteamento_cos2_pr = 0
        self.bloqueio_rerroteamento_cos3_pr = 0
        self.bloqueio_rerroteamento_100_pr = 0
        self.bloqueio_rerroteamento_150_pr = 0
        self.bloqueio_rerroteamento_200_pr = 0
        self.bloqueio_rerroteamento_250_pr = 0
        self.bloqueio_rerroteamento_300_pr = 0
        self.bloqueio_rerroteamento_350_pr = 0
        self.bloqueio_rerroteamento_400_pr = 0
        self.total_req_afetadas_od = 0
        self.NumReqBlocked = 0
        self.cont_req = 0
        self.total_req_restauradas_pr_pr = 0
        self.total_req_afetadas_od_pr = 0
        self.restauradasF = 0
        self.afetadasF = 0
        self.Qtd_sol_Numsaltos = 0 
        self.total_req_restauradas = 0
        self.bloqueio_rerroteamento_pr = 0
        self.bloqueio_rerroteamento_pr_pr = 0
        self.bloqueio_rerroteamento_pr_ahp_pr = 0
        self.bloqueio_rerroteamento_pr_ahp_dg_pr = 0   
             
    def conta_requisicao_banda(banda):

        contador = Contador.get_intance()
        
        if banda == 100:
            contador.NumReq_100 += 1
        elif banda == 150:
            contador.NumReq_150 += 1
        elif banda == 200:
            contador.NumReq_200 += 1
        elif banda == 250:
            contador.NumReq_250 += 1
        elif banda == 300:
            contador.NumReq_300 += 1
        elif banda == 350:
            contador.NumReq_350 += 1
        else:
            contador.NumReq_400 += 1


    def conta_requisicao_classe(classe):
        
        contador = Contador.get_intance()
        contador.Numero_Requisicoes_por_classe[classe] += 1
        if classe == 1:
            contador.NumReq_classe1 += 1
        elif classe == 2:
            contador.NumReq_classe2 += 1
        else:
            contador.NumReq_classe3 += 1
            
    def conta_bloqueio_requisicao_banda( banda):

        
        contador = Contador.get_intance()

        if banda == 100:
            contador.NumReqBlocked_100 += 1
        elif banda == 150:
            contador.NumReqBlocked_150 += 1
        elif banda == 200:
            contador.NumReqBlocked_200 += 1
        elif banda == 250:
            contador.NumReqBlocked_250 += 1
        elif banda == 300:
            contador.NumReqBlocked_300 += 1
        elif banda == 350:
            contador.NumReqBlocked_350 += 1
        else:
            contador.NumReqBlocked_400 += 1

    def conta_bloqueio_requisicao_classe( classe):

        contador = Contador.get_intance()

        if classe == 1:
            contador.NumReqBlocked_classe1 += 1
        elif classe == 2:
            contador.NumReqBlocked_classe2 += 1
        else:
            contador.NumReqBlocked_classe3 += 1

    def Bloqueio_falha_od_cos(cos):

        contador = Contador.get_intance()

        if cos == 1:
            contador.total_req_afetadas_od_cos1 += 1
        elif cos == 2:
            contador.total_req_afetadas_od_cos2 += 1
        else:
            contador.total_req_afetadas_od_cos3 += 1

    def Bloqueio_falha_od_banda( banda):
        contador = Contador.get_intance()

        if banda == 100:
            contador.total_req_afetadas_od_100 += 1
        elif banda == 150:
            contador.total_req_afetadas_od_150 += 1
        elif banda == 200:
            contador.total_req_afetadas_od_200 += 1
        elif banda == 250:
            contador.total_req_afetadas_od_250 += 1
        elif banda == 300:
            contador.total_req_afetadas_od_300 += 1
        elif banda == 350:
            contador.total_req_afetadas_od_350 += 1
        else:
            contador.total_req_afetadas_od_400 += 1

    def Bloqueio_rerroteamento_cos_pr( cos):
        contador = Contador.get_intance()

        if cos == 1:
            contador.bloqueio_rerroteamento_cos1_pr += 1
        elif cos == 2:
            contador.bloqueio_rerroteamento_cos2_pr += 1
        else:
            contador.bloqueio_rerroteamento_cos3_pr += 1

    def Bloqueio_rerroteamento_banda_pr( banda):
        contador = Contador.get_intance()
        if banda == 100:
            contador.bloqueio_rerroteamento_100_pr +=1
        elif banda == 150:
            contador.bloqueio_rerroteamento_150_pr +=1
        elif banda == 200:
            contador.bloqueio_rerroteamento_200_pr +=1
        elif banda == 250:
            contador.bloqueio_rerroteamento_250_pr +=1
        elif banda == 300:
            contador.bloqueio_rerroteamento_300_pr +=1
        elif banda == 350:
            contador.bloqueio_rerroteamento_350_pr +=1
        else:
            contador.bloqueio_rerroteamento_400_pr += 1

    def incrementa_numero_requisicoes_bloqueadas():
        contador = Contador.get_intance()
        contador.NumReqBlocked +=1

    def incrementa_numero_requisicoes():
        contador = Contador.get_intance()
        contador.cont_req +=1