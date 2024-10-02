

# Problema

## Cenário
Em uma rede óptica elástica (EON - Elastic Optical Network) em funcionamento com uma topologia dada por um grafo pesado com um dado número de Provedores de Internet (ISP - Internet Service Providers) responsáveis pelo roteamento das requisições espalhados por sua topologia, um desastre está prestes a acontecer. As ISPs serão, em momentos diferentes, alertadas sobre esse desastre e mudarão sua politicas de roteamento para que os links e nodes afetados pelo desastre sejam evitados e, alem disso, será dado início a uma migração de um banco de dados relacionado a dada ISP em direção ao node mais distante do node relacionado ao centro do desastre.

## Desafio
Uma vez que a ISP seja acionada o metodo de roteamento aplicado deve levar em consideração a possibilidade do mesmo "afogar" a migração de outras mensagens vindas da propia ou de outras ISPs em seu caminho uma vez que cada link em um caminho tem uma capacidade maxima. O objetivo é que o metodo de roteamento ativado no momento que o desastre é descoberto minimize a taxa de bloqueios em coparação ao roteamento padrão assim como maximize a capacidade das ISPs migrarem seus dados

## Caminho para solução

Para a solução desse problema, eu decidi criar um simulador que emula uma EON com parametros ajustaveis. Esse simulador emula o envio de um número X de requisições de datapath a uma taxa de Y requisições por segundo e coleta dados sobre o bloqueio e aceitação dessas mensagens durante todo o antes o durante e o logo depois do desastre

## Funcionamento do Simulador

O simulador planejado se trata de um conjunto de varios modulos que funcionam em conjuntos e utiliza como recurso principal a biblioteca simpy do python. Os modulos são:

### 1. [Simulador](simuladorV2/Simulador.py):
Classe é responsavel por receber um  [cenario](#2-cenario) ou criar um atravez do [gerador de cenários](), e executar um loop de criar uma [requisicão](#3-requisicao) com o [gerador de trafego](#31-geradordetrafego) ou receber uma requisição de uma lista de [requisições](#3-requisicao) pre feita, e rotear a mesma usando o roteamento da ISP de origem da [requisição](#3-requisicao)

### 2. [Cenario](simuladorV2/Cenario/Cenario.py):
Classe é responsavel por armazenar os objetos [Topologia](#4-topologia), [Desastre](#5-desastre), uma lista de objetos [ISPs](#6-isp) e, opcionalmente, uma lista de requisições pre contruida a serem encaminhadas, assim como possuir metodos de salvar um cenário e carregar um cenário em formato .pkl. O intenção de criação dessa classe é passar o mesmo cenário para Roteamentos de desastre diferentes e comparar o resultado dos mesmos
### 2.1. [GeradorDeCenarios](simuladorV2/Cenario/GeradorDeCenarios.py)
Classe de utilidade que guarda metodos referentes a geração de cenarios

### 3. [Requisicao](simuladorV2/Requisicao/Requisicao.py):
Essa é uma classe criada para armazenar informações sobre a requisição assim como informações sobre sua alocação ou bloqueio na topologia

### 3.1. [GeradorDeTrafego](simuladorV2/Requisicao/GeradorDeTrafico.py):
Essa é uma classe de utilidade que guarda metodos relacionados a geração de [requisições](#4-requisicao)

### 4. [Topologia](simuladorV2/Topologia.py):
Classe responsavel por instanciar inicialmente dados importantes da topologia assim como a matrix de listas de menores caminhos, slots para cada link. Uma vez instanciada é chamada por classes criadas a partir da interface iRoteamento para realizar a alocação e desalocação dos slots dos links

### 5. [Desastre](simuladorV2/Desastre/Desastre.py):
