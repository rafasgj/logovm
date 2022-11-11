LogoVM
======

A LogoVM é um ambiente de execução semelhante ao da linguagem Logo, porém ao invés de interpretar a linguagem Logo, a LovoVM traduz e executa programas em uma linguagem de mais baixo nível, a LogoASM.

A LogoVM é implementada como uma máquina de pilha, mesmo assim, contém seis registradores de dados, e um conjunto de flags de estado da VM, dois registradores de posição da caneta de desenho (`tartaruga`), uma área de "vídeo" onde as instruções de desenho são executadas, e uma área de memória para o armazenamento de dados.

Ao executar o código em LogoASM a entrada de dados é realizada pela entrada de dados padrão do sistema, a saída de dados é realizada pela saída padrão do sistema. Caso alguma operação de desendo seja executada, ou se a flag DRAW for setada, uma imagem contendo o resultado do desenho será gerada.

Para instruções de instalação consulte o arquivo [INSTALL.md](INSTALL.md).


Modelo de execução
------------------

Toda operação da LogoVM é realizada com dados da pilha, porém, na execução da operação os dados são lidos para registradores, a partr dos quais a operação será realizada.

Por exemplo, a operação ADD soma dois valores numéricos no topo da pilha, e armazena o resultado de volta no topo da pilha. Durante a operação os registradores `R0` e `R1` são alterados.

O código para a operação `2 + 5` é:

```
  PUSH 2
  PUSH 5
  ADD
```

Após `PUSH 2`, o estado da pilha é `| 2` (onde '|' é o marcador de pilha vazia). Depois de executar `PUSH 5`, o estado da pilha é `| 2 5`.

Ao executar a instrução `ADD`, o valor `5` será extraído para R1, o valor `2` será extraído para `R0` e os valores dos registradores `R0` e `R1` serão somados, o resultado armazenado em `R0`, e o valor de `R0` será adicionado à pilha.

O estado final da pilha será `| 7`, e dos registradores `R0 = 7` e `R1 = 5`.

Outras operações podem exigir que um ou mais parâmetros sejam armazenados na pilha para que sejam executadas.


LogoASM
-------

LogoASM é a linguagem interpretada pela LogoVM para a execução dos programas. É uma linguagem de baixo nível, que permite a execução de todos os comandos necessários de uma implementação da lingagem Logo.

Alguns elementos importantes da linguagem são:

    * identificadores
        : Nomes de elementos definidos pela expressão regular
          `[_a-zA-Z][_a-zA-Z0-9]\*`

    * Strings
        : Literais representando cadeias de caracteres, delimitadas por
          apóstrofes (') ou aspas (")
    
    * Numeros
        : Literais representando números inteiro ou de ponto flutuante.

Sobre os números, em geral, o tipo de dado de um número é "NUMBER", em alguns casos específicos, onde a distinção é óbvia, eles são tratados de forma diferente caso o número seja um "INT" ou um "FLOAT". A coerção de tipo de "INT" para "FLOAT" é automática e feita sempre que necessário.

Um programa em LogoASM possui um cabeçalho de inicialização, uma seção de dados, e uma seção de código.

O cabeçalho de inicialização deve conter a definição do ponto de início do programa, definido pela diretiva `START` e, opcionalmente, a inicialização do sistema de desenho com a diretiva `INIT`.

A diretiva `START` define o `label` que será utilizado como endereço de entrada do programa, por exemplo, `START main` define o label `main` como ponto de entrada do programa, e define `main` como um `label de função`.

```
.START <identifier>
```

A diretiva `INIT` configura e sistema de desenho com a coordenada do ponto inicial do desenho e o tamanho da área de desenho, em pixels.

```
.INIT <x: INT> <y: INT> <width: INT> <height: INT>
```

Por exemplo, `INIT 200 200 400 400` configuraria uma área de desenho de 400 pixels de largura por 400 pixels de largura e colocaria o apontador de desenho no meio dessa área (200x200).

Após o cabeçalho de inicialização, caso o programa utilize variáveis armazenadas em memória, deve ser utilizado uma seção `DATA` com a declaração e inicialização das variáveis.

```
.DATA <var_list>  
```

Cada variável é composta de um identificador e um valor de inicialização. Os tipos de dados não são declarados para uma variável, eles são inferidos a partir do tipo de dado do valor armazenado.

```
   pi     3.141516
   angle  0
   greet  "Hello, "
```

Os tipos de dados não são verificados, porém, uma operação pode exigir tipos de dados específicos, e apenas nesse caso, os tipos de dados dos valores serão verificados.

A última seção do programa é a seção de código. Nesta seção serão adicionados os comandos que serão executados, sequencialmente, pela LogoVM. A diretiva `CODE` marca o início da seção de código.

```
.CODE
```

A seção `CODE` contém uma sequência de comandos que irão alterar o estado da LogoVM.

Os seguintes commandos controlam a lógica de execução do programa:

| Comando | Descrição | Stack IN | Stack OUT | Regs. IN | Regs.  OUT |
| :------ | :-------- | :------- | :-------- | :------- | :--------- |
| DEF \<id> : | Define uma nova função que pode ser chamada via CALL. | -- | -- | -- | -- |
| CALL \<id> | Executa a função de nome _id_. | Todos os parâmetros para a função devem ser colocados na pilha. | Se a função retorna valores, eles estarão na pilha. | A alteração de registradores depende da funçã executada. | A alteração de registradores depende da funçã executada. |
| :\<id> | A função `label` (:) cria um label que pode ser alvo de um `jump`. | -- | -- | -- | -- |
| PUSH \<value> | Empilha _value_. | -- | Topo = \<value> | -- | -- |
| POP | Desempilha um elemento. | ... \<value> | ... | -- | R0 = \<value> |
| DUP | Duplica o elemento no topo da pilha. | ... \<value> | ... \<value> \<value> | -- | R0 = \<value> | -- | R0 = \<value> |
| LOAD \<id> | Empilha o valor atual da variável com nome _id_. | ... | ... \<id.value> | -- | R0 = \<id.value>
| STORE \<id> | Desempilha um elemento e armazena o valor na variável com nome _id_. | ... \<value> | ... | -- | R0 = \<id.value> |
| CMP \<value> | Compara o valor do topo da pilha com \<value>. | ... \<topo> | ... \<topo> | -- | R0 = -1 se `(topo < value)`; R0 = 0 se `(topo == value)`; R0 = +1 se `(topo > value)` |
| CMP \<id> | Compara o valor do topo da pilha com o valor da variável \<id>. | ... \<topo> | ... \<topo> | -- | R0 = -1 se `(topo < id.value)`; R0 = 0 se `(topo == id.value)`; R0 = +1 se `(topo > id.value)` |
| JP \<id> | Move o PC para o `label` idetificado por \<id>. | -- | -- | -- | PC = \<label[id].pc>, R5 = PC |
| JZ :\<id> | Move o PC para o `label` idetificado por \<id>, se R0 = 0. | -- | -- | R0 | PC = \<label[id].pc>, R5 = PC |
| JNZ :\<id> | Move o PC para o `label` idetificado por \<id>, se R0 != 0. | -- | -- | R0 | PC = \<label[id].pc>, R5 = PC |
| JMORE :\<id> | Move o PC para o `label` idetificado por \<id>, se R0 > 0. | -- | -- | R0 | PC = \<label[id].pc>, R5 = PC |
| JLESS :\<id> | Move o PC para o `label` idetificado por \<id>, se R0 \< 0. | -- | -- | R0 | PC = \<label[id].pc>, R5 = PC |
| SET \<number> | Liga a _flag_ indicada por `number` (um inteiro). | -- | -- | -- | FL |
| UNSET \<number> | Desliga a _flag_ indicada por `number` (um inteiro). | -- | -- | -- | FL |
| RET | Retorna ao contexto de execução (função) anterior. | -- | -- | -- | PC | 
| HALT | Termina a execução do programa e salva a imagem gerada se a flag `DRAW` estiver setada. | -- | -- | -- | PC | 


LogoASM disponibiliza as seguintes operações matemáticas:

| Comando | Descrição | Stack IN | Stack OUT | Regs. IN | Regs.  OUT |
| :------ | :-------- | :------- | :-------- | :------- | :--------- |
| ADD | Retira dois valores da pilha, soma e empilha o resultado. Opera apenas em `NUMBER`.| ...\<lhs> \<rhs> | ... \<lhs + rhs> | -- | R0 = \<lhs + rhs>, R1 = \<rhs> |
| SUB | Retira dois valores da pilha, subtrai e empilha o resultado. Opera apenas em `NUMBER`.| ...\<lhs> \<rhs> | ... \<lhs - rhs> | -- | R0 = \<lhs - rhs>, R1 = \<rhs> |
| MUL | Retira dois valores da pilha, multiplica e empilha o resultado. Opera apenas em `NUMBER`.| ...\<lhs> \<rhs> | ... \<lhs * rhs> | -- | R0 = \<lhs * rhs>, R1 = \<rhs> |
| DIV | Retira dois valores da pilha, divide e empilha o resultado. Opera apenas em `NUMBER`.| ...\<lhs> \<rhs> | ... \<lhs / rhs> | -- | R0 = \<lhs / rhs>, R1 = \<rhs> |
| IDIV | Retira dois valores da pilha, realiza a divisão inteira e empilha o resultado e o quociente. Opera apenas em `NUMBER`.| ...\<lhs> \<rhs> | ... \<resultado> \<resto> | -- | R0 = \<resultado>, R1 = \<resto> |
| POW | Retira dois valores da pilha, eleva o primeiro à potência definida pelo segundo e empilha o resultado. Opera apenas em `NUMBER`. | ...\<lhs> \<rhs> | ... \<lhs ** rhs> | -- | R0 = \<lhs ** rhs>, R1 = \<rhs> |
| RAND | Empilha um valor randômico, do tipo _float_, no intervalo [0,1).| ... | ... \<value> | -- | R0 = \<value> |
| TRUNC | Trunca o valor no topo da pilha para a sua parte inteira. Opera apenas em `NUMBER`. | ...\<float> | ... \<int> | -- | R0 = \<int> |


Flags e Registradores
---------------------

A LogoVM possui seis registradores, que, nessa versão não são acessíveis para uso geral. Existem também 3 _flags_ de controle e status:

* PEN (1): Quando setada, a função "MOVE" irá desenhar o caminho percorrido.
* DRAW (2): Quando setada, a função "HALT" irá gerar uma imagem com o conteúdo da memória de vídeo.
* EXC (5): Quando setada, ocorreu uma exceção em alguma operação realizada. A exceção dependerá da operação e do erro.


Entrada e Saída de Dados
------------------------

A entrada e saída de dados é realizada por meio de duas funções internas:

| Comando | Descrição | Stack IN | Stack OUT | Regs. IN | Regs.  OUT |
| :------ | :-------- | :------- | :-------- | :------- | :--------- |
| READ | Lê um valor da entrada padrão e empilha.| ... | ... \<value> | -- | R4 = \<value> |
| WRITE | Desempilha um `INT` da pilha, e então desempilha o número de elementos indicado pelo `INT`. Envia os elementos para a saída padrão. | ... \<a> ... \<b> \<int: count(a..b)> | ... | -- | -- |

Dado o seguinte trecho de código:

```
  PUSH "Hello, "
  LOAD nome
  PUSH 2
  CALL WRITE
```

Ao executar esse código, considerando que a variável `nome` contém o valor `John`, o resultado impresso na saída padrão seria `Hello, John`.


Comandando a tartaruga
----------------------

Os seguintes comandos podem ser utilizados para controlar a área de desenho:

| Comando | Descrição | Stack IN | Stack OUT | Regs. IN | Regs.  OUT |
| :------ | :-------- | :------- | :-------- | :------- | :--------- |
| MVTO    | Retira dois valores da pilha representando as coordenadas horizontal e vertical e posiciona o cursor de desenho nessa posição | ... \<y> \<x> | ... | -- | R0 = \<x>, R1 = \<y> |
| SETPX   | Seta a posição do pixel sob o cursor de desenho para `branco`. | -- | -- | -- | -- |


Para setar o valor de um pixel na posição `(25, 30)`, utilize:

```
PUSH 25
PUSH 30
MVTO
SETPX
```


Existem duas funções definidas na LogoVM para controle do modo de desenho.

A função `CLRSCR` limpa a tela de desenho e reseta a flag `DRAW`. É uma função que não recebe nenhum parâmetro e não altera outros registradores.

A função `MOVE` move o cursor de desenho (`tartaruga`) na área de desenho, desenhando se a flag `PEN` (1) estiver setada. A função recebe dois parâmetros, um angulo, em graus, e o tamanho do segmenho de reta a ser desenhado. O angulo é sempre em relação ao eixo horizontal, sendo que o angulo _0 grous_ (zero) é paralelo ao eixo horizontal, com direção da esquerda para a direita. Os angulos crescem no sentido anti-horário, por isso, o angulo de _90 graus_, é paralelo ao eixo vertical, com direção de baixo para cima. Os registradores R0 e R1 armazenam a posição final da `tartaruga`. Veja o exemplo de código para gerar uma reta de tamanho _5_, a _45 graus_:

```
PUSH 45
PUSH 5
CALL MOVE
```


Executando um programa a partir do shell
----------------------------------------

Para executar um programa com a LogoVM a partir de um _shell_, execute:

```
logovm <programa> [<parâmetros>]
```

Apenas um programa pode ser carregado por vez e, caso sejam fornecidos, os parâmetros serão armazenados na pilha de execução _antes_ da execução do programa. Por exemplo,dados os parâmetros `a b c`, o estado inicial da pilha será `| a b c`, ou seja, ao retirar os parâmetros de linha de comando da pilha, eles serão obtidos na ordem em que foram apresentados.

Para aumentar o nível de informação interna da execução da LogoVM, voce pode passar, múltiplas vezes, o parâmetro `-d`, o que aumentará o nível de debug da VM (até `-ddd`). Por exemplo, para ver o debug da VM e do parser e lexer da VM, você usará:

```
logovm -ddd <programa> [<parâmetros>]
```

Lembre-se, que ao utilizar `-d` o formato de saída do arquivo de imagem será, sempre, `PNM`.

