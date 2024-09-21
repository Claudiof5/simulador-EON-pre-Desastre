#Quanto as requisicoes
BANDWIDTH    :list[int]   = [100, 150, 200, 250, 300, 350, 400]
CLASS_TYPE   :list[float] = [1, 2, 3]
CLASS_WEIGHT :list[float] = [0.15, 0.25, 0.60]
HOLDING_TIME :float       = 1

#Quanto aos datacenters
THROUGHPUT                   :float = 250
VARIANCIA_THROUGPUT          :float = 25
TEMPO_DE_REACAO              :float = 600
VARIANCIA_TEMPO_DE_REACAO    :float = 90
TAMANHO_DATACENTER           :float = 250*300
VARIANCIA_TAMANHO_DATACENTER :float = 25*300


#Quando a topologia
NUMERO_DE_SLOTS    :int   = 200
NUMERO_DE_CAMINHOS :int   = 10
SLOT_SIZE          :float = 12.5

#Quanto a simulação
REQUISICOES_POR_SEGUNDO :float = 75
NUMERO_DE_REQUISICOES   :int   = 300000
NUMERO_DE_ISPS          :int   = 5