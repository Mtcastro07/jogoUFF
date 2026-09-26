# assets/art — onde cada peca gerada vai parar

As tres pastas de cima sao as TRES CATEGORIAS DO GERADOR:

    objetos/       tudo que voce pedir como "object"
    ui/            tudo que voce pedir como "UI"
    personagens/   tudo que voce pedir como "character"

Dentro de objetos/ existe UMA divisao, e ela nao e artistica: e porque o
codigo desenha os dois grupos de um jeito diferente.

    objetos/jogo/        o que o jogador encosta ou le como obstaculo:
                         caco, bloco, ponte, coluna, chevron, portal.
                         BRANCO #FFFFFF + CINZA #808080, sem cor nenhuma.
                         Escala da TELA (o tile tem 48 px).
                         O codigo tinge com a paleta de cada fase, entao a
                         mesma forma serve as tres.

    objetos/cenario/<fase>/   o que fica longe, no ceu e no horizonte:
                         astro, arvores, ilhas, torres, nuvens.
                         COLORIDO, na paleta da fase (config.py, TEMAS).
                         Escala do BUFFER: o fundo e desenhado em 320x180 e
                         ampliado 4x. Gere grande e exporte DIVIDIDO POR 4,
                         com nearest neighbor. Uma arvore de 160 px na tela
                         e um arquivo de 40 px de altura.

    objetos/jogo/<fase>/  pecas de jogo DESTA fase, ja coloridas: o codigo
                         NAO tinge. Escala da TELA. Ganham da versao comum:
                         o jogo procura aqui primeiro e so depois em
                         objetos/jogo/. Hoje: nas ilhas cacos, bloco, portal,
                         3 colunas e a ponte. (O chao.png do bosque fica
                         guardado, mas o chao do bosque agora e desenhado:
                         veja "Bosque dos Ecos" abaixo.)
                         Peca gerada na paleta errada (a ponte das ilhas veio
                         verde) e recolorida pelo importador.

    Variantes: coluna_1, coluna_2, coluna_3... o jogo alterna entre elas.
    Na cidadela, coluna_2 e coluna_4 (a esfera de anel dourado flutuando)
    ficam de fora: pareciam moedas, e o jogo nao tem moedas (arte.FORA).

    Ponte: a ponte de eco (segurar o botao sobre um abismo) SAIU do jogo; as
    pecas ponte_off, ponte_pronta, ponte_viva e ponte_pilar ficam guardadas
    nas pastas, mas nenhuma fase as usa.

ui/ e uma pasta so, nao uma por fase. A arte crua dela vem de objetos/ui/ do
gerador. As molduras (moldura_*.png, trilho.png) vem de "Painel e botao/",
recortadas no desenho: o codigo estica em 9 fatias, quinas intactas. Letreiros de julgamento e logo ficam no tamanho em que foram
desenhados: o codigo amplia por fator inteiro (o logo 3x no menu, a medalha 2x
no resultado). coracao_3f tem celulas de 40x40: cheio, cheio na batida, vazio. Os emblemas das fases sao UI (aparecem
na carta de selecao, em escala de tela), entao ficam aqui com a fase no nome:
emblema_bosque.png, emblema_ilhas.png, emblema_eclipse.png.

## Animacao

Tira horizontal, quadros da mesma largura, sufixo _Nf no nome.
    caco1_4f.png = 4 quadros de 48x48 = arquivo de 192x48.
Sem sufixo = imagem parada.

## Conferir

    ./.venv/bin/python ferramentas/conferir_arte.py

Diz, peca por peca: ok, -- (ainda falta) ou o erro exato de tamanho, quadros,
transparencia ou cor. O jogo roda com qualquer subconjunto: o que nao existe
continua desenhado por codigo (jogo/arte.py, jogo/cenario.py).

## Pecas paradas e animadas

objetos/jogo/ aceita as duas formas: caco1_4f.png (tira de 4 quadros) ou
caco1.png (parado). Se as duas existirem, vale a animada.

## Importar arte crua do gerador

    ./.venv/bin/python ferramentas/importar_arte.py

O mapeamento "arquivo do gerador -> nome do contrato" fica no topo do script.
Ele recorta, reduz, enevoa a camada distante, tira o contorno preto do
cenario e acinzenta as pecas de jogo.

## Personagem

personagens/ vem no formato do gerador de personagens, olhando para a direita:

    east.png                        parado (1 quadro)
    Full_Sprint/east/frame_*.png    corrida: o ciclo inteiro dura 1 batida
    Running_Jump/east/frame_*.png   pulo: os quadros sao escolhidos pela
                                    velocidade vertical; o ultimo e o pouso

Cada animacao tem a propria tela (a corrida e 72x72, o resto 56x56). O jogo
alinha todas pelo centro da CABECA e pela linha dos pes, para o Leo nao
deslizar ao trocar de animacao. Escala 1x: a largura dele (33 px) e a da caixa
de colisao (32 px). Sem pose propria de sustentar a nota, ele corre sobre a
ponte de luz. Sem nada disso, o jogo volta para a folha da Ozzbit.

O interruptor e LEO_DESENHADO, em jogo/config.py: com False (o valor atual) o
jogo usa a folha da Ozzbit mesmo com estes arquivos aqui.
south.png (de frente) nao e usado: o jogo e todo de lado.

## Arte crua

A saida do gerador, com os nomes dele, fica em "objetos 2/" (cenario/, ui/) e
"Painel e botao/", dentro desta pasta. O jogo NAO le essas pastas: quem le e
ferramentas/importar_arte.py, que tem a lista "arquivo cru -> nome do
contrato" e grava as pecas prontas nas pastas acima.

## Cacos

Caco parado (caco1.png, sem o _Nf) ganha volume e glitch no codigo
(arte._facetar e arte._glitch): a face da direita -- a da lua e do sol --
clareia, a da esquerda escurece, e numa tira de 16 quadros so 3 mexem (uma
faisca na ponta, uma fatia que escorrega de lado). Cada coluna do mundo tem a
sua defasagem, entao os glitches nunca batem juntos: o perigo nao pode pulsar,
ou vira uma pista falsa de tempo. Uma tira caco1_4f.png pronta dispensa isso.

## Bosque dos Ecos

O chao do bosque e desenhado por jogo/terreno.py: um caminho de lajes de pedra
com musgo, na paleta do chao.png, sobre terra em camadas com pedras e raizes.
Lajes, camadas e pedras seguem o x/y do mundo, entao nada se repete como
carimbo. Em cima do caminho nascem tufos, flores e cogumelos que brilham
(redondos: pontudo e so o perigo). Os fossos tem fundo de terra, e os cacos
ficam cravados nele.

No ar, vaga-lumes (jogo/efeitos.py).

## Ilhas Suspensas

O chao das ilhas nao usa sprite: e desenhado por jogo/terreno.py como ilhas de
pedra flutuando, na paleta das ilhas com cascata (a (6) e a (7) do gerador),
com nos de cristal na borda, raizes pendendo e cascatas nas pontas. Por cima
da rocha: a borda de cima escorrendo irregular, veios de cristal (os mesmos do
bloco das ilhas), pedras incrustadas e tufos de musgo lilas.

## Cidadela do Eclipse

O chao da cidadela tambem e desenhado (terreno.py): alvenaria na paleta das
muralhas geradas. O fundo troca as colinas por muralhas com ameias
(cenario.MURALHAS), e as torres e castelos ficam de pe em cima delas.

Nas duas fases, colunas sao cenario: puxadas para a cor do fundo e com o pe
atras da borda do chao (mundo.AMBIENTE). Cacos que nao estao sobre chao
ganham um leito de rocha, e blocos ganham sombra de contato.

