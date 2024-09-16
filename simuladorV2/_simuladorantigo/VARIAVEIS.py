
#sementes random 
RANDOM_SEED = [50, 60, 70, 80, 90, 100, 110, 120, 130, 140]

#tempo maximo de simulacao
MAX_TIME = 3600  

#ERLANG_MIN = 300
ERLANG_MIN = 300

#ERLANG_MAX = 380
ERLANG_MAX = 380

#pabrao 20
ERLANG_INC = 80

#quantidade de repeticoes padrao 10
REP = 1

#numero de requisicoes padrao 100.000 100000
NUM_OF_REQUESTS = 36000

#tramanho das bandas >>>>>> MEXER NO CODIGO AO ALTERAR BANDAS >>>>
BANDWIDTH = [100, 150, 200, 250, 300, 350, 400]

#classes de trafego
CLASS_TYPE = [1, 2, 3]

#divisao do trafego por classes
CLASS_WEIGHT = [0.15, 0.25, 0.60]

#topologia
TOPOLOGY = 'usa'

##### aki aumenta o tarfego, reduzindo o tempo por requisicao ########
#tempo por requisicao padrao 1.0
HOLDING_TIME = 2


#quantidade slot Eon 400
SLOTS = 80

#tamanho do slot ghz
SLOT_SIZE = 12.5

#N_PATH 15
N_PATH = 10

#duracao do desastre
TEMPO_INICIO_DESASTRE = 600 #
DURACAO_DESASTRE = 600 #43200

#pontos de falha = pontoA, pontoB, tempo para falhar [[1,2,1], [1,4,2]]
LINK_POINTS = [[6,9,1],[9,11,3],[7,9,6],[9,12,6],[9,10,9],[6,7,9],[11,12,9]]
LPF_TIME_INDEX = 2
LPF_SRC_INDEX = 0
LPF_DST_INDEX = 1



#pontos de falha = no, tempo [[4,2], [2,5]]
NODE_POINTS = [[9,9]]
NPF_TIME_INDEX = 1
NPF_NODE_INDEX = 0