"""
Constantes do jogo: janela, mundo, fisica, ritmo e cores.

Tudo que precisa ser ajustado "no olho" fica aqui, num lugar so.
"""

import os
from collections import namedtuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_MUSICA = os.path.join(RAIZ, "assets", "music")
DIR_SFX = os.path.join(RAIZ, "assets", "sfx")
SPRITESHEET = os.path.join(RAIZ, "male_hero_free", "male_hero.png")
FONTE = os.path.join(RAIZ, "assets", "fonts", "Silkscreen-Regular.ttf")
ARQUIVO_SAVE = os.path.join(RAIZ, "savegame.json")

# ------------------------------------------------------------------ janela
LARGURA, ALTURA = 1280, 720    # resolucao em que o jogo e DESENHADO (16:9)
TELA_CHEIA = True              # abre ocupando o monitor; F11 alterna com a janela.
                               # A imagem e ampliada sem suavizar para qualquer
                               # tela: 1920x1080 e 1,5x, 2560x1440 e 2x, 4K e 3x.
                               # Fora de 16:9, sobram faixas pretas.
FPS = 60
VOLUME_MUSICA = 0.7            # 0..1
VOLUME_SFX = 0.8

# ------------------------------------------------------------------- mundo
TILE = 48                      # lado de um bloco do grid, em pixels
# a velocidade da corrida e o pulo (batidas no ar, tiles por batida, altura)
# sao de cada mundo: fases.PULO
LINHA_CHAO = 10                # linha do grid onde o chao comeca (y = 10 * TILE)
PASSO_FISICA = 1.0 / 240.0     # a fisica anda em passos fixos de 1/240 s

# ----------------------------------------------------------------- jogador
# Os mundos desenhados como a VERSAO ALPHA do jogo (jogo/alpha.py): os mesmos
# sprites, cenario e interface, simplificados e sem animacao -- foi usada para
# gravar o video do alpha. Vazio: todas as fases na versao final, completas.
# Para gravar de novo, ponha o nome do mundo aqui (ex.: ALPHA = {"bosque"}).
ALPHA = set()
LEO_DESENHADO = False          # True: o Leo gerado para o jogo (assets/art/personagens/);
                               # False: a folha da Ozzbit (male_hero_free/). A arte nova
                               # fica guardada nos dois casos.
JOGADOR_TAM = 32               # lado da caixa de colisao (o sprite tem 32 px de largura)
LARGURA_APOIO = 22             # a SOLA: a parte da caixa que pisa no chao e bate em
                               # parede. Com a caixa inteira o Leo ficava de pe no ar,
                               # com o corpo todo para fora da beirada.
# O que os cacos ferem e o CORPO do Leo como ele aparece na tela (pernas e
# tronco, um pouco a frente do centro da caixa), contra o DESENHO de cada caco:
# o que se ve encostar e o que machuca.
CORPO_LARGURA = 20             # px
CORPO_ALTURA = 30              # px, de logo acima dos pes para cima
CORPO_FRENTE = 2               # px que o corpo fica a frente do centro da caixa
FOLGA_PE = 2                   # px da sola que nao contam (o pe que so encosta)
FOLGA_PE_AR = 9                # no ar as pernas vao encolhidas: os pes sobem ~9 px no sprite
FOLGA_CACO = 3                 # px da ponta de cada caco que nao contam
QUINA = 8                      # pousar ate 8 px abaixo do topo de um degrau sobe nele
# A ALTURA do pulo depende de quanto tempo o botao fica apertado: soltando na
# subida o arco fica mais baixo, entao um toque rapido e um pulo baixo e
# segurar ate o alto do arco e o pulo inteiro. Os dois pousam no mesmo lugar,
# na batida seguinte. Todo toque rapido da o mesmo pulo baixo, que sobe
# PULO_MINIMO da altura: passa por cacos, blocos, vaos e degraus de 1 tile --
# e as fases so tem isso, entao nenhum obstaculo pede o botao segurado.
PULO_MINIMO = 0.5              # fracao da altura do pulo que um toque rapido alcanca
CORTE_PULO = 0.45              # soltar na subida: o arco sobe o que 45% da velocidade subiria
COYOTE = 0.04                  # ainda da para pular ate 40 ms depois de sair do chao
BUFFER_PULO = 0.7              # BATIDAS: um toque ate 0,7 batida antes de pousar vale
                               # como pulo (sai no pouso). Cobre o pior caso da janela BOM:
                               # um pulo atrasado (0,2) que desce um degrau (o pouso atrasa
                               # ate 0,22) seguido de um toque adiantado (0,2).
VIDAS = 3
INVULNERAVEL = 1.5             # BATIDAS sem levar dano depois de uma batida: 1,1 s no
                               # bosque, 0,8 s nas ilhas, 0,6 s na cidadela

# ------------------------------------------------------------------- ritmo
# Janelas de julgamento, em fracao da batida. Sao as maiores janelas em que
# um toque julgado como "bom" ainda passa por cima de todos os obstaculos.
JANELA_PERFEITO = 0.10
JANELA_BOM = 0.20
PONTOS_PERFEITO = 50
PONTOS_BOM = 25
NOTAS = ((0.95, "S"), (0.85, "A"), (0.70, "B"), (0.0, "C"))   # por precisao

# ------------------------------------------------------------------- cores
BRANCO = (240, 240, 250)
CINZA = (150, 155, 185)
FUNDO = (18, 16, 36)
PAINEL = (30, 26, 56)
AMARELO = (255, 214, 92)
VERMELHO = (255, 86, 112)
VERDE = (120, 255, 168)
AZUL = (120, 240, 255)
ROXO = (200, 160, 255)
CONTORNO = (14, 10, 28)         # contorno escuro dos textos: le em cima de qualquer ceu

COR_JULGAMENTO = {"perfeito": VERDE, "bom": AMARELO, "erro": VERMELHO}
COR_DIFICULDADE = {"FACIL": VERDE, "NORMAL": AMARELO, "DIFICIL": VERMELHO}
COR_NOTA = {"S": AMARELO, "A": VERDE, "B": AZUL, "C": ROXO, "-": CINZA}

# Paleta de cada mundo: so cores chapadas.
Tema = namedtuple("Tema", "nome ceu sol montanha chao chao_topo bloco perigo destaque")
TEMAS = {
    "bosque": Tema("bosque", ceu=(22, 34, 66), sol=(255, 226, 170),
                   montanha=(20, 56, 60), chao=(32, 62, 54),
                   chao_topo=(110, 220, 160), bloco=(48, 84, 74),
                   perigo=(240, 110, 160), destaque=(126, 244, 180)),
    "ilhas": Tema("ilhas", ceu=(136, 82, 104), sol=(255, 220, 150),
                  montanha=(86, 60, 112), chao=(58, 50, 92),
                  chao_topo=(150, 226, 255), bloco=(76, 68, 118),
                  perigo=(255, 106, 118), destaque=(255, 200, 130)),
    "eclipse": Tema("eclipse", ceu=(14, 6, 26), sol=(255, 200, 110),
                    montanha=(30, 14, 50), chao=(28, 14, 46),
                    chao_topo=(178, 138, 232), bloco=(46, 26, 74),
                    perigo=(255, 128, 96), destaque=(255, 206, 120)),
}
