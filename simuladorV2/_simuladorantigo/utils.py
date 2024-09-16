from VARIAVEIS import *
import networkx as nx
from itertools import islice

# Calcula a distância do caminho de acordo com os pesos das arestas               


#Calcula os k-menores caminhos entre pares o-d
def k_shortest_paths( G, source, target, k, weight='weight'):
    return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

# Calcula o formato de modulação de acordo com a distância do caminho    
def Modulation( dist, demand):
    if dist <= 500:
        return (float(demand) / float(4 * SLOT_SIZE))
    elif 500 < dist <= 1000:
        return (float(demand) / float(3 * SLOT_SIZE))
    elif 1000 < dist <= 2000:
        return (float(demand) / float(2 * SLOT_SIZE)) 
    else:
        return (float(demand) / float(1 * SLOT_SIZE))


# Calcula o formato de modulação de acordo com a distância do caminho    
def FatorModulation( dist):
    if dist <= 500:
        return (float(4 * SLOT_SIZE))
    elif 500 < dist <= 1000:
        return (float(3 * SLOT_SIZE))
    elif 1000 < dist <= 2000:
        return (float(2 * SLOT_SIZE)) 
    else:
        return (float(1 * SLOT_SIZE))
