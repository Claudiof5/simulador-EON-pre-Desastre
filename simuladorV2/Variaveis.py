
#Quanto a simulação
REQUISICOES_POR_SEGUNDO :float = 75
NUMERO_DE_REQUISICOES   :int   = 150000
NUMERO_DE_ISPS          :int   = 5

#Quanto as requisicoes
BANDWIDTH    :list[int]   = [100, 150, 200, 250, 300, 350, 400]
CLASS_TYPE   :list[float] = [1, 2, 3]
CLASS_WEIGHT :list[float] = [0.15, 0.25, 0.60]
HOLDING_TIME :float       = 1

REQUISITADO_DA_REDE_POR_SEGUNDO :float = (sum(BANDWIDTH)/len(BANDWIDTH))*REQUISICOES_POR_SEGUNDO

#Quanto aos datacenters
THROUGHPUT                   :float = REQUISITADO_DA_REDE_POR_SEGUNDO * 0.025
VARIANCIA_THROUGPUT          :float = THROUGHPUT*0.1
TEMPO_DE_REACAO              :float = 600
VARIANCIA_TEMPO_DE_REACAO    :float = 90
TAMANHO_DATACENTER           :float = THROUGHPUT*300
VARIANCIA_TAMANHO_DATACENTER :float = TAMANHO_DATACENTER*0.1


#Quando a topologia
NUMERO_DE_SLOTS    :int   = 200
NUMERO_DE_CAMINHOS :int   = 10
SLOT_SIZE          :float = 12.5
