class Contador:

    def __init__(self) -> None:
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
    # Computa numero de requisicoes por banda
    def conta_requisicao_banda(self, banda):
        if banda == 100:
            self.NumReq_100 += 1
        elif banda == 150:
            self.NumReq_150 += 1
        elif banda == 200:
            self.NumReq_200 += 1
        elif banda == 250:
            self.NumReq_250 += 1
        elif banda == 300:
            self.NumReq_300 += 1
        elif banda == 350:
            self.NumReq_350 += 1
        else:
            self.NumReq_400 += 1

    # Computa o numero de requisicoes por classe
    def conta_requisicao_classe(self, classe):
        if classe == 1:
            self.NumReq_classe1 += 1
        elif classe == 2:
            self.NumReq_classe2 += 1
        else:
            self.NumReq_classe3 += 1
            
    # Computa numero de bloqueio por banda
    def conta_bloqueio_requisicao_banda(self, banda):
        if banda == 100:
            self.NumReqBlocked_100 += 1
        elif banda == 150:
            self.NumReqBlocked_150 += 1
        elif banda == 200:
            self.NumReqBlocked_200 += 1
        elif banda == 250:
            self.NumReqBlocked_250 += 1
        elif banda == 300:
            self.NumReqBlocked_300 += 1
        elif banda == 350:
            self.NumReqBlocked_350 += 1
        else:
            self.NumReqBlocked_400 += 1

    # Computa numero de requisicoes bloqueadas por classe
    def conta_bloqueio_requisicao_classe(self, classe):
        if classe == 1:
            self.NumReqBlocked_classe1 += 1
        elif classe == 2:
            self.NumReqBlocked_classe2 += 1
        else:
            self.NumReqBlocked_classe3 += 1


    def Bloqueio_falha_od_cos(self, cos):
        if cos == 1:
            self.total_req_afetadas_od_cos1 += 1
        elif cos == 2:
            self.total_req_afetadas_od_cos2 += 1
        else:
            self.total_req_afetadas_od_cos3 += 1

    def Bloqueio_falha_od_banda(self, banda):
        if banda == 100:
            self.total_req_afetadas_od_100 += 1
        elif banda == 150:
            self.total_req_afetadas_od_150 += 1
        elif banda == 200:
            self.total_req_afetadas_od_200 += 1
        elif banda == 250:
            self.total_req_afetadas_od_250 += 1
        elif banda == 300:
            self.total_req_afetadas_od_300 += 1
        elif banda == 350:
            self.total_req_afetadas_od_350 += 1
        else:
            self.total_req_afetadas_od_400 += 1

    def Bloqueio_rerroteamento_cos_pr(self, cos):
        if cos == 1:
            self.bloqueio_rerroteamento_cos1_pr += 1
        elif cos == 2:
            self.bloqueio_rerroteamento_cos2_pr += 1
        else:
            self.bloqueio_rerroteamento_cos3_pr += 1
    def Bloqueio_rerroteamento_banda_pr(self, banda):
        if banda == 100:
            self.bloqueio_rerroteamento_100_pr +=1
        elif banda == 150:
            self.bloqueio_rerroteamento_150_pr +=1
        elif banda == 200:
            self.bloqueio_rerroteamento_200_pr +=1
        elif banda == 250:
            self.bloqueio_rerroteamento_250_pr +=1
        elif banda == 300:
            self.bloqueio_rerroteamento_300_pr +=1
        elif banda == 350:
            self.bloqueio_rerroteamento_350_pr +=1
        else:
            self.bloqueio_rerroteamento_400_pr += 1