"""
Desenho do mundo da fase (chao, blocos, cacos, pontes, guias, enfeites e o
heroi) e a camera que o acompanha. So as colunas visiveis sao percorridas.
"""

import random

import pygame

from . import arte, terreno
from .config import TILE, JOGADOR_TAM, LARGURA, ALTURA, BRANCO

ANCORA_X = 0.30       # Leo fica a 30% da largura da tela: o olhar vai para a frente
ANCORA_Y = 0.66       # e o chao a 66% da altura
POUSO_DURA = 0.08     # quanto tempo o quadro do pe tocando o chao fica na tela
# nas Ilhas Suspensas o chao e desenhado como ilhas de pedra flutuando (terreno.py)
TERRENO_FLUTUANTE = {"ilhas"}


class Camera:
    def __init__(self, fase):
        self.x = -LARGURA * ANCORA_X
        self.y = fase.chao_y - ALTURA * ANCORA_Y
        self.tremor = 0.0

    def sacudir(self, forca):
        self.tremor = max(self.tremor, forca)

    def seguir(self, fase, est, dt):
        """Segue o x do jogador na hora; em y acompanha o CHAO, nao o pulo."""
        self.x = est.x - LARGURA * ANCORA_X
        chao = fase.nivel_chao(int((est.x + JOGADOR_TAM) // TILE)) * TILE
        alvo = chao - ALTURA * ANCORA_Y
        self.y += (alvo - self.y) * min(1.0, dt * 5.0)
        self.tremor = max(0.0, self.tremor - dt * 40.0)

    def na_tela(self):
        """Posicao da camera com o tremor aplicado, em inteiros."""
        if self.tremor > 0.0:
            return (int(self.x + random.uniform(-self.tremor, self.tremor)),
                    int(self.y + random.uniform(-self.tremor, self.tremor)))
        return int(self.x), int(self.y)


def desenhar(tela, fase, est, cam_x, cam_y, pulso, espera=None):
    """
    Desenha tudo que pertence a fase. `pulso` vai de 1 na batida a 0.
    `espera` e o tempo parado na largada: enquanto nao e None, Leo fica de pe.
    """
    tema = fase.tema
    c0 = int(cam_x // TILE) - 1
    c1 = int((cam_x + LARGURA) // TILE) + 2

    # enfeites ficam atras de tudo
    for d in fase.decos:
        if cam_x - d.w <= d.x <= cam_x + LARGURA:
            _desenhar_deco(tela, d, cam_x, cam_y, tema, pulso, est.tempo)

    # chao: nas ilhas, ilhas de pedra flutuando; nas outras, o chao de sempre
    if tema.nome in TERRENO_FLUTUANTE:
        terreno.desenhar(tela, fase, cam_x, cam_y, c0, c1)
    else:
        _desenhar_chao(tela, fase, cam_x, cam_y, c0, c1)

    for tx, ty in fase.blocos:
        if c0 <= tx < c1:
            tela.blit(arte.bloco(tema.bloco, tema.chao_topo, tema.nome),
                      (tx * TILE - cam_x, ty * TILE - cam_y))

    for k, p in enumerate(fase.pontes):
        if p.x0 <= cam_x + LARGURA and p.x1 >= cam_x:
            _desenhar_ponte(tela, p, est, cam_x, cam_y, tema, pulso, k)

    # o glitch dos cacos corre solto, FORA da grade: o perigo nunca pode
    # piscar na batida, ou vira uma pista falsa de tempo.
    q = int(est.tempo * 12)
    for tx in range(c0, c1):
        for p in fase.col_perigos.get(tx, ()):
            tela.blit(arte.caco(p.quantidade, tema.perigo, q, tema.nome),
                      (p.x - cam_x, p.y - cam_y))

    # guias de "pule aqui": so as que ainda estao a frente de Leo
    seta = arte.chevron(tema.destaque, 10 + int(6 * pulso), pulso > 0.5, tema.nome)
    for mx, my in fase.marcas:
        if est.x - TILE <= mx <= cam_x + LARGURA:
            # ancorada pela PONTA: a guia fica no mesmo lugar qualquer que seja a arte
            tela.blit(seta, (mx - cam_x + TILE // 2 - seta.get_width() // 2,
                             my - 74 - seta.get_height() - int(8 * pulso) - cam_y))

    _desenhar_heroi(tela, fase, est, cam_x, cam_y, espera)


def _desenhar_chao(tela, fase, cam_x, cam_y, c0, c1):
    """O chao de uma coluna de cada vez, da linha do topo ate o pe da tela."""
    tema = fase.tema
    chao = fase.chao_col
    topo = arte.chao(tema.nome)
    for tx in range(c0, c1):
        n = chao.get(tx)
        if n is None:
            continue
        sx, sy = tx * TILE - cam_x, n * TILE - cam_y
        if sy < ALTURA:
            pygame.draw.rect(tela, tema.chao, (sx, sy, TILE, ALTURA - sy))
            if topo is not None:
                tela.blit(topo, (sx, sy))
            # a linha clara fica mesmo com a arte: e ela que o olho segue
            pygame.draw.rect(tela, tema.chao_topo, (sx, sy, TILE, 6 if topo is None else 3))
            # onde o chao termina ou desce, uma borda mostra a queda
            for viz, bx in ((chao.get(tx - 1), sx), (chao.get(tx + 1), sx + TILE - 4)):
                if viz is None or viz > n:
                    pygame.draw.rect(tela, tema.chao_topo, (bx, sy, 4, min(TILE * 3, ALTURA - sy)))


def _desenhar_ponte(tela, p, est, cam_x, cam_y, tema, pulso, indice=0):
    y = p.y - cam_y - 4
    viva = est.ponte is p and est.sustentando
    estado = "viva" if viva else "pronta" if est.ponte is p else "off"
    q = int(est.tempo * 10)
    seg = arte.ponte(estado, tema.destaque, q, tema.nome)
    if seg is not None:
        # a tabua tem o topo na linha do chao (os pes pisam nela); a faixa de luz
        # e centrada na linha, como a ponte desenhada por codigo
        topo = p.y - cam_y - (seg.get_height() // 2 if viva else 0)
        for k, x in enumerate(range(int(p.x0), int(p.x1), seg.get_width())):
            s = arte.ponte(estado, tema.destaque, q, tema.nome, k)
            # fora da nota a tabua e um FANTASMA: se parecesse chao firme, o
            # jogador nao seguraria o botao. So a nota sustentada e solida.
            if not viva:
                s = arte.fantasma(s, 150 if estado == "pronta" else 110)
            larg = min(s.get_width(), int(p.x1) - x)
            tela.blit(s, (x - cam_x, topo), (0, 0, larg, s.get_height()))
    elif viva:
        # a nota longa esta viva: a ponte vira uma faixa de luz solida
        pygame.draw.rect(tela, tema.destaque, (p.x0 - cam_x, y, p.x1 - p.x0, 8))
        pygame.draw.rect(tela, BRANCO, (p.x0 - cam_x, y + 2, p.x1 - p.x0, 3))
    else:
        cor = arte.escurecer(tema.destaque, 0.35 if est.ponte is p else 0.6)
        for x in range(int(p.x0), int(p.x1), 24):
            pygame.draw.rect(tela, cor, (x - cam_x, y + 2, 12, 4))
    # os dois pilares que emolduram o vao, de pe na beirada do chao
    if arte.ponte_pilar(tema.chao_topo, tema.nome) is not None:
        # havendo varios desenhos de pilar, cada lado de cada ponte ganha o seu
        for lado, cx in enumerate((p.x0 - 6, p.x1 + 6)):
            pilar = arte.ponte_pilar(tema.chao_topo, tema.nome, indice * 2 + lado)
            tela.blit(pilar, (cx - cam_x - pilar.get_width() // 2, p.y - cam_y - pilar.get_height()))
    else:
        for x in (p.x0 - 10, p.x1 + 2):
            pygame.draw.rect(tela, tema.chao_topo, (x - cam_x, y - 40, 8, 48))


def _desenhar_deco(tela, d, cam_x, cam_y, tema, pulso, tempo):
    x, y = d.x - cam_x, d.y - cam_y
    if d.tipo == "coluna":
        # a coluna acende NA batida: e a antecipacao visual que o jogo ensina.
        # A arte pode ser menor que a caixa: fica de pe no pe da caixa, centrada.
        img = arte.coluna(int(d.w), int(d.h), tema.bloco, tema.chao_topo, pulso > 0.5,
                          tema.nome, d.variante)
        tela.blit(img, (x + (d.w - img.get_width()) // 2, y + d.h - img.get_height()))
    else:   # portal
        img = arte.portal(int(d.w), int(d.h), tema.destaque, int(tempo * 8), tema.nome)
        tela.blit(img, (x + (d.w - img.get_width()) // 2, y + d.h - img.get_height()))
        if not arte.tem_peca("portal", tema.nome):
            # o anel que respira e do portal desenhado por codigo; o sprite tem o dele
            pygame.draw.ellipse(tela, arte.clarear(tema.destaque, 0.5),
                                (x + d.w * 0.35, y + d.h * 0.35, d.w * 0.3, d.h * 0.3),
                                2 + int(3 * pulso))


def _desenhar_heroi(tela, fase, est, cam_x, cam_y, espera):
    if est.invuln > 0.0 and int(est.tempo * 20) % 2 == 0:
        return                                   # piscando
    batidas = est.tempo / fase.dur_batida
    if espera is not None:
        anim, i = "parado", espera * 6           # na largada, esperando o toque
    elif est.sustentando:
        anim, i = "segura", (batidas * arte.n_quadros("segura") if arte.SEGURA_CORRE
                             else est.tempo * 6)
    elif not est.no_chao:
        # cada quadro do pulo cobre uma faixa da velocidade vertical
        k = (est.vy + fase.v_pulo) / (2.0 * fase.v_pulo)     # 0 subindo, 1 caindo
        anim, i = "pula", arte.quadro_do_pulo(k)
    elif arte.TEM_POUSO and est.tempo - est.pouso < POUSO_DURA:
        anim, i = "pouso", 0                     # o pe acabou de tocar o chao
    else:
        # a corrida no compasso: um ciclo inteiro por batida, com quantos
        # quadros a animacao tiver -- o quadro 0 cai sempre em cima da batida
        anim, i = "corre", batidas * arte.n_quadros("corre")
    cx = est.x + JOGADOR_TAM * 0.5 - cam_x
    pes = est.y + JOGADOR_TAM - cam_y
    # sombra no chao: e ela que diz a que altura Leo esta
    chao = fase.chao_col.get(int((est.x + JOGADOR_TAM * 0.5) // TILE))
    if chao is not None:
        dist = min(1.0, max(0.0, (chao * TILE - est.y - JOGADOR_TAM) / (TILE * 4)))
        larg = int(JOGADOR_TAM * (1.1 - 0.5 * dist))
        sombra = pygame.Surface((larg, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, int(120 * (1 - dist * 0.6))), (0, 0, larg, 8))
        tela.blit(sombra, (cx - larg // 2, chao * TILE - cam_y - 4))
    arte.desenhar_heroi(tela, anim, i, cx, pes)
