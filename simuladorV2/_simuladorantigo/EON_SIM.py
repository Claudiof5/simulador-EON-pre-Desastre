#!/usr/bin/env python
# -*- coding: utf-8 -*-



import simpy
import numpy as np
import networkx as nx
import math
from random import *
from VARIAVEIS import *
from utils import k_shortest_paths, Modulation, FatorModulation
from Contador import Contador

desastre_padrao = {"duration":DURACAO_DESASTRE, "nodes":NODE_POINTS, "links":LINK_POINTS, "start":TEMPO_INICIO_DESASTRE}

class Simulador:
		
	def __init__(self, env :simpy.Environment, topology, rate, ISP_dict :dict, disaster = desastre_padrao):
	
		self.random = Random()
		self.nodes = list(topology.nodes())
		self.env :simpy.Environment = env
		self.topology :nx.Graph = topology

		#mover para inicialização da classe Topologia
		for u, v in list(self.topology.edges):				 #seta os slots em cada LP(as arestas da rede) como disponiveis 
			self.topology[u][v]['capacity'] = [0] * SLOTS

		self.contador:Contador = Contador()
		self.ISP_dict = ISP_dict
		self.nodes_and_edges_to_ISP_dict = self.node_and_link_to_ISP()
		self.disaster = disaster

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
		#NOVAS
		self.mensagem_impressa = False
		# variaveis pr 
		self.afetadas_pr = []
		self.nao_restauradas_pr = []
		self.rr_nao_restauradas_pr = []

		self.action = env.process(self.Run(rate))
		self.timeSimFim = None
	
	def timer(self):
		while True:
			if self.env.now % 10 == 0:
				print(".", end="")
			if self.env.now % 100 == 0:
				print("\n")
				print(f"{list(self.ativo.keys())[-1000:][::-1]}")
				print("\n")

			yield self.env.timeout(1)

	def Run(self, rate):

		try:
			#adicionar em classe Topologia
			#pre-processamento dos caminhos mais curtos
			for i in list(self.topology.nodes()):
				for j in list(self.topology.nodes()):
					if i!= j:
						self.k_paths[i,j] = k_shortest_paths(self.topology, i, j, N_PATH, weight='weight')
			
			
			#self.env.process(self.GerarFalhas())
			self.env.process(self.timer())

			for count in range(1, NUM_OF_REQUESTS + 1):

				yield self.env.timeout(self.random.expovariate(rate))
				#escolhe tempo de espera aleatorio, destino e origem, tipo de pacote, e bandwidth do pacote
				class_type = np.random.choice(CLASS_TYPE, p=CLASS_WEIGHT)
				src, dst = np.random.sample(self.nodes, 2)
				src_ISP = self.random.choice( self.nodes_and_edges_to_ISP_dict["nodes"][src])
				dst_ISP = self.random.choice( self.nodes_and_edges_to_ISP_dict["nodes"][dst])
				
				bandwidth = self.random.choice(BANDWIDTH)
				holding_time = self.random.expovariate(HOLDING_TIME)
				self.sum_ht += holding_time

				self.contador.conta_requisicao_banda(bandwidth)
				self.contador.conta_requisicao_classe(class_type)
	
				#se o destino for um node adjacente a origem, e esse node estiver afetado bloquear requisição e computar bloqueio
				if self.topology.has_edge(src, dst) and 'failed' in self.topology[src][dst] and self.topology[src][dst]['failed'] == True:
					self.contador.total_req_afetadas_od += 1
					self.contador.NumReqBlocked +=1
					self.Vet_NumReqBlocked2x.append(count)
					self.contador.Bloqueio_falha_od_cos(class_type)
					self.contador.Bloqueio_falha_od_banda(bandwidth)

				else:
					paths = self.k_paths[src,dst]
					flag = 0
					

					capacity = 0
					Datapaths = []
					found = False
					#agrega em uma lista Datapaths de informações sobre todos os caminhos
					for i in range(N_PATH):
						distance = int(self.Distance(paths[i]))  # Calcule a distância
						
						Fatormodulation = FatorModulation(distance) #calcula modulação

						FreeSlots, FreeSlotsMatrix, INSlotsfreeMatrix = self.MaxFlow(paths[i]) #retorna uma lista dos slots disponiveis, os valores de slots continuos, e os inicios e fins dos slots continuos
						FreeSlotsSun = len(FreeSlots) 
						capacityCalc = Fatormodulation * FreeSlotsSun
						capacity += capacityCalc
						num_slots = int(math.ceil(Modulation(distance, bandwidth))) #numero de slots nescessarios para o caminho dado a modulação
						Datapaths.append([paths[i], distance, Fatormodulation, FreeSlotsSun , capacityCalc, FreeSlotsMatrix, FreeSlots, INSlotsfreeMatrix , num_slots ])
					
					Contbandwidth = bandwidth
					ConjSlots = 0
					
					CAMINHOINDEX = 0
					DISTANCIAINDEX = 1
					FATORMODULACAOINDEX = 2
					LISTAIFINDEX = 7

					if capacity >= bandwidth:
						
						for sublista in Datapaths:
							listaDeIniciosEFinais = sublista[LISTAIFINDEX]
							fatorModulacao = sublista[FATORMODULACAOINDEX]
							caminho = sublista[CAMINHOINDEX]
							distancia = sublista[DISTANCIAINDEX]
							
							for pathsAble in listaDeIniciosEFinais:
								inicioSlotContinuo = pathsAble[0]
								finalSlotContinuo = pathsAble[1]
								
								tamanhoDoSlotConinuo = finalSlotContinuo-inicioSlotContinuo+1
								Transporte = fatorModulacao * tamanhoDoSlotConinuo #calcula o throuput possivel no caminho

								DadosSOL = {"caminho":caminho, "inicio":inicioSlotContinuo, "fim":finalSlotContinuo}

								#se mais slots que o preciso existam 
								if Transporte > Contbandwidth:
									Transporte = Contbandwidth
									DadosSOL = {"caminho":caminho, "inicio":inicioSlotContinuo, "fim": inicioSlotContinuo + int(math.ceil(Modulation(distancia, Contbandwidth)))-1}
								Contbandwidth -= Transporte

								self.contador.cont_req += 1
								
								self.FirstFit(count, DadosSOL["inicio"], DadosSOL["fim"], DadosSOL["caminho"])
								spectro = [DadosSOL["inicio"], DadosSOL["fim"]]

								# Tabela de requisições aceitas com n° da req, classe ,num_slots, path, posição no spectro, inicio ,holding_time, frac_ht, hops, distancia_km, bandwidth
								processo = self.env.process(self.Desalocate(count,DadosSOL["caminho"],spectro,holding_time, self.env.now))

								self.req[count] = {"num": count, "class":class_type, "num_slots":num_slots, "path":DadosSOL["caminho"],"path_length": len(DadosSOL["caminho"]),"spectro":spectro,
								  "tempo_criacao":self.env.now , "tempo_desalocacao":self.env.now  +holding_time, "distacia":distancia, "bandwidth":bandwidth, "blocked":False, "source_ISP":src_ISP, "destination_ISP":dst_ISP}
								self.ativo[count] = 1

								flag = 1
								ConjSlots += 1
								self.Numsaltos +=  len(DadosSOL["caminho"])
								self.contador.Qtd_sol_Numsaltos += 1 

								if Contbandwidth == 0:
									found = True
									break
							if found:
								break

					if flag == 0:
							self.req[count] = {"num": count, "class":class_type, "num_slots":num_slots, "path":None,"path_length": None,"spectro":None,
								  "tempo_criacao":self.env.now , "tempo_desalocacao":None, "distacia":None, "bandwidth":bandwidth, "blocked":True, "source_ISP":src_ISP, "destination_ISP":dst_ISP}
							self.contador.NumReqBlocked +=1
							self.Vet_NumReqBlocked2x.append(count)
							self.contador.conta_bloqueio_requisicao_banda(bandwidth)
							self.contador.conta_bloqueio_requisicao_classe(class_type)

			print( f"Simulation end at {self.env.now}")
			self.timeSimFim = self.env.now
			self.Simfim =  True

		except simpy.Interrupt:
			print("Simulation interrupted at time", self.env.now)

	
	def node_and_link_to_ISP( self):

		node_dict = {node:[] for node in self.topology.nodes()}
		edge_dict = {edges:[] for edges in self.topology.edges()}

		print(node_dict)
		print(edge_dict.keys())
		for key in self.ISP_dict.keys():

			for node in self.ISP_dict[key]["nodes"]:
				node_dict[node].append(key)

			for edge in self.ISP_dict[key]["edges"]:
				if edge in edge_dict.keys():
					edge_dict[edge].append(key)
				elif (edge[1], edge[0]) in edge_dict.keys():
					edge_dict[(edge[1], edge[0])].append(key)

		return { "nodes":node_dict, "edges":edge_dict }
	
	

	def MaxFlow(self, path):
		
		current_consecutive = []  # Lista temporária para armazenar o conjunto atual de slots consecutivos

		#itera sobre os slots e adiciona esse a current consecutive caso os mesmo estejam disponiveis por toda 
		for slot in range(len(self.topology[path[0]][path[1]]['capacity'])):
			if self.topology[path[0]][path[1]]['capacity'][slot] == 0:
				k = 0
				for ind in range(len(path) - 1):
					if self.topology[path[ind]][path[ind + 1]]['capacity'][slot] == 0:
						k += 1
				if k == len(path) - 1:
					current_consecutive.append(slot)
		grupos = []
		IFgrupos = []
		grupo_atual = []

		for numero in current_consecutive:
			# Se o grupo atual estiver vazio ou se o número for igual ao último número + 1, adicione-o ao grupo atual.
			if not grupo_atual or numero == grupo_atual[-1] + 1:
				grupo_atual.append(numero)
			else:
				# Caso contrário, termine o grupo atual e comece um novo grupo.
				grupos.append(grupo_atual)
				IFgrupos.append([grupo_atual[0], grupo_atual[-1]])
				grupo_atual = [numero]

		# Certifique-se de adicionar o último grupo à lista de grupos.
		if grupo_atual:
			grupos.append(grupo_atual)
			IFgrupos.append([grupo_atual[0], grupo_atual[-1]])

		return current_consecutive, grupos, IFgrupos

	def Distance(self, path):
		soma = 0
		for i in range(0, (len(path)-1)):
			soma += self.topology[path[i]][path[i+1]]['weight']
		return (soma)

	def InterruptSimulation(self, interruption_point):
		while True:
			if self.env.now >= interruption_point:
				self.timeSimFim = self.env.now
				self.Simfim = True
				self.action.interrupt()
				break
			yield self.env.timeout(1)

	#desaloca espectro ao finalizar 
	def Desalocate(self, count, path, spectro, holding_time, inicio):
		#self.sum_ht += holding_time
		try:
			yield self.env.timeout(holding_time)
			for i in range(0, (len(path)-1)):
				#print("Antes ===",self.topology[path[i]][path[i+1]]['capacity'])
				for slot in range(spectro[0],spectro[1]+1):
					self.topology[path[i]][path[i+1]]['capacity'][slot] = 0

			self.ativo[count] = 0
			if count not in self.desalocateReq1:
				self.sum_time_up += (self.env.now - inicio)
				self.desalocateReq1.append(count)
				#print("1>>>>>>", self.env.now , count, inicio, self.sum_time_up, holding_time)
		except simpy.Interrupt as interrupt:
			for i in range(0, (len(path)-1)):
				for slot in range(spectro[0],spectro[1]+1):
					self.topology[path[i]][path[i+1]]['capacity'][slot] = 0
			if count not in self.desalocateReq2:
				self.sum_time_up += (self.env.now - inicio)
				self.desalocateReq2.append(count)
				#print("2>>>>>>", self.env.now , count, inicio, self.sum_time_up, holding_time)
			self.ativo[count] = 0
			#input()
			pass

	#Realiza a alocação de espectro utilizando First-fit
	def FirstFit(self, count, i, j, path):

		inicio = i 
		fim =j
		for i in range(0,len(path)-1):
			for slot in range(inicio,fim):
				self.topology[path[i]][path[i+1]]['capacity'][slot] = count
			self.topology[path[i]][path[i+1]]['capacity'][fim] = 'GB'

	# Verifica se o caminho escolhido possui espectro disponível para a demanda requisitada
	'''def PathIsAble(self, nslots, path):
		cont = 0
		t = 0
		for slot in range (0,len(self.topology[path[0]][path[1]]['capacity'])):
			if self.topology[path[0]][path[1]]['capacity'][slot] == 0:
				k = 0
				for ind in range(0,len(path)-1):
					if self.topology[path[ind]][path[ind+1]]['capacity'][slot] == 0:
						k += 1
				if k == len(path)-1:
					cont += 1
					if cont == 1:
						i = slot
					if cont > nslots:
						j = slot
						return [True,i,j]
					if slot == len(self.topology[path[0]][path[1]]['capacity'])-1:
							return [False,0,0]
				else:
					cont = 0
					if slot == len(self.topology[path[0]][path[1]]['capacity'])-1:
						return [False,0,0]
			else:
				cont = 0
				if slot == len(self.topology[path[0]][path[1]]['capacity'])-1:
					return [False,0,0]	

'''
		# Função para gerar falhas na rede
	

	def GenerateMigrationTrafic(self):

		databases_reaction_time = {}
		for key in self.ISP_dict.keys():
			databases_reaction_time[key] = self.ISP_dict[key]["reaction_time"] + self.disaster["start"]
		
		while True:

			for key in databases_reaction_time.keys():
				if self.env.now > databases_reaction_time[key]:
					self.StartISPMigration( key )
					del databases_reaction_time[key]

			if len(databases_reaction_time) == 0:
				break
			yield self.env.timeout(1)



	def GerarFalhas(self):
		while True:
			for link_point in self.disaster["links"]:
				if link_point not in self.LINK_POINTSF and self.env.now >= link_point[LPF_TIME_INDEX]+ TEMPO_INICIO_DESASTRE:
					self.FalhaNoLink(link_point[LPF_SRC_INDEX], link_point[LPF_DST_INDEX])
					self.LINK_POINTSF.append(link_point)
					print("falha ge2rada", link_point )

			for node_point in self.disaster["nodes"]:
				if node_point not in self.NODE_POINTSF and self.env.now >= node_point[NPF_TIME_INDEX]+ TEMPO_INICIO_DESASTRE:
					# Falha no nó node_point[LPF_SRC_INDEX]
					self.FalhaNoNo(node_point[NPF_NODE_INDEX])
					self.NODE_POINTSF.append(node_point)
					print("falha gerada", node_point )


			if self.env.now >= self.disaster["duration"]+self.disaster["start"]:
				for u, v in list(self.topology.edges):
					self.topology[u][v]['failed'] = False
				if not self.mensagem_impressa:
					print ("links reestabelecidos")

					self.mensagem_impressa = True
			# Verifique se todas as requisições foram concluídas
			if self.Simfim == True:
				break  # Encerra o loop se todas as requisições foram concluídas
			yield self.env.timeout(1)  # Verifica a cada unidade de tempo

	# Função para lidar com falhas em links
	def FalhaNoLink(self, node1, node2):
		# Verifique se o link entre node1 e node2 existe
		if self.topology.has_edge(node1, node2):
			# Marque o link como falho (você pode adicionar um atributo 'failed' ao link)
			self.topology[node1][node2]['failed'] = True
			#print("self.FalhaNoLink2")

			reqfalhou = []
			reqfalhou = self.Quem_falhou_link(node1, node2)

			# Chame Desalocate para liberar slots de espectro nos links afetados
			for i in range(len(reqfalhou)):
				print("FalhaNoLink")
				process = reqfalhou[i][11]
				process.interrupt()
				#self.sum_time_up += (self.env.now - reqfalhou[i][5])
				self.Desalocate(reqfalhou[i][0],reqfalhou[i][3],reqfalhou[i][4],reqfalhou[i][6], reqfalhou[i][5])
				# Implemente aqui a lógica para o self.reroteamento do tráfego afetado
				self.Reroteamento(reqfalhou[i][0], reqfalhou[i][3], reqfalhou[i][4], reqfalhou[i][6], reqfalhou[i][3][0], reqfalhou[i][3][-1], reqfalhou[i][10], reqfalhou[i][1])

			# Imprima uma mensagem para indicar que o link falhou
			print(f"Falha no link entre os nós {node1} e {node2}")

		else:
			# O link não existe, imprima uma mensagem de erro
			print(f"Erro: O link entre os nós {node1} e {node2} não existe na topologia.")

	# Função para lidar com falhas em nós
	def FalhaNoNo(self, node):

		# Verifique se o nó existe na topologia
		if node in self.topology.nodes:
			# Marque o nó como falho (você pode adicionar um atributo 'failed' ao nó)

			# Itere sobre todos os links conectados ao nó falho
			for neighbor in self.topology.neighbors(node):
				# Verifique se o link ainda existe e marque-o como falho
				if self.topology.has_edge(node, neighbor):
					self.topology[node][neighbor]['failed'] = True

					reqfalhou = []
					reqfalhou = self.Quem_falhou_link(node, neighbor)

					# Chame Desalocate para liberar slots de espectro nos links afetados
					for i in range(len(reqfalhou)):
						process = reqfalhou[i][11]
						process.interrupt()
						#self.sum_time_up += (self.env.now - reqfalhou[i][5])
						self.Desalocate(reqfalhou[i][0],reqfalhou[i][3],reqfalhou[i][4],reqfalhou[i][6],reqfalhou[i][5])
						# Implemente aqui a lógica para o self.reroteamento do tráfego afetado
						self.Reroteamento(reqfalhou[i][0], reqfalhou[i][3], reqfalhou[i][4], reqfalhou[i][6], reqfalhou[i][3][0], reqfalhou[i][3][-1], reqfalhou[i][10], reqfalhou[i][1])

					# Imprima uma mensagem para indicar que o link falhou
					print(f"Falha no link entre os nós {node} e {neighbor}")

			# Imprima uma mensagem para indicar que o nó falhou
			print(f"Falha no nó {node}")

		else:
			# O nó não existe, imprima uma mensagem de erro
			print(f"Erro: O nó {node} não existe na topologia.")

# Função para self.reroteamento após falha
	def Reroteamento(self, count, path, spectro, holding_time, src, dst, bandwidth, class_type):
		if count not in self.desalocateReqRerr:
			self.contador.afetadasF += 1
			self.sum_ht += holding_time
		
		self.afetadas_pr.append(count)
		
		if self.topology.has_edge(src, dst) and 'failed' in self.topology[src][dst] and self.topology[src][dst]['failed'] == True:
			self.cotnador.NumReqBlocked +=1
			self.Vet_NumReqBlocked2x.append(count)
			self.contador.Bloqueio_rerroteamento_cos_pr(class_type)
			self.contador.Bloqueio_rerroteamento_banda_pr(bandwidth)
			self.contador.bloqueio_rerroteamento_pr += 1
			#pass
		else:
			new_paths = self.k_paths[src,dst]
			capacity = 0
			Datapaths = []
			found = False
			for i in range(N_PATH):
				distance = int(self.Distance(new_paths[i]))  # Calcule a distância
				Fatormodulation = FatorModulation(distance)
				FreeSlots, FreeSlotsMatrix, INSlotsfreeMatrix = self.MaxFlow(new_paths[i])
				FreeSlotsSun = len(FreeSlots)
				capacityCalc = Fatormodulation * FreeSlotsSun
				capacity += capacityCalc
				num_slots = int(math.ceil(Modulation(distance, bandwidth)))
				Datapaths.append([new_paths[i], distance, Fatormodulation, FreeSlotsSun , capacityCalc, FreeSlotsMatrix, FreeSlots, INSlotsfreeMatrix , num_slots ])
			Contbandwidth = bandwidth
			ConjSlots = 0
			if capacity >= bandwidth:
				for sublista in Datapaths:
					coluna_7 = sublista[7]
					for pathsAble in coluna_7:
						Transporte = sublista[2] *(pathsAble[1]-pathsAble[0]+1)
						DadosSOL = [sublista[0], pathsAble [0],pathsAble[1]]
						if Transporte > Contbandwidth:
							Transporte = Contbandwidth
							DadosSOL = [sublista[0], pathsAble[0], pathsAble[0] + int(math.ceil(Modulation(sublista[1], Contbandwidth)))-1]
						Contbandwidth -= Transporte

						if count not in self.desalocateReqRerr:
							self.desalocateReqRerr.append(count)
							self.contador.total_req_restauradas += 1
							self.contador.restauradasF +=1
						self.FirstFit(count, DadosSOL[1], DadosSOL[2], DadosSOL[0])
						New_spectro = [DadosSOL[1], DadosSOL[2]]
						processo = self.env.process(self.Desalocate(count,DadosSOL[0],New_spectro,holding_time, self.env.now))
						# Tabela de requisições aceitas com n° da req, classe ,num_slots, path, posição no spectro, inicio ,holding_time, frac_ht, hops, distancia_km, bandwidth
						self.req.append([count, class_type, num_slots, DadosSOL[0], New_spectro, self.env.now , holding_time, 0, len(new_paths[i])-1, distance, bandwidth, processo])
						self.ativo[count] = 1
						self.Numsaltos +=  len(DadosSOL[0])
						self.contador.Qtd_sol_Numsaltos += 1 

						

						ConjSlots += 1
						if Contbandwidth == 0:
							found = True
							break
					if found:
						break
					
				self.contador.total_req_restauradas_pr_pr += 1
			else:
				self.contador.bloqueio_rerroteamento_pr += 1
				self.contador.Bloqueio_rerroteamento_cos_pr(class_type)
				self.contador.Bloqueio_rerroteamento_banda_pr(bandwidth)
				self.contador.NumReqBlocked +=1
				self.Vet_NumReqBlocked2x.append(count)
				self.contador.bloqueio_rerroteamento_pr_pr += 1
				self.rr_nao_restauradas_pr.append(count)
				self.nao_restauradas_pr.append(count)
				# Se nenhum novo caminho foi encontrado, a requisição é bloqueada

	def Quem_falhou_link(self, pontaa, pontab):
		ativo2 = []
		#print("self.Quem_falhou_link" , self.ativo)
		for i in range(len(self.ativo)):
			if i in self.ativo and self.ativo[i] == 1:
				ativo2.append(i)
		entradas_filtradas = [
		entrada for entrada in self.req
		if entrada[0] in ativo2 and (any(entrada[3][i] == pontaa and entrada[3][i + 1] == pontab for i in range(len(entrada[3]) - 1)) or any(entrada[3][i] == pontab and entrada[3][i + 1] == pontaa for i in range(len(entrada[3]) - 1)))
		]

		return entradas_filtradas

