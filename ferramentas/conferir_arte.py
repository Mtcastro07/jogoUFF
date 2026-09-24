"""
Confere os PNGs de assets/art/ contra o contrato de nomes e tamanhos.

    ./.venv/bin/python ferramentas/conferir_arte.py

Para cada peca diz: FALTA (ainda desenhada por codigo), OK, ou o erro exato
de tamanho / quadros / transparencia. O jogo roda com qualquer subconjunto:
o que nao existe continua sendo desenhado por codigo.
"""

import os
import re
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_ART = os.path.join(RAIZ, "assets", "art")

# pasta -> [(arquivo, quadros, largura_da_celula, altura, cinza)]
# largura/altura None = livre (silhuetas de cenario, medidas pela faixa abaixo)
CONTRATO = {
    "objetos/jogo": [
        ("caco1_4f.png", 4, 48, 48, True),
        ("caco2_4f.png", 4, 48, 48, True),
        ("caco3_4f.png", 4, 48, 48, True),
        ("bloco.png", 1, 48, 48, True),
        ("ponte_off.png", 1, 48, 16, True),
        ("ponte_pronta.png", 1, 48, 16, True),
        ("ponte_viva_4f.png", 4, 48, 16, True),
        ("ponte_pilar.png", 1, 16, 64, True),
        ("coluna_96_2f.png", 2, 48, 96, True),
        ("coluna_144_2f.png", 2, 48, 144, True),
        ("chevron_2f.png", 2, 32, 32, True),
        ("portal_6f.png", 6, 96, 192, True),
    ],
    # pecas de jogo PROPRIAS de uma fase: coloridas, largura de 1 tile
    "objetos/jogo/bosque": [
        ("chao.png", 1, 48, None, False),
    ],
    "objetos/cenario/bosque": [
        ("astro_3f.png", 3, 44, 44, False),
        ("longe_1.png", 1, None, None, False),
        ("longe_2.png", 1, None, None, False),
        ("longe_3.png", 1, None, None, False),
        ("longe_4.png", 1, None, None, False),
        ("perto_1.png", 1, None, None, False),
        ("perto_2.png", 1, None, None, False),
        ("perto_3.png", 1, None, None, False),
        ("perto_4.png", 1, None, None, False),
    ],
    "objetos/jogo/ilhas": [
        ("caco1.png", 1, 48, 48, False),
        ("caco2.png", 1, 48, 48, False),
        ("caco3.png", 1, 48, 48, False),
        ("bloco.png", 1, 48, 48, False),
        ("portal.png", 1, 96, 192, False),
        ("coluna_1_2f.png", 2, 48, 96, False),
        ("coluna_2_2f.png", 2, 48, 96, False),
        ("coluna_3_2f.png", 2, 48, 96, False),
        ("ponte_off_1.png", 1, 48, None, False),
        ("ponte_off_2.png", 1, 48, None, False),
        ("ponte_pronta.png", 1, 48, None, False),
        ("ponte_viva_3f.png", 3, 48, None, False),
        ("ponte_pilar.png", 1, None, None, False),
        ("chevron.png", 1, 32, 32, False),
    ],
    "objetos/cenario/ilhas": [
        ("astro_3f.png", 3, 44, 44, False),
        ("longe_1.png", 1, None, None, False),
        ("longe_2.png", 1, None, None, False),
        ("longe_3.png", 1, None, None, False),
        ("longe_4.png", 1, None, None, False),
        ("perto_1.png", 1, None, None, False),
        ("perto_2.png", 1, None, None, False),
        ("perto_3.png", 1, None, None, False),
    ] + [(f"nuvem_{i}.png", 1, None, None, False) for i in range(1, 11)],
    "objetos/jogo/eclipse": [
        ("caco1.png", 1, 48, 48, False),
        ("caco2.png", 1, 48, 48, False),
        ("caco3.png", 1, 48, 48, False),
        ("bloco.png", 1, 48, 48, False),
        ("portal.png", 1, 96, 192, False),
        ("chevron.png", 1, 32, 32, False),
        ("ponte_viva_4f.png", 4, 48, None, False),
    ] + [(f"coluna_{i}_2f.png", 2, 56, 96, False) for i in range(1, 6)]
      + [(f"ponte_pilar_{i}.png", 1, None, None, False) for i in range(1, 5)],
    "objetos/cenario/eclipse": [
        ("astro_3f.png", 3, 44, 44, False),
        ("longe_1.png", 1, None, None, False),
        ("longe_2.png", 1, None, None, False),
        ("longe_3.png", 1, None, None, False),
        ("longe_4.png", 1, None, None, False),
        ("perto_1.png", 1, None, None, False),
        ("perto_2.png", 1, None, None, False),
        ("perto_3.png", 1, None, None, False),
    ],
    "ui": [
        ("coracao_3f.png", 3, 40, 40, False),
        # letreiros e logo ficam no tamanho em que foram desenhados
        ("julgamento_perfeito.png", 1, None, None, False),
        ("julgamento_bom.png", 1, None, None, False),
        ("julgamento_erro.png", 1, None, None, False),
        ("nota_s.png", 1, 64, 64, False),
        ("nota_a.png", 1, 64, 64, False),
        ("nota_b.png", 1, 64, 64, False),
        ("nota_c.png", 1, 64, 64, False),
        ("emblema_bosque.png", 1, 96, 96, False),
        ("emblema_ilhas.png", 1, 96, 96, False),
        ("emblema_eclipse.png", 1, 96, 96, False),
        ("painel.png", 1, 48, 48, False),
        ("botao.png", 1, 48, 48, False),
        ("logo.png", 1, None, None, False),
    ],
    # o personagem vem no formato do gerador e e conferido a parte (PERSONAGEM)
}

# silhueta de cenario: altura aceitavel, ja na escala do buffer (320x180).
# O teto pega a arte exportada na escala da tela por engano (100+ px); nuvem
# baixa de 10 px e legitima, entao o piso e so contra arquivo vazio.
FAIXA_FUNDO = (4, 72)

# pecas que sao TILE SOLIDO ou EMENDAM com a vizinha: podem ser opacas de
# ponta a ponta (um bloco de canto reto preenche o tile inteiro)
EMENDAM = ("ponte_off", "ponte_pronta", "ponte_viva", "chao", "bloco")


def conferir(pasta, nome, quadros, cw, ch, cinza):
    caminho = os.path.join(DIR_ART, pasta, nome)
    parado = ""
    if not os.path.exists(caminho) and quadros > 1:
        # a versao parada tambem vale: a peca anima quando a arte animada vier
        caminho = os.path.join(DIR_ART, pasta, re.sub(r"_\d+f\.png$", ".png", nome))
        quadros, parado = 1, "  (parado; falta a tira de %d quadros)" % quadros
    if not os.path.exists(caminho):
        return "falta", "ainda desenhado por codigo"
    try:
        img = pygame.image.load(caminho)
    except pygame.error as erro:
        return "erro", f"nao abriu ({erro})"
    img = img.convert_alpha()
    w, h = img.get_size()

    if w % quadros:
        return "erro", f"largura {w} nao divide por {quadros} quadros"
    larg = w // quadros

    if cw is not None and ch is None and larg != cw:
        return "erro", f"largura {larg}, esperado {cw} (um tile)"
    if cw is not None and ch is not None and (larg, h) != (cw, ch):
        return "erro", f"celula {larg}x{h}, esperado {cw}x{ch}"
    if cw is None and pasta.startswith("objetos/cenario") and not FAIXA_FUNDO[0] <= h <= FAIXA_FUNDO[1]:
        return "erro", (f"altura {h} fora de {FAIXA_FUNDO[0]}-{FAIXA_FUNDO[1]} px "
                        "(silhueta de cenario vai na escala do buffer: divida por 4)")

    if not nome.startswith(EMENDAM) and not _tem_alpha(img):
        return "erro", "sem transparencia (exporte PNG com canal alfa)"
    if cinza and not _e_cinza(img):
        return "erro", "tem cor (objetos/jogo/ vai em branco e cinza: o codigo tinge)"
    return "ok", f"{larg}x{h}" + (f" x{quadros}q" if quadros > 1 else "") + parado


def _tem_alpha(img):
    for x in range(0, img.get_width(), 4):
        for y in range(0, img.get_height(), 4):
            if img.get_at((x, y)).a < 250:
                return True
    return False


def _e_cinza(img):
    for x in range(0, img.get_width(), 3):
        for y in range(0, img.get_height(), 3):
            c = img.get_at((x, y))
            if c.a > 8 and max(c.r, c.g, c.b) - min(c.r, c.g, c.b) > 12:
                return False
    return True


# animacao -> (arquivo ou pasta de quadros em personagens/, minimo de quadros)
PERSONAGEM = {
    "parado": ("east.png", 1),
    "corrida": ("Full_Sprint/east", 2),
    "pulo (o ultimo quadro e o pouso)": ("Running_Jump/east", 3),
}


def conferir_personagem():
    """O Leo no formato do gerador. Sem ele, o jogo usa a folha da Ozzbit."""
    base = os.path.join(DIR_ART, "personagens")
    for nome, (rel, minimo) in PERSONAGEM.items():
        caminho = os.path.join(base, rel)
        if os.path.isdir(caminho):
            n = len([a for a in os.listdir(caminho) if a.endswith(".png")])
        else:
            n = 1 if os.path.exists(caminho) else 0
        if n == 0:
            yield "falta", rel, "o jogo usa a folha da Ozzbit"
        elif n < minimo:
            yield "erro", rel, f"{n} quadro(s), precisa de pelo menos {minimo}"
        else:
            yield "ok", rel, f"{nome}: {n} quadro(s)"


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    total = {"ok": 0, "falta": 0, "erro": 0}
    for pasta, pecas in CONTRATO.items():
        print(f"\n\033[1massets/art/{pasta}/\033[0m")
        for nome, quadros, cw, ch, cinza in pecas:
            estado, detalhe = conferir(pasta, nome, quadros, cw, ch, cinza)
            total[estado] += 1
            marca = {"ok": "\033[32m ok \033[0m",
                     "falta": "\033[90m -- \033[0m",
                     "erro": "\033[31mERRO\033[0m"}[estado]
            print(f"  [{marca}] {nome:26} {detalhe}")
    print("\n\033[1massets/art/personagens/\033[0m")
    for estado, rel, detalhe in conferir_personagem():
        total[estado] += 1
        marca = {"ok": "\033[32m ok \033[0m", "falta": "\033[90m -- \033[0m",
                 "erro": "\033[31mERRO\033[0m"}[estado]
        print(f"  [{marca}] {rel:26} {detalhe}")
    print(f"\n{total['ok']} prontos, {total['falta']} faltando, {total['erro']} com erro")
    return 1 if total["erro"] else 0


if __name__ == "__main__":
    sys.exit(main())
