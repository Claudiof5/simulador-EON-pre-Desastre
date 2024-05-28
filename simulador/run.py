from VARIAVEIS import *
from EON_SIM import Simulador
import simpy
from random import *
import numpy as np
import networkx as nx


def CalculaIntervalo(amostra):
	# calcula média e intervalo de confiança de uma amostra (t de Student) 95%. 
	media = np.mean(amostra)
	desvio = np.std(amostra, ddof=1)
	intervalo = (desvio/len(amostra))*1.833
	return [media,intervalo]


topologia = TOPOLOGY
#abre aquivos
arquivo1  = open('out/'+topologia+'/bloqueio'+'.dat', 'w') # bloqueio = nao restauradas
arquivo2  = open('out/'+topologia+'/bloqueio_100'+'.dat', 'w')
arquivo3  = open('out/'+topologia+'/bloqueio_150'+'.dat', 'w')
arquivo4  = open('out/'+topologia+'/bloqueio_200'+'.dat', 'w')
arquivo5  = open('out/'+topologia+'/bloqueio_250'+'.dat', 'w')
arquivo6  = open('out/'+topologia+'/bloqueio_300'+'.dat', 'w')
arquivo7  = open('out/'+topologia+'/bloqueio_350'+'.dat', 'w')
arquivo8  = open('out/'+topologia+'/bloqueio_400'+'.dat', 'w')
arquivo9  = open('out/'+topologia+'/bloqueio_classe1'+'.dat', 'w')
arquivo10  = open('out/'+topologia+'/bloqueio_classe2'+'.dat', 'w')
arquivo11  = open('out/'+topologia+'/bloqueio_classe3'+'.dat', 'w')
arquivo12  = open('out/'+topologia+'/bloqueio_banda'+'.dat', 'w')
arquivo13  = open('out/'+topologia+'/restorability'+'.dat', 'w')
arquivo14  = open('out/'+topologia+'/availability'+'.dat', 'w')
arquivo15  = open('out/'+topologia+'/afetadas'+'.dat', 'w')
arquivo16  = open('out/'+topologia+'/re_afetadas'+'.dat', 'w')
arquivo17  = open('out/'+topologia+'/saltos'+'.dat', 'w')



topology = nx.read_weighted_edgelist('topology/' + TOPOLOGY, nodetype=int)

for e in range(ERLANG_MIN, ERLANG_MAX+1, ERLANG_INC):

	Bloqueio = []
	interrupcoes_serv = []
	Bloqueio_10 = []
	Bloqueio_20 = []
	Bloqueio_40 = []
	Bloqueio_80 = []
	Bloqueio_160 = []
	Bloqueio_200 = []
	Bloqueio_400 = []
	Bloqueio_classe1 = []
	Bloqueio_classe2 = []
	Bloqueio_classe3 = []
	Bloqueio_banda = []
	Restorability = []
	Availability = []
	afetadas = []
	afetadas2x = []
	saltos = []




	for rep in range(REP):		
		#zera os slots
		for u, v in list(topology.edges):
			topology[u][v]['capacity'] = [0] * SLOTS
			topology[u][v]['failed'] = False
		
		rate = e / HOLDING_TIME
		seed(RANDOM_SEED[rep])

		# Crie o ambiente SimPy
		env = simpy.Environment()
		simulador = Simulador(env, topology)
		# Adicione o processo de geração de requisições ao ambiente
		env.process(simulador.Run(rate))
		

		# Inicie a simulação
		env.run(until=MAX_TIME)

		
	
		req_accepts = simulador.req_accepts
		ativo = simulador.ativo
		k_paths = simulador.k_paths
		LINK_POINTSF = simulador.LINK_POINTSF
		NODE_POINTSF = simulador.NODE_POINTSF
		Simfim = simulador.Simfim
		desalocateReq1 = simulador.desalocateReq1
		desalocateReq2 = simulador.desalocateReq2
		desalocateReqRerr = simulador.desalocateReqRerr
		desalocateReqRerr2 = simulador.desalocateReqRerr2
		Vet_NumReqBlocked2x = simulador.Vet_NumReqBlocked2x

		NumReqBlocked = simulador.NumReqBlocked
		cont_req = simulador.cont_req
		NumReq_100 = simulador.contador.NumReq_100
		NumReq_150 = simulador.contador.NumReq_150
		NumReq_200 = simulador.contador.NumReq_200
		NumReq_250 = simulador.contador.NumReq_250
		NumReq_300 = simulador.contador.NumReq_300
		NumReq_350 = simulador.contador.NumReq_350
		NumReq_400 = simulador.contador.NumReq_400
		NumReq_classe1 = simulador.contador.NumReq_classe1
		NumReq_classe2 = simulador.contador.NumReq_classe2
		NumReq_classe3 = simulador.contador.NumReq_classe3
		NumReqBlocked_100 = simulador.contador.NumReqBlocked_100
		NumReqBlocked_150 = simulador.contador.NumReqBlocked_150
		NumReqBlocked_200 = simulador.contador.NumReqBlocked_200
		NumReqBlocked_250 = simulador.contador.NumReqBlocked_250
		NumReqBlocked_300 = simulador.contador.NumReqBlocked_300
		NumReqBlocked_350 = simulador.contador.NumReqBlocked_350
		NumReqBlocked_400 = simulador.contador.NumReqBlocked_400
		NumReqBlocked_classe1 = simulador.contador.NumReqBlocked_classe1
		NumReqBlocked_classe2 = simulador.contador.NumReqBlocked_classe2
		NumReqBlocked_classe3 = simulador.contador.NumReqBlocked_classe3
		# NOVAS
		bloqueio_rerroteamento_pr = simulador.bloqueio_rerroteamento_pr
		bloqueio_rerroteamento_cos1_pr = simulador.contador.bloqueio_rerroteamento_cos1_pr
		bloqueio_rerroteamento_cos2_pr = simulador.contador.bloqueio_rerroteamento_cos2_pr
		bloqueio_rerroteamento_cos3_pr = simulador.contador.bloqueio_rerroteamento_cos3_pr
		bloqueio_rerroteamento_100_pr = simulador.contador.bloqueio_rerroteamento_100_pr
		bloqueio_rerroteamento_150_pr = simulador.contador.bloqueio_rerroteamento_150_pr
		bloqueio_rerroteamento_200_pr = simulador.contador.bloqueio_rerroteamento_200_pr
		bloqueio_rerroteamento_250_pr = simulador.contador.bloqueio_rerroteamento_250_pr
		bloqueio_rerroteamento_300_pr = simulador.contador.bloqueio_rerroteamento_300_pr
		bloqueio_rerroteamento_350_pr = simulador.contador.bloqueio_rerroteamento_350_pr
		bloqueio_rerroteamento_400_pr = simulador.contador.bloqueio_rerroteamento_400_pr
		restauradasF = simulador.restauradasF
		afetadasF = simulador.afetadasF
		sum_time_up = simulador.sum_time_up
		sum_ht = simulador.sum_ht
		NumReqBlocked2x = simulador.NumReqBlocked2x
		Numsaltos = simulador.Numsaltos
		Qtd_sol_Numsaltos = simulador.Qtd_sol_Numsaltos

		print("---"*10, end="\n\n\n")
		simulador.print_attributes()
		print("---"*10, end="\n\n\n")
		#report final 	
		print("Erlang", e, "Simulacao...", rep)
		print("bloqueadas", NumReqBlocked, "de", NUM_OF_REQUESTS)



		Bloqueio_10.append(NumReqBlocked_100/float(NumReq_100))
		Bloqueio_20.append(NumReqBlocked_150/float(NumReq_150))
		Bloqueio_40.append(NumReqBlocked_200/float(NumReq_200))
		Bloqueio_80.append(NumReqBlocked_250/float(NumReq_250))
		Bloqueio_160.append(NumReqBlocked_300/float(NumReq_300))
		Bloqueio_200.append(NumReqBlocked_350/float(NumReq_350))
		Bloqueio_400.append(NumReqBlocked_400/float(NumReq_400))
		Bloqueio_classe1.append(NumReqBlocked_classe1/float(NumReq_classe1))
		Bloqueio_classe2.append(NumReqBlocked_classe2/float(NumReq_classe2))
		Bloqueio_classe3.append(NumReqBlocked_classe3/float(NumReq_classe3))
		BD_solicitada = ((NumReq_100)*100+(NumReq_150)*150+(NumReq_200)*200+(NumReq_250)*250+(NumReq_300)*300+(NumReq_350)*350+(NumReq_400)*400)
		BD_bloqueada = ((NumReqBlocked_100)*100+(NumReqBlocked_150)*150+(NumReqBlocked_200)*200+(NumReqBlocked_250)*250+(NumReqBlocked_300)*300+(NumReqBlocked_350)*350+(NumReqBlocked_400)*400)
		Bloqueio_banda.append(BD_bloqueada/float(BD_solicitada))


 
		if restauradasF == 0 or afetadasF == 0:
			Restorability.append(0)
		else:
			Restorability.append(restauradasF/afetadasF)
		Availability.append(sum_time_up / sum_ht ) 
		afetadas.append(afetadasF)

		Bloqueio.append(NumReqBlocked / float(NUM_OF_REQUESTS)) 
		afetadas.append(NumReqBlocked)
		saltos.append(Numsaltos/Qtd_sol_Numsaltos)

		contagem = {}
		for numero in Vet_NumReqBlocked2x:
			if numero in contagem:
				contagem[numero] += 1
			else:
				contagem[numero] = 1
		NumReqBlocked2x = sum(contador > 1 for contador in contagem.values())

		afetadas2x.append(NumReqBlocked2x)
 
    
    #calcula intervalos
	intervalo_10 = CalculaIntervalo(Bloqueio_10)
	intervalo_20 = CalculaIntervalo(Bloqueio_20)
	intervalo_40 = CalculaIntervalo(Bloqueio_40)
	intervalo_80 = CalculaIntervalo(Bloqueio_80)
	intervalo_160 = CalculaIntervalo(Bloqueio_160)
	intervalo_200 = CalculaIntervalo(Bloqueio_200)
	intervalo_400 = CalculaIntervalo(Bloqueio_400)
	intervalo_classe1 = CalculaIntervalo(Bloqueio_classe1)
	intervalo_classe2 = CalculaIntervalo(Bloqueio_classe2)
	intervalo_classe3 = CalculaIntervalo(Bloqueio_classe3)
	intervalo_bloqueio_banda = CalculaIntervalo(Bloqueio_banda)
	intervalo_restorability = CalculaIntervalo(Restorability)
	intervalo_availability = CalculaIntervalo(Availability)

	intervalo = CalculaIntervalo(Bloqueio)
	intervalo_afetadas = CalculaIntervalo(afetadas)
	intervalo_afetadas2x = CalculaIntervalo(afetadas2x)
	intervalo_saltos = CalculaIntervalo(saltos)
	
    
    #escreve arquivos
	arquivo1.write(str(e))
	arquivo1.write("\t")
	arquivo1.write(str(intervalo[0]))
	arquivo1.write("\t")
	arquivo1.write(str(intervalo[0]-intervalo[1]))
	arquivo1.write("\t")
	arquivo1.write(str(intervalo[0]+intervalo[1]))
	arquivo1.write("\n")

	arquivo2.write(str(e))
	arquivo2.write("\t")
	arquivo2.write(str(intervalo_10[0]))
	arquivo2.write("\t")
	arquivo2.write(str(intervalo_10[0]-intervalo_10[1]))
	arquivo2.write("\t")
	arquivo2.write(str(intervalo_10[0]+intervalo_10[1]))
	arquivo2.write("\n")

	arquivo3.write(str(e))
	arquivo3.write("\t")
	arquivo3.write(str(intervalo_20[0]))
	arquivo3.write("\t")
	arquivo3.write(str(intervalo_20[0]-intervalo_20[1]))
	arquivo3.write("\t")
	arquivo3.write(str(intervalo_20[0]+intervalo_20[1]))
	arquivo3.write("\n")

	arquivo4.write(str(e))
	arquivo4.write("\t")
	arquivo4.write(str(intervalo_40[0]))
	arquivo4.write("\t")
	arquivo4.write(str(intervalo_40[0]-intervalo_40[1]))
	arquivo4.write("\t")
	arquivo4.write(str(intervalo_40[0]+intervalo_40[1]))
	arquivo4.write("\n")

	arquivo5.write(str(e))
	arquivo5.write("\t")
	arquivo5.write(str(intervalo_80[0]))
	arquivo5.write("\t")
	arquivo5.write(str(intervalo_80[0]-intervalo_80[1]))
	arquivo5.write("\t")
	arquivo5.write(str(intervalo_80[0]+intervalo_80[1]))
	arquivo5.write("\n")

	arquivo6.write(str(e))
	arquivo6.write("\t")
	arquivo6.write(str(intervalo_160[0]))
	arquivo6.write("\t")
	arquivo6.write(str(intervalo_160[0]-intervalo_160[1]))
	arquivo6.write("\t")
	arquivo6.write(str(intervalo_160[0]+intervalo_160[1]))
	arquivo6.write("\n")

	arquivo7.write(str(e))
	arquivo7.write("\t")
	arquivo7.write(str(intervalo_200[0]))
	arquivo7.write("\t")
	arquivo7.write(str(intervalo_200[0]-intervalo_200[1]))
	arquivo7.write("\t")
	arquivo7.write(str(intervalo_200[0]+intervalo_200[1]))
	arquivo7.write("\n")

	arquivo8.write(str(e))
	arquivo8.write("\t")
	arquivo8.write(str(intervalo_400[0]))
	arquivo8.write("\t")
	arquivo8.write(str(intervalo_400[0]-intervalo_400[1]))
	arquivo8.write("\t")
	arquivo8.write(str(intervalo_400[0]+intervalo_400[1]))
	arquivo8.write("\n")

	arquivo9.write(str(e))
	arquivo9.write("\t")
	arquivo9.write(str(intervalo_classe1[0]))
	arquivo9.write("\t")
	arquivo9.write(str(intervalo_classe1[0]-intervalo_classe1[1]))
	arquivo9.write("\t")
	arquivo9.write(str(intervalo_classe1[0]+intervalo_classe1[1]))
	arquivo9.write("\n")

	arquivo10.write(str(e))
	arquivo10.write("\t")
	arquivo10.write(str(intervalo_classe2[0]))
	arquivo10.write("\t")
	arquivo10.write(str(intervalo_classe2[0]-intervalo_classe2[1]))
	arquivo10.write("\t")
	arquivo10.write(str(intervalo_classe2[0]+intervalo_classe2[1]))
	arquivo10.write("\n")

	arquivo11.write(str(e))
	arquivo11.write("\t")
	arquivo11.write(str(intervalo_classe3[0]))
	arquivo11.write("\t")
	arquivo11.write(str(intervalo_classe3[0]-intervalo_classe3[1]))
	arquivo11.write("\t")
	arquivo11.write(str(intervalo_classe3[0]+intervalo_classe3[1]))
	arquivo11.write("\n")

	arquivo12.write(str(e))
	arquivo12.write("\t")
	arquivo12.write(str(intervalo_bloqueio_banda[0]))
	arquivo12.write("\t")
	arquivo12.write(str(intervalo_bloqueio_banda[0]-intervalo_bloqueio_banda[1]))
	arquivo12.write("\t")
	arquivo12.write(str(intervalo_bloqueio_banda[0]+intervalo_bloqueio_banda[1]))
	arquivo12.write("\n")


	#restorability
	arquivo13.write(str(e))
	arquivo13.write("\t")
	arquivo13.write(str(intervalo_restorability[0]))
	arquivo13.write("\t")
	arquivo13.write(str(intervalo_restorability[0]-intervalo_restorability[1]))
	arquivo13.write("\t")
	arquivo13.write(str(intervalo_restorability[0]+intervalo_restorability[1]))
	arquivo13.write("\n")

	#availability
	arquivo14.write(str(e))
	arquivo14.write("\t")
	arquivo14.write(str(intervalo_availability[0]))
	arquivo14.write("\t")
	arquivo14.write(str(intervalo_availability[0]-intervalo_availability[1]))
	arquivo14.write("\t")
	arquivo14.write(str(intervalo_availability[0]+intervalo_availability[1]))
	arquivo14.write("\n")

	#afetadas
	arquivo15.write(str(e))
	arquivo15.write("\t")
	arquivo15.write(str(intervalo_afetadas[0]))
	arquivo15.write("\t")
	arquivo15.write(str(intervalo_afetadas[0]-intervalo_afetadas[1]))
	arquivo15.write("\t")
	arquivo15.write(str(intervalo_afetadas[0]+intervalo_afetadas[1]))
	arquivo15.write("\n")

	#afetadas
	arquivo16.write(str(e))
	arquivo16.write("\t")
	arquivo16.write(str(intervalo_afetadas2x[0]))
	arquivo16.write("\t")
	arquivo16.write(str(intervalo_afetadas2x[0]-intervalo_afetadas2x[1]))
	arquivo16.write("\t")
	arquivo16.write(str(intervalo_afetadas2x[0]+intervalo_afetadas2x[1]))
	arquivo16.write("\n")

	#saltos
	arquivo17.write(str(e))
	arquivo17.write("\t")
	arquivo17.write(str(intervalo_saltos[0]))
	arquivo17.write("\t")
	arquivo17.write(str(intervalo_saltos[0]-intervalo_saltos[1]))
	arquivo17.write("\t")
	arquivo17.write(str(intervalo_saltos[0]+intervalo_saltos[1]))
	arquivo17.write("\n")

#fecha arquivos
arquivo1.close()
arquivo2.close()
arquivo3.close()
arquivo4.close()
arquivo5.close()
arquivo6.close()
arquivo7.close()
arquivo8.close()
arquivo10.close()
arquivo11.close()
arquivo12.close()
arquivo13.close()
arquivo14.close()
arquivo15.close()
arquivo16.close()
arquivo17.close()
