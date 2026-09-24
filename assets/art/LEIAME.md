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
                         objetos/jogo/. Hoje: o topo do chao do bosque, e nas
                         ilhas cacos, bloco, portal, 3 colunas e a ponte.
                         Peca gerada na paleta errada (a ponte das ilhas veio
                         verde) e recolorida pelo importador.

    Variantes: coluna_1, coluna_2, coluna_3... o jogo alterna entre elas.

    Ponte: ponte_off (longe dela) e ponte_pronta (Leo na zona) sao desenhadas
    TRANSLUCIDAS -- tabua opaca parece chao firme, e o jogador nao seguraria
    o botao. ponte_viva (a nota sustentada) e opaca. ponte_pilar emoldura o vao.

ui/ e uma pasta so, nao uma por fase. A arte crua dela vem de objetos/ui/ do
gerador. Letreiros de julgamento e logo ficam no tamanho em que foram
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
south.png (de frente) nao e usado: o jogo e todo de lado.

