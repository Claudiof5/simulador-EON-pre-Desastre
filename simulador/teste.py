import simpy
import numpy as np
import networkx as nx
import math
from random import Random
from VARIAVEIS import *
from utils import k_shortest_paths, Modulation, FatorModulation
from contador import Contador

class Simulador:
    def __init__(self, env: simpy.Environment, topology, rate):
        self.random = Random()
        self.env = env
        self.topology = topology
        self.nodes = list(topology.nodes())
        self.contador = Contador()

        self.init_topology()
        self.init_variables()

        self.action = env.process(self.run(rate))
        self.env.process(self.interrupt_simulation(1800))
        self.timeSimFim = None

    def init_topology(self):
        for u, v in self.topology.edges:
            self.topology[u][v]['capacity'] = [0] * SLOTS

    def init_variables(self):
        self.solicitacoes_em_andamento = []
        self.req = {}
        self.ativo = {}
        self.k_paths = {}
        self.LINK_POINTSF = []
        self.NODE_POINTSF = []
        self.Simfim = False
        self.sum_time_up = 0
        self.sum_ht = 0
        self.Vet_NumReqBlocked2x = []
        self.NumReqBlocked2x = []
        self.Numsaltos = 0
        self.desalocateReq1 = []
        self.desalocateReq2 = []
        self.desalocateReqRerr = []
        self.desalocateReqRerr2 = []
        self.mensagem_impressa = False
        self.afetadas_pr = []
        self.nao_restauradas_pr = []
        self.rr_nao_restauradas_pr = []

    def run(self, rate):
        try:
            self.preprocess_paths()
            for count in range(1, NUM_OF_REQUESTS + 1):
                yield self.env.timeout(self.random.expovariate(rate))
                class_type, src, dst, bandwidth, holding_time = self.generate_request()

                if self.is_blocked(src, dst):
                    self.handle_blocked_request(count, class_type, bandwidth)
                else:
                    self.handle_request(count, class_type, src, dst, bandwidth, holding_time)
            self.end_simulation()
        except simpy.Interrupt:
            print("Simulation interrupted at time", self.env.now)

    def preprocess_paths(self):
        for i in self.topology.nodes():
            for j in self.topology.nodes():
                if i != j:
                    self.k_paths[i, j] = k_shortest_paths(self.topology, i, j, N_PATH, weight='weight')

    def generate_request(self):
        class_type = np.random.choice(CLASS_TYPE, p=CLASS_WEIGHT)
        src, dst = self.random.sample(self.nodes, 2)
        bandwidth = self.random.choice(BANDWIDTH)
        holding_time = self.random.expovariate(HOLDING_TIME)
        self.sum_ht += holding_time

        self.contador.conta_requisicao_banda(bandwidth)
        self.contador.conta_requisicao_classe(class_type)

        return class_type, src, dst, bandwidth, holding_time

    def is_blocked(self, src, dst):
        return self.topology.has_edge(src, dst) and 'failed' in self.topology[src][dst] and self.topology[src][dst]['failed']

    def handle_blocked_request(self, count, class_type, bandwidth):
        self.contador.total_req_afetadas_od += 1
        self.contador.NumReqBlocked += 1
        self.Vet_NumReqBlocked2x.append(count)
        self.contador.Bloqueio_falha_od_cos(class_type)
        self.contador.Bloqueio_falha_od_banda(bandwidth)

    def handle_request(self, count, class_type, src, dst, bandwidth, holding_time):
        paths = self.k_paths[src, dst]
        capacity, datapaths = self.calculate_capacity(paths, bandwidth)

        if capacity >= bandwidth:
            self.allocate_request(count, class_type, bandwidth, holding_time, datapaths)
        else:
            self.block_request(count, class_type, bandwidth)

    def calculate_capacity(self, paths, bandwidth):
        capacity = 0
        datapaths = []

        for path in paths:
            distance = self.distance(path)
            fatormodulation = FatorModulation(distance)
            free_slots, free_slots_matrix, inslotsfree_matrix = self.max_flow(path)
            freeslots_sun = len(free_slots)
            capacity_calc = fatormodulation * freeslots_sun
            capacity += capacity_calc
            num_slots = math.ceil(Modulation(distance, bandwidth))
            datapaths.append({
                "path": path,
                "distance": distance,
                "fatormodulation": fatormodulation,
                "freeslots_sun": freeslots_sun,
                "capacity_calc": capacity_calc,
                "free_slots_matrix": free_slots_matrix,
                "free_slots": free_slots,
                "inslotsfree_matrix": inslotsfree_matrix,
                "num_slots": num_slots
            })

        return capacity, datapaths

    def allocate_request(self, count, class_type, bandwidth, holding_time, datapaths):
        cont_bandwidth = bandwidth
        flag = False

        for path_data in datapaths:
            for paths_able in path_data["inslotsfree_matrix"]:
                inicio, fim = paths_able
                transporte = path_data["fatormodulation"] * (fim - inicio + 1)
                dados_sol = {"caminho": path_data["path"], "inicio": inicio, "fim": fim}

                if transporte > cont_bandwidth:
                    dados_sol["fim"] = inicio + math.ceil(Modulation(path_data["distance"], cont_bandwidth)) - 1

                cont_bandwidth -= transporte
                self.allocate_spectrum(count, dados_sol["inicio"], dados_sol["fim"], dados_sol["caminho"])
                spectro = [dados_sol["inicio"], dados_sol["fim"]]
                self.req[count] = self.create_request_entry(count, class_type, path_data["num_slots"], dados_sol["caminho"], spectro, holding_time, path_data["distance"], bandwidth, False)
                self.ativo[count] = 1
                self.env.process(self.desalocate(count, dados_sol["caminho"], spectro, holding_time))

                if cont_bandwidth == 0:
                    flag = True
                    break
            if flag:
                break

    def create_request_entry(self, count, class_type, num_slots, caminho, spectro, holding_time, distance, bandwidth, blocked):
        return {
            "num": count,
            "class": class_type,
            "num_slots": num_slots,
            "path": caminho,
            "path_length": len(caminho),
            "spectro": spectro,
            "tempo_criacao": self.env.now,
            "tempo_desalocacao": self.env.now + holding_time,
            "distancia": distance,
            "bandwidth": bandwidth,
            "blocked": blocked
        }

    def block_request(self, count, class_type, bandwidth):
        self.req[count] = self.create_request_entry(count, class_type, None, None, None, None, None, bandwidth, True)
        self.contador.NumReqBlocked += 1
        self.Vet_NumReqBlocked2x.append(count)
        self.contador.conta_bloqueio_requisicao_banda(bandwidth)
        self.contador.conta_bloqueio_requisicao_classe(class_type)

    def end_simulation(self):
        print(f"Simulation end at {self.env.now}")
        self.timeSimFim = self.env.now
        self.Simfim = True

    def max_flow(self, path):
        current_consecutive = self.find_consecutive_slots(path)
        grupos, if_grupos = self.group_consecutive_slots(current_consecutive)

        return current_consecutive, grupos, if_grupos

    def find_consecutive_slots(self, path):
        current_consecutive = []

        for slot in range(len(self.topology[path[0]][path[1]]['capacity'])):
            if all(self.topology[path[ind]][path[ind + 1]]['capacity'][slot] == 0 for ind in range(len(path) - 1)):
                current_consecutive.append(slot)

        return current_consecutive

    def group_consecutive_slots(self, slots):
        grupos = []
        if_grupos = []
        grupo_atual = []

        for numero in slots:
            if not grupo_atual or numero == grupo_atual[-1] + 1:
                grupo_atual.append(numero)
            else:
                grupos.append(grupo_atual)
                if_grupos.append({"inicio": grupo_atual[0], "fim": grupo_atual[-1]})
                grupo_atual = [numero]

        if grupo_atual:
            grupos.append(grupo_atual)
            if_grupos.append({"inicio": grupo_atual[0], "fim": grupo_atual[-1]})

        return grupos, if_grupos

    def distance(self, path):
        return sum(self.topology[path[i]][path[i + 1]]['weight'] for i in range(len(path) - 1))

    def interrupt_simulation(self, interruption_point):
        while True:
            if self.env.now >= interruption_point:
                self.timeSimFim = self.env.now
                self.Simfim = True
                self.action.interrupt()
                break
            yield self.env.timeout(1)

    def desalocate(self, count, path, spectro, holding_time):
        try:
            yield self.env.timeout(holding_time)
            self.release_spectrum(path, spectro)
            self.ativo[count] = 0
            self.update_desalocate_req(count, holding_time)
        except simpy.Interrupt:
            self.release_spectrum(path, spectro)
            self.update_desalocate_req(count, holding_time)

    def release_spectrum(self, path, spectro):
        for i in range(len(path) - 1):
            for slot in range(spectro[0], spectro[1] + 1):
                self.topology[path[i]][path[i + 1]]['capacity'][slot] = 0

    def update_desalocate_req(self, count, holding_time):
        if count not in self.desalocateReq1:
            self.sum_time_up += self.env.now - self.req[count]['tempo_criacao']
            self.desalocateReq1.append(count)
        elif count not in self.desalocateReq2:
            self.sum_time_up += self.env.now - self.req[count]['tempo_criacao']
            self.desalocateReq2.append(count)

    def allocate_spectrum(self, count, inicio, fim, path):
        for i in range(len(path) - 1):
            for slot in range(inicio, fim + 1):
                self.topology[path[i]][path[i + 1]]['capacity'][slot] = count

    def path_is_able(self, nslots, path):
        cont = 0

        for slot in range(len(self.topology[path[0]][path[1]]['capacity'])):
            if self.topology[path[0]][path[1]]['capacity'][slot] == 0:
                if all(self.topology[path[ind]][path[ind + 1]]['capacity'][slot] == 0 for ind in range(len(path) - 1)):
                    cont += 1
                    if cont == 1:
                        i = slot
                    if cont > nslots:
                        return [True, i, slot]
            else:
                cont = 0

        return [False, 0, 0]

    def reroteamento(self, count, path, spectro, holding_time, src, dst, bandwidth, class_type):
        if count not in self.desalocateReqRerr:
            self.contador.afetadasF += 1
            self.sum_ht += holding_time

        self.afetadas_pr.append(count)

        if self.is_blocked(src, dst):
            self.block_reroute(count, class_type, bandwidth)
        else:
            new_paths = self.k_paths[src, dst]
            capacity, datapaths = self.calculate_capacity(new_paths, bandwidth)

            if capacity >= bandwidth:
                self.allocate_reroute(count, class_type, bandwidth, holding_time, datapaths)
            else:
                self.block_reroute(count, class_type, bandwidth)

    def block_reroute(self, count, class_type, bandwidth):
        self.contador.NumReqBlocked += 1
        self.Vet_NumReqBlocked2x.append(count)
        self.contador.Bloqueio_rerroteamento_cos_pr(class_type)
        self.contador.Bloqueio_rerroteamento_banda_pr(bandwidth)
        self.contador.bloqueio_rerroteamento_pr += 1
        self.contador.bloqueio_rerroteamento_pr_pr += 1
        self.rr_nao_restauradas_pr.append(count)
        self.nao_restauradas_pr.append(count)

    def allocate_reroute(self, count, class_type, bandwidth, holding_time, datapaths):
        cont_bandwidth = bandwidth

        for path_data in datapaths:
            for paths_able in path_data["inslotsfree_matrix"]:
                inicio, fim = paths_able
                transporte = path_data["fatormodulation"] * (fim - inicio + 1)
                dados_sol = [path_data["path"], inicio, fim]

                if transporte > cont_bandwidth:
                    dados_sol[2] = inicio + math.ceil(Modulation(path_data["distance"], cont_bandwidth)) - 1

                cont_bandwidth -= transporte

                if count not in self.desalocateReqRerr:
                    self.desalocateReqRerr.append(count)
                    self.contador.total_req_restauradas += 1
                    self.contador.restauradasF += 1

                self.allocate_spectrum(count, dados_sol[1], dados_sol[2], dados_sol[0])
                new_spectro = [dados_sol[1], dados_sol[2]]
                self.env.process(self.desalocate(count, dados_sol[0], new_spectro, holding_time))
                self.req.append(self.create_request_entry(count, class_type, path_data["num_slots"], dados_sol[0], new_spectro, holding_time, path_data["distance"], bandwidth, False))
                self.ativo[count] = 1
                self.Numsaltos += len(dados_sol[0])
                self.contador.Qtd_sol_Numsaltos += 1

                if cont_bandwidth == 0:
                    break
            if cont_bandwidth == 0:
                break

        self.contador.total_req_restauradas_pr_pr += 1

    def quem_falhou_link(self, pontaa, pontab):
        ativo2 = [i for i in self.ativo if self.ativo[i] == 1]
        return [entrada for entrada in self.req if entrada["num"] in ativo2 and 
                (any(entrada["path"][i] == pontaa and entrada["path"][i + 1] == pontab for i in range(len(entrada["path"]) - 1)) or
                any(entrada["path"][i] == pontab and entrada["path"][i + 1] == pontaa for i in range(len(entrada["path"]) - 1)))]

# Define the classes `Contador`, `FatorModulation`, `Modulation`, `k_shortest_paths` as necessary
