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

Classe é responsável por receber um [cenario](#2-cenario) ou criar um atravez do [gerador de cenários](#21-geradordecenarios), e executar um loop de criar uma [requisicão](#3-requisicao) com o [gerador de trafego](#31-geradordetrafego) ou receber uma requisição de uma lista de [requisições](#3-requisicao) pre feita, e rotear a mesma usando o roteamento da ISP de origem da [requisição](#3-requisicao)

### 2. [Cenario](simuladorV2/Cenario/Cenario.py):

Classe é responsável por armazenar os objetos [Topologia](#4-topologia), [Desastre](#5-desastre), uma lista de objetos [ISPs](#6-isp) e, opcionalmente, uma lista de [requisições](#3-requisicao) pre contruida a serem encaminhadas, assim como possuir metodos de salvar um [cenário](#2-cenario) e carregar um [cenário](#2-cenario) em formato .pkl. O intenção de criação dessa classe é passar o mesmo [cenário](#2-cenario) com apenas o [roteamentos de desastre](#7-IRoteamento) diferentes e comparar o resultado dos mesmos

### 2.1. [GeradorDeCenarios](simuladorV2/Cenario/GeradorDeCenarios.py)

Classe de utilidade que guarda metodos referentes a geração de [cenários](#2-cenario)

### 3. [Requisicao](simuladorV2/Requisicao/Requisicao.py):

Essa é uma classe criada para armazenar informações sobre uma [requisição](#3-requisicao) assim como informações sobre o resultado da [requisição](#3-requisicao)

### 3.1. [GeradorDeTrafego](simuladorV2/Requisicao/GeradorDeTrafico.py):

Essa é uma classe de utilidade que guarda metodos relacionados a geração de [requisições](#3-requisicao)

### 4. [Topologia](simuladorV2/Topologia.py):

Classe responsável por instanciar inicialmente dados importantes da topologia assim como a matrix de listas de menores caminhos, slots para cada link. Uma vez instanciada é chamada por classes criadas a partir da interface [IRoteamento](#7-IRoteamento) para realizar a alocação e desalocação dos slots dos links

### 5. [Desastre](simuladorV2/Desastre/Desastre.py):

Classe responsável por criar as falhas de rede nos links e nodes assim como identificar quais requisições foram afetadas pelo desastre e acionar o reroteamento das mesmas

### 6. [ISP](simuladorV2/ISP/ISP.py):

Responsável por armazenar informações sobre a topologia da ISP assim como o metodo de [roteamento](#7-IRoteamento) sendo utilizado no momento e o metodo a ser aplicado uma vez que o [desastre](#5-desastre) seja iniciado. Responsável por, uma vez que o tempo de reação seja atingido, iniciar a migração do [Datacenter](#8-datacenter) e trocar o metodo de roteamento

### 6.1. [GeradorDeISPs](simuladorV2/ISP/GeradorDeISPs.py):

Responsável por gerar a disposição física de um número requisitado de ISPs na topologia e retorna a lista das mesmas

### 7. [IRoteamento](simuladorV2/Roteamento/IRoteamento.py):

Interface para classes de utilidade, que não precisam ser instanciadas, que contem metodos responsaveis pela tomada de decisões de alocação de caminho e janela para requisições. Os metodos utilizados pelas outras classes são rotear_requisicao e rerotear_requisicao. Implementa um padrão State para definir qual o comportamento de Roteamento em vigor

### 8. [Registrador](simuladorV2/Registrador.py):

Essa é uma classe Singleton chamada no codigo inteiro responsável por coletar dados sobre o resultado das requisições

### 9. [Variaveis](simuladorV2/Variaveis.py):

Arquivo responsável por definir dados usados principalmente com os geradores msa tambem para definir o número de requisições passadas e a taxa dessas mensagens

# Afazeres

- [ ] Ajustar comportamento indesejado do Registrador com a adição da classe Cenario
- [ ] Criar função de comparação de Registradores em [teste](simuladorV2/teste.ipynb)
- [ ] Capturar um numero substâncial de estados da rede durante a execução do desastre
- [ ] Criar nova classe Roteamento de mesmo de maneira custosa checando todas as possibilidades de alocação de todos os caminhos disponiveis e ranqueia elas de melhor para pior, com base na taxa e bloqueios da requisição seguinte vinda de qualquer outro node para qualquer outro node
- [ ] Criar uma função de comparação que compara o resultado de um dado metodo de roteamento com a maneira custosa
- [ ] Criar heuristica com performance melhor que o baseline( não trocar o metodo de roteamento) e seja razoavelmente custoso
