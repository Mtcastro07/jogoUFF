import os
import sys
from collections import namedtuple

PASTA_DO_JOGO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_MUSICAS = os.path.join(PASTA_DO_JOGO, "assets", "music")
PASTA_SONS = os.path.join(PASTA_DO_JOGO, "assets", "sfx")
IMAGEM_DO_LEO = os.path.join(PASTA_DO_JOGO, "male_hero_free", "male_hero.png")
FONTE = os.path.join(PASTA_DO_JOGO, "assets", "fonts", "Silkscreen-Regular.ttf")
ONDE_SALVA = os.path.join(os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else PASTA_DO_JOGO,
                          "savegame.json")

LARG_TELA, ALT_TELA = 1280, 720
TELA_CHEIA = True
FPS = 60
VOLUME_DAS_MUSICAS = 0.7
VOLUME_DOS_SONS = 0.8

QUADRADO = 48
LINHA_DO_CHAO = 10
TEMPINHO = 1.0 / 240.0

TAM_DO_LEO = 32
LARG_DO_PE = 22
LARG_DO_CORPO = 20
ALT_DO_CORPO = 30
CORPO_PRA_FRENTE = 2
FOLGA_DO_PE = 2
FOLGA_DO_PE_NO_AR = 9
FOLGA_DO_CACO = 3
QUINA = 8
PULINHO = 0.5
CORTA_O_PULO = 0.45
PULO_ATRASADO = 0.04
PULO_ADIANTADO = 0.7
QTD_VIDAS = 3
TEMPO_SEM_LEVAR_DANO = 1.5

TEMPO_PERFEITO = 0.10
TEMPO_BOM = 0.20
PONTOS_DO_PERFEITO = 50
PONTOS_DO_BOM = 25
NOTAS = ((0.95, "S"), (0.85, "A"), (0.70, "B"), (0.0, "C"))

BRANCO = (240, 240, 250)
CINZA = (150, 155, 185)
FUNDO = (18, 16, 36)
PAINEL = (30, 26, 56)
AMARELO = (255, 214, 92)
VERMELHO = (255, 86, 112)
VERDE = (120, 255, 168)
AZUL = (120, 240, 255)
ROXO = (200, 160, 255)
CONTORNO = (14, 10, 28)

COR_DO_ACERTO = {"perfeito": VERDE, "bom": AMARELO, "erro": VERMELHO}
COR_DA_DIFICULDADE = {"FACIL": VERDE, "MODERADO": (190, 240, 110), "NORMAL": AMARELO,
                      "AVANCADO": (255, 150, 80), "DIFICIL": VERMELHO}
COR_DA_NOTA = {"S": AMARELO, "A": VERDE, "B": AZUL, "C": ROXO, "-": CINZA}

Tema = namedtuple("Tema", "nome ceu sol montanha chao chao_topo bloco perigo destaque")
CORES_DAS_FASES = {
    "bosque": Tema("bosque", ceu=(22, 34, 66), sol=(255, 226, 170),
                   montanha=(20, 56, 60), chao=(32, 62, 54),
                   chao_topo=(110, 220, 160), bloco=(48, 84, 74),
                   perigo=(240, 110, 160), destaque=(126, 244, 180)),
    "dunas": Tema("dunas", ceu=(52, 132, 160), sol=(255, 244, 200),
                  montanha=(198, 132, 84), chao=(150, 92, 60),
                  chao_topo=(255, 226, 150), bloco=(170, 106, 72),
                  perigo=(232, 56, 92), destaque=(72, 226, 208)),
    "ilhas": Tema("ilhas", ceu=(136, 82, 104), sol=(255, 220, 150),
                  montanha=(86, 60, 112), chao=(58, 50, 92),
                  chao_topo=(150, 226, 255), bloco=(76, 68, 118),
                  perigo=(255, 106, 118), destaque=(255, 200, 130)),
    "geleira": Tema("geleira", ceu=(14, 22, 52), sol=(226, 240, 255),
                    montanha=(44, 72, 118), chao=(56, 92, 140),
                    chao_topo=(214, 246, 255), bloco=(84, 128, 178),
                    perigo=(214, 84, 255), destaque=(110, 255, 214)),
    "eclipse": Tema("eclipse", ceu=(14, 6, 26), sol=(255, 200, 110),
                    montanha=(30, 14, 50), chao=(28, 14, 46),
                    chao_topo=(178, 138, 232), bloco=(46, 26, 74),
                    perigo=(255, 128, 96), destaque=(255, 206, 120)),
}
