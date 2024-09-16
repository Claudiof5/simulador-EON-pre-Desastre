import simpy
import simpy.events

class Requisicao:

    def __init__(self, id, src, dst, src_ISP, dst_ISP, bandwidth, class_type, holding_time):
        self.id = id
        self.src = src
        self.dst = dst
        self.src_ISP_index = src_ISP
        self.src_ISP_index = dst_ISP
        self.bandwidth = bandwidth
        self.class_type = class_type
        self.holding_time = holding_time
        self.resultados_requisicao = None
        self.bloqueada = None
        self.processo_de_desalocacao :simpy.events.Process = None
    

    def bloqueia_requisicao(self, tempo_criacao):
        self.bloqueada = True

        self.resultados_requisicao = ({"num_slots":None, "path":None,"path_length": None,"spectro":None, "tempo_criacao":tempo_criacao , "tempo_desalocacao":None, "distacia":None, "blocked":True})
        
    					
    def aceita_requisicao(self, num_slots, path, path_length, spectro, tempo_criacao, tempo_desalocacao, distancia):
        self.bloqueada = False

        self.resultados_requisicao = ({"num_slots":num_slots, "path":path,"path_length": path_length,"spectro":spectro,
                                            "tempo_criacao":tempo_criacao , "tempo_desalocacao":tempo_desalocacao, "distacia":distancia, "blocked":False})
   