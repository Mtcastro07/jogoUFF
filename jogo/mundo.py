"""
Desenho do mundo da fase (chao, blocos, cacos, guias, enfeites e o
heroi) e a camera que o acompanha. So as colunas visiveis sao percorridas.
"""

import math
import random

import pygame

from . import arte, terreno
from .config import TILE, JOGADOR_TAM, LARGURA, ALTURA, FOLGA_CACO

ANCORA_X = 0.30       # Leo fica a 30% da largura da tela: o olhar vai para a frente
ANCORA_Y = 0.66       # e o chao a 66% da altura
POUSO_DURA = 0.07     # quanto tempo o quadro do pe tocando o chao fica na tela
ESTICA = 0.10         # quanto dura o esticar do corpo na saida do pulo
AMASSA = 0.12         # e o amassar no pouso
# chao desenhado por terreno.py: o caminho de lajes do bosque, ilhas de pedra
# flutuando e a alvenaria da cidadela
TERRENO_DESENHADO = {"bosque", "ilhas", "eclipse"}

# Mundos com o ambiente trabalhado: colunas recuadas para o fundo, blocos com
# sombra de contato e cacos sempre apoiados num leito, nunca soltos no ar.
# (tema -> cor para onde o cenario recua, quanto recua, cores do leito dos cacos)
AMBIENTE = {
    "bosque": ((24, 44, 48), 0.40, ((22, 44, 40), (66, 86, 82), (94, 114, 106))),
    "ilhas": ((118, 78, 112), 0.42, ((46, 33, 61), (69, 50, 87), (86, 66, 106))),
    "eclipse": ((26, 12, 44), 0.45, ((14, 6, 26), (28, 14, 46), (40, 24, 64))),
}
# no bosque o chao e terra firme: o leito dos cacos e o FUNDO de um fosso, que
# desce ate o pe da tela (nas ilhas e na cidadela e uma prateleira no ar)
FOSSO = {"bosque": terreno.fosso}
# O mapa muda de cara a cada parte da musica (fase.ato): introducao, A, B, A'.
# Quais enfeites (os numeros de enfeite_N.png) moram em cada ato...
ENFEITES_DO_ATO = {
    # a trilha (placa, cerca, lampiao) -> a mata -> as ruinas -> o santuario
    # (os cogumelos, 8, sairam: liam-se como o cogumelo que fere)
    "bosque": ((3, 7, 1), (1, 2, 7), (4, 5, 6), (6, 1, 5, 2, 3)),
    # os cristais -> os cataventos -> as ruinas e os baloes -> a festa das lanternas
    # (o cristal, 1, e o catavento de pontas, 4, sairam: pareciam perigo)
    "ilhas": ((6, 2), (6, 3), (2, 3, 5), (5, 3, 2)),
    # a muralha (tochas, estandartes) -> a guarda -> o patio das gargulas -> a catedral
    # (o braseiro, 3, e a gargula, 4, sairam: chama e chifres pareciam perigo)
    "eclipse": ((1, 2), (1, 2, 5), (7, 5, 6), (6, 7, 5, 2)),
}
# ...e quais desenhos de perigo (0 = o caco original, 1 e 2 = as variantes dele,
# 3 e 4 = os outros tipos). A introducao mostra so o perigo mais simples; a
# parte B troca de tipo; o final junta tudo. Todo desenho passou pelo robo em
# todos os perigos da fase, entao qualquer distribuicao continua justa.
CACOS_DO_ATO = {
    "bosque": ((0,), (0, 1, 2), (3, 4, 1), (0, 3, 4, 2)),
    "ilhas": ((0, 1), (0, 1, 2), (3, 4), (0, 1, 2, 3, 4)),
    "eclipse": ((0, 2), (0, 1, 2), (4, 3), (0, 1, 2, 3, 4)),
}
RAIO_AURA = 4         # o clarao em volta de cada perigo, em px
AFUNDA_ENFEITE = 6    # o enfeite miudo afunda menos: quase tudo dele e para ver
AFUNDA_COLUNA = 14    # a base da coluna fica atras da borda do chao: ela esta mais longe


class Camera:
    def __init__(self, fase):
        self.x = -LARGURA * ANCORA_X
        self.y = fase.chao_y - ALTURA * ANCORA_Y
        self.tremor = 0.0
        self.fixa = fase.alpha         # a versao alpha: camera sem tranco nem subida

    def sacudir(self, forca):
        if not self.fixa:
            self.tremor = max(self.tremor, forca)

    def seguir(self, fase, est, dt):
        """Segue o x do jogador na hora; em y acompanha o CHAO, nao o pulo."""
        self.x = est.x - LARGURA * ANCORA_X
        if self.fixa:
            return                     # na altura de sempre: a fase alpha e plana
        chao = fase.nivel_chao(int((est.x + JOGADOR_TAM) // TILE)) * TILE
        alvo = chao - ALTURA * ANCORA_Y
        # num salto de mola ou de orbe o Leo sobe muito: a camera sobe junto
        alvo = min(alvo, est.y - ALTURA * 0.24)
        self.y += (alvo - self.y) * min(1.0, dt * 5.0)
        self.tremor = max(0.0, self.tremor - dt * 40.0)

    def na_tela(self):
        """Posicao da camera com o tremor aplicado, em inteiros."""
        if self.tremor > 0.0:
            return (int(self.x + random.uniform(-self.tremor, self.tremor)),
                    int(self.y + random.uniform(-self.tremor, self.tremor)))
        return int(self.x), int(self.y)


def preparar(fase):
    """Faz de uma vez as contas que olham a fase inteira (terreno, leitos dos cacos)."""
    tema = fase.tema
    if tema.nome in TERRENO_DESENHADO:
        terreno.preparar(fase)
    if tema.nome in AMBIENTE:
        _leitos(fase)
    # os cacos (com volume e glitch) e o bloco prontos antes do 1o quadro: ler
    # arquivo e sombrear pixel a pixel no meio da musica daria um tranco
    _variar_cacos(fase)
    cor_aura = arte.clarear(tema.perigo, 0.3)
    for quantidade, variante in {(p.quantidade, p.variante) for p in fase.perigos}:
        for i in range(arte.QUADROS_GLITCH):
            arte.aura(arte.caco(quantidade, tema.perigo, i, tema.nome, variante), cor_aura, RAIO_AURA)
    # e a colisao de cada caco passa a ser a silhueta do desenho desta fase
    for p in fase.perigos:
        p.perfil = arte.perfil_caco(p.quantidade, tema.perigo, tema.nome, FOLGA_CACO, p.variante)
    for v in range(arte.variantes_bloco(tema.nome) if fase.blocos else 0):
        arte.bloco(tema.bloco, tema.chao_topo, tema.nome, v)
    amb = AMBIENTE.get(tema.nome)
    for d in fase.decos:
        if d.tipo == "portal":
            arte.portal(int(d.w), int(d.h), tema.destaque, 0, tema.nome)
        elif d.tipo == "arvore":
            _arvore(d, tema)
        elif d.tipo == "enfeite":
            for i in range(4):
                _enfeite(d, tema, i)
        else:
            for aceso in (False, True):
                img = arte.coluna(int(d.w), int(d.h), tema.bloco, tema.chao_topo, aceso,
                                  tema.nome, d.variante)
                if amb:
                    arte.recuar(img, amb[0], amb[1])


def variante_bloco(nome, tx):
    """Qual desenho o bloco da coluna `tx` usa: fixo pela posicao, a fase e sempre a mesma."""
    return (tx * 2654435761 >> 8) % arte.variantes_bloco(nome)


def _variar_cacos(fase):
    """
    Sorteia o desenho de cada caco entre as variantes que a fase tem. Cacos
    vizinhos (uma fileira no fundo de um fosso) saem todos iguais: o grupo e
    uma coisa so, e o sorteio e fixo pela posicao -- a fase e sempre a mesma.
    """
    nome = fase.tema.nome
    grupo = None
    anterior = None
    for p in sorted(fase.perigos, key=lambda p: (p.y, p.x)):
        if anterior is None or p.y != anterior.y or p.x - anterior.x > TILE:
            grupo = (int(p.x // TILE) * 2654435761 >> 9) & 0xFFFF
        anterior = p
        n = arte.variantes_caco(p.quantidade, nome)
        atos = CACOS_DO_ATO.get(nome)
        if atos:
            quais = [v for v in atos[min(fase.ato(p.x), len(atos) - 1)] if v < n] or [0]
            p.variante = quais[grupo % len(quais)]
        else:
            p.variante = grupo % n


def desenhar(tela, fase, est, cam_x, cam_y, pulso, espera=None, y_heroi=None, heroi=True,
             simples=False, rastro=()):
    """
    Desenha tudo que pertence a fase. `pulso` vai de 1 na batida a 0.
    `espera` e o tempo parado na largada: enquanto nao e None, Leo fica de pe.
    `y_heroi` e onde desenhar o Leo, se nao for o y da fisica (resgate suave).
    `heroi`: False quando quem desenha o Leo e a animacao da morte.
    `simples`: a versao alpha -- sem enfeites nem guias, chao liso e cacos parados.
    """
    tema = fase.tema
    c0 = int(cam_x // TILE) - 1
    c1 = int((cam_x + LARGURA) // TILE) + 2

    # enfeites ficam atras de tudo
    for d in fase.decos:
        if cam_x - d.w <= d.x <= cam_x + LARGURA and not (simples and d.tipo != "portal"):
            _desenhar_deco(tela, d, cam_x, cam_y, tema, pulso, 0.0 if simples else est.tempo,
                           None if simples else est.x)

    # chao: desenhado por terreno.py; sem estilo la (ou na alpha), o chao de sempre
    if tema.nome in TERRENO_DESENHADO and not simples:
        terreno.desenhar(tela, fase, cam_x, cam_y, c0, c1, est.tempo)
    else:
        _desenhar_chao(tela, fase, cam_x, cam_y, c0, c1)

    # os portais de velocidade ficam de pe no chao, atras do Leo
    for px, py, rapido in fase.portais:
        if cam_x - TILE <= px <= cam_x + LARGURA + TILE:
            img = arte.portal_velocidade(rapido, int(est.tempo * 12))
            tela.blit(img, (px - cam_x - img.get_width() // 2, py - cam_y - img.get_height() + 4))

    _desenhar_pontes(tela, fase, cam_x, cam_y, c0, c1)
    _desenhar_molas(tela, fase, est, cam_x, cam_y, pulso)

    amb = AMBIENTE.get(tema.nome)
    for tx, ty in fase.blocos:
        if c0 <= tx < c1 and (tx, ty) not in est.quebrados:
            bx, by = tx * TILE - cam_x, ty * TILE - cam_y
            if amb:
                _base_do_bloco(tela, fase, tx, ty, bx, by, amb)
            tela.blit(arte.bloco(tema.bloco, tema.chao_topo, tema.nome,
                                 0 if simples else variante_bloco(tema.nome, tx)), (bx, by))

    # o glitch dos cacos corre solto, FORA da grade: o perigo nunca pode
    # piscar na batida, ou vira uma pista falsa de tempo.
    q = 0 if simples else int(est.tempo * 12)
    cor_aura = arte.clarear(tema.perigo, 0.3)
    if amb:
        fosso = FOSSO.get(tema.nome)
        for (a, b, y) in _leitos(fase):
            if a * TILE < cam_x + LARGURA and b * TILE > cam_x:
                if fosso and not simples:
                    fosso(tela, a, b, y, cam_x, cam_y)
                else:
                    _desenhar_leito(tela, a, b, y, cam_x, cam_y, amb[2])
    for tx in range(c0, c1):
        for p in fase.col_perigos.get(tx, ()):
            # cada coluna com a sua defasagem: os glitches nunca batem juntos
            fase_glitch = 0 if simples else (tx * 2654435761 >> 11) % 16
            img = arte.caco(p.quantidade, tema.perigo, q + fase_glitch, tema.nome,
                            0 if simples else p.variante)
            if not simples:
                tela.blit(arte.aura(img, cor_aura, RAIO_AURA),
                          (p.x - cam_x - RAIO_AURA, p.y - cam_y - RAIO_AURA))
            tela.blit(img, (p.x - cam_x, p.y - cam_y))

    # guias de "pule aqui": so as que ainda estao a frente de Leo
    if simples:
        pulso = 0.0                                        # a alpha nao pulsa
    seta = arte.chevron(tema.destaque, 10 + int(6 * pulso), pulso > 0.5, tema.nome)
    guias = fase.guias and not simples                   # a alpha nao tem guias
    for mx, my in fase.marcas if guias else ():           # so no mundo que ensina
        if est.x - TILE <= mx <= cam_x + LARGURA:
            # ancorada pela PONTA: a guia fica no mesmo lugar qualquer que seja a arte
            tela.blit(seta, (mx - cam_x + TILE // 2 - seta.get_width() // 2,
                             my - 74 - seta.get_height() - int(8 * pulso) - cam_y))

    _desenhar_orbes(tela, fase, est, cam_x, cam_y, pulso)

    # o rastro da sequencia: os ultimos quadros do Leo, cada vez mais apagados
    for i, (q, qx, qy) in enumerate(rastro):
        tela.blit(arte.fantasma(q, 40 + 30 * i), (qx - cam_x, qy - cam_y))
    if heroi:
        _desenhar_heroi(tela, fase, est, cam_x, cam_y, espera, est.y if y_heroi is None else y_heroi)


_BRILHOS = {}
_PECAS = {}


def _laje(tema, esq, dir_):
    """Um tile de passarela: uma laje fina, clara em cima, com as pontas fechadas."""
    chave = ("laje", tema.nome, esq, dir_)
    if chave not in _PECAS:
        img = pygame.Surface((TILE, 20), pygame.SRCALPHA)
        corpo = arte.clarear(tema.bloco, 0.12)
        a = 3 if esq else 0
        b = TILE - (3 if dir_ else 0)
        pygame.draw.rect(img, arte.escurecer(tema.bloco, 0.6), (a, 0, b - a, 17))
        pygame.draw.rect(img, corpo, (a + (3 if esq else 0), 3, b - a - (3 if esq else 0) - (3 if dir_ else 0), 11))
        pygame.draw.rect(img, tema.chao_topo, (a, 0, b - a, 6))
        pygame.draw.rect(img, arte.clarear(tema.chao_topo, 0.6), (a, 0, b - a, 3))
        for x in range(a + 9, b - 6, 15):                 # as juntas da laje
            pygame.draw.rect(img, arte.escurecer(tema.bloco, 0.6), (x, 6, 3, 6))
        if esq or dir_:                                   # o tirante que a segura
            pygame.draw.rect(img, arte.escurecer(tema.bloco, 0.6), (a + 3 if esq else b - 9, 14, 6, 6))
        _PECAS[chave] = img
    return _PECAS[chave]


def _desenhar_pontes(tela, fase, cam_x, cam_y, c0, c1):
    """As passarelas no ar (so seguram quem vem de cima: sao finas, nao um muro)."""
    for tx in range(c0, c1):
        for ty in fase.pontes_col.get(tx, ()):
            img = _laje(fase.tema, (tx - 1, ty) not in fase.pontes, (tx + 1, ty) not in fase.pontes)
            tela.blit(_sombra(TILE, 6, 60), (tx * TILE - cam_x, ty * TILE - cam_y + 18))
            tela.blit(img, (tx * TILE - cam_x, ty * TILE - cam_y))


def _seta_cima(cor, u=3):
    """Uma seta para cima em pixels grandes: o sinal da mola."""
    chave = ("seta", cor, u)
    if chave not in _PECAS:
        img = pygame.Surface((7 * u, 4 * u), pygame.SRCALPHA)
        for y in range(4):
            for x in (3 - y, 3 + y):
                img.fill(cor, (x * u, y * u, u, u))
                if y:
                    img.fill(cor, (x * u, (y - 1) * u, u, u))
        _PECAS[chave] = img
    return _PECAS[chave]


def _desenhar_molas(tela, fase, est, cam_x, cam_y, pulso):
    """
    A mola: uma placa de luz no chao, com setas subindo. Ela marca o tempo
    (pulsa na batida): e um convite, nao um perigo.
    """
    cor = fase.tema.destaque
    clara = arte.clarear(cor, 0.6)
    for x0, x1, y in fase.molas:
        a, b = x0 + 8 - cam_x, x1 + JOGADOR_TAM - 8 - cam_x
        if b < 0 or a > LARGURA:
            continue
        sy = y - cam_y
        larg = int(b - a)
        alto = 8 + int(4 * pulso)
        pygame.draw.rect(tela, arte.escurecer(cor, 0.5), (a - 3, sy - alto - 3, larg + 6, alto + 6))
        pygame.draw.rect(tela, cor, (a, sy - alto, larg, alto))
        pygame.draw.rect(tela, (255, 255, 255), (a, sy - alto, larg, 3))
        # as setas sobem sem parar por cima da placa
        seta = _seta_cima(clara)
        n = max(2, larg // 44)
        for k in range(n):
            cx = a + (k + 0.5) * larg / n
            for passo in range(3):
                sobe = (est.tempo * 60.0 + passo * 16) % 48
                img = arte.fantasma(seta, int(255 * (1.0 - sobe / 48.0)) // 32 * 32 + 31)
                tela.blit(img, (cx - seta.get_width() // 2, sy - alto - 14 - sobe))


def _anel(cor, raio, grosso):
    chave = ("anel", cor, raio, grosso)
    if chave not in _PECAS:
        u = 3
        n = raio * 2 + 3
        img = pygame.Surface((n * u, n * u), pygame.SRCALPHA)
        c = n // 2
        for y in range(n):
            for x in range(n):
                d = math.hypot(x - c, y - c)
                if raio - grosso < d <= raio + 0.3:
                    img.fill(cor, (x * u, y * u, u, u))
                elif d <= raio - grosso - 2:
                    img.fill((255, 255, 255) if d <= 1.5 else arte.clarear(cor, 0.5),
                             (x * u, y * u, u, u))
        _PECAS[chave] = arte.aura(img, cor, 4)
    return _PECAS[chave]


def _desenhar_orbes(tela, fase, est, cam_x, cam_y, pulso):
    """O orbe: um anel de luz no ar, que respira na batida; usado, ele se apaga."""
    cor = fase.tema.destaque
    for i, (ox, oy, _, _) in enumerate(fase.orbes):
        if not cam_x - TILE * 2 <= ox <= cam_x + LARGURA + TILE * 2:
            continue
        if i in est.orbes:
            img = arte.fantasma(_anel(arte.escurecer(cor, 0.4), 5, 1), 96)
        else:
            img = _anel(cor, 6 if pulso > 0.5 else 5, 2)
        tela.blit(img, (ox - cam_x - img.get_width() // 2, oy - cam_y - img.get_height() // 2))


def _brilho(cor, alto, quadro):
    """O eco no ar: um losango de luz que cintila (o alto tem um anel em volta)."""
    chave = (cor, alto, quadro)
    if chave not in _BRILHOS:
        u = 3
        img = pygame.Surface((11 * u, 11 * u), pygame.SRCALPHA)
        def ponto(x, y, c):
            img.fill(c, (x * u, y * u, u, u))
        raio = 3 if quadro != 1 else 2
        for y in range(-raio, raio + 1):
            for x in range(-raio, raio + 1):
                d = abs(x) + abs(y)
                if d <= raio:
                    c = (255, 255, 255) if d <= raio - 2 else cor if d < raio else arte.escurecer(cor, 0.45)
                    ponto(5 + x, 5 + y, c)
        if quadro == 2:                                   # a cintilada: quatro pontas
            for dx, dy in ((0, -5), (0, 5), (-5, 0), (5, 0)):
                ponto(5 + dx, 5 + dy, (255, 255, 255))
        if alto:
            for dx, dy in ((-4, -2), (4, -2), (-4, 2), (4, 2), (-2, -4), (2, -4), (-2, 4), (2, 4)):
                ponto(5 + dx, 5 + dy, arte.clarear(cor, 0.35))
        # um halo na cor do mundo: de longe ele se le como coisa de pegar, nao como estrela
        _BRILHOS[chave] = arte.aura(img, cor, 4)
    return _BRILHOS[chave]


def icone_eco(cor):
    """O losango do eco, parado: o icone da conta no HUD."""
    return _brilho(cor, False, 0)


def desenhar_brilhos(tela, fase, cam_x, cam_y, pegos, tempo):
    """Os ecos que ainda estao no ar, subindo e descendo devagar (fora da batida)."""
    cor = fase.tema.destaque
    for i, (x, y, alto) in enumerate(fase.brilhos):
        if x < cam_x - TILE:
            continue
        if x > cam_x + LARGURA + TILE:
            break
        if i in pegos:
            continue
        quadro = (int(tempo * 6) + i * 3) % 8
        img = _brilho(cor, alto, 2 if quadro == 0 else 1 if quadro == 4 else 0)
        dy = math.sin(tempo * 3.0 + i * 1.7) * 3.0
        tela.blit(img, (x - cam_x - img.get_width() // 2,
                        y - JOGADOR_TAM * 0.5 - cam_y - img.get_height() // 2 + dy))


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


def _arvore(d, tema):
    """A arvore do bosque, puxada para a cor do fundo: e cenario, nao obstaculo."""
    amb = AMBIENTE[tema.nome]
    return arte.recuar(arte.arvore(d.variante), amb[0], amb[1])


def _enfeite(d, tema, i):
    """O enfeite, um pouco puxado para a cor do fundo (menos que as colunas: e miudo)."""
    atos = ENFEITES_DO_ATO.get(tema.nome)
    img = None
    if atos and d.ato is not None:
        quais = atos[min(d.ato, len(atos) - 1)]
        img = arte.enfeite_numero(tema.nome, quais[d.variante % len(quais)], i)
    if img is None:
        img = arte.enfeite(tema.nome, d.variante, i)
    amb = AMBIENTE.get(tema.nome)
    if img is None or not amb:
        return img
    # bem recuado: o que brilha e tem cor viva no caminho e so o que importa
    return arte.recuar(img, amb[0], amb[1] * 0.85)


ACORDA = 7 * TILE     # a que distancia, a frente do Leo, o enfeite animado acorda
_pocas = {}


def _poca(cor, larg):
    """A luz que um enfeite aceso joga no chao: uma elipse macia, somada a cena."""
    chave = (cor, larg)
    if chave not in _pocas:
        s = pygame.Surface((larg, 22))
        for i, k in enumerate((0.10, 0.18, 0.28)):
            pygame.draw.ellipse(s, tuple(int(c * k) for c in cor),
                                (i * larg // 8, i * 3, larg - i * larg // 4, 22 - i * 6))
        _pocas[chave] = s
    return _pocas[chave]


def _desenhar_deco(tela, d, cam_x, cam_y, tema, pulso, tempo, leo_x=None):
    x, y = d.x - cam_x, d.y - cam_y
    if d.tipo == "arvore":
        # de pe atras do caminho, com o pe escondido pela borda do chao
        img = _arvore(d, tema)
        tela.blit(img, (x + (d.w - img.get_width()) // 2,
                        y + d.h - img.get_height() + AFUNDA_COLUNA))
    elif d.tipo == "coluna":
        # a coluna acende NA batida: e a antecipacao visual que o jogo ensina.
        # A arte pode ser menor que a caixa: fica de pe no pe da caixa, centrada.
        img = arte.coluna(int(d.w), int(d.h), tema.bloco, tema.chao_topo, pulso > 0.5,
                          tema.nome, d.variante)
        amb = AMBIENTE.get(tema.nome)
        desce = 0
        if amb:
            # ruina ao fundo: puxada para a cor do ceu e com o pe atras da borda
            # do chao, para nao parecer um objeto solido no caminho do jogador
            img = arte.recuar(img, amb[0], amb[1])
            desce = AFUNDA_COLUNA
        tela.blit(img, (x + (d.w - img.get_width()) // 2, y + d.h - img.get_height() + desce))
    elif d.tipo == "enfeite":
        # miudezas de pe atras do caminho; as animadas (chama, lanterna) correm
        # soltas da batida -- so a coluna marca o tempo
        # O mundo acorda com a musica: o que tem luz (lampiao, tocha, lanterna)
        # dorme apagado e parado, e acende quando o Leo chega perto.
        img = _enfeite(d, tema, int(tempo * 7) + d.variante)
        if img is not None:
            vivo = _enfeite(d, tema, 1) is not _enfeite(d, tema, 0)     # tem mais de um quadro
            acordou = leo_x is None or d.x < leo_x + ACORDA
            pe = y + d.h + AFUNDA_ENFEITE
            ex = x + (d.w - img.get_width()) // 2
            if leo_x is not None:
                tela.blit(_sombra(max(20, img.get_width() - 8), 8, 80),
                          (ex + 4, pe - AFUNDA_ENFEITE - 4))
            if vivo and not acordou:
                img = arte.recuar(_enfeite(d, tema, 0), (10, 8, 22), 0.5)
            tela.blit(img, (ex, pe - img.get_height()))
            if vivo and acordou and leo_x is not None:
                perto = 1.0 - min(1.0, max(0.0, (leo_x + ACORDA - d.x) / (TILE * 1.5)))
                larg = 96 + int(40 * perto)            # acabou de acender: a luz estoura
                tela.blit(_poca(tema.destaque, larg),
                          (x + d.w // 2 - larg // 2, pe - AFUNDA_ENFEITE - 12),
                          special_flags=pygame.BLEND_RGB_ADD)
    else:   # portal
        img = arte.portal(int(d.w), int(d.h), tema.destaque, int(tempo * 8), tema.nome)
        tela.blit(img, (x + (d.w - img.get_width()) // 2, y + d.h - img.get_height()))
        if not arte.tem_peca("portal", tema.nome):
            # o anel que respira e do portal desenhado por codigo; o sprite tem o dele
            pygame.draw.ellipse(tela, arte.clarear(tema.destaque, 0.5),
                                (x + d.w * 0.35, y + d.h * 0.35, d.w * 0.3, d.h * 0.3),
                                2 + int(3 * pulso))


def _pose(fase, est, espera):
    """(animacao, quadro) do Leo agora."""
    batidas = est.tempo / fase.dur_batida
    if espera is not None:
        return "parado", espera * 6              # na largada, esperando o toque
    if not est.no_chao:
        # cada quadro do ar cobre uma faixa da velocidade vertical
        return arte.quadro_no_ar(est.vy, fase.v_pulo, est.tempo)
    if arte.TEM_POUSO and est.tempo - est.pouso < POUSO_DURA:
        return "pouso", 0                        # o pe acabou de tocar o chao
    # a corrida no compasso: um ciclo inteiro por batida, com quantos quadros a
    # animacao tiver -- o quadro 0 cai sempre em cima da batida
    return "corre", batidas * arte.n_quadros("corre")


def sprite_heroi(fase, est, y):
    """(quadro, x, y): o Leo como ele esta desenhado agora, com o canto no mundo."""
    anim, i = _pose(fase, est, None)
    q, ax, ay = arte.heroi(anim, i, _elastico(est, None))
    return q, int(est.x + JOGADOR_TAM * 0.5 - ax), int(y + JOGADOR_TAM - ay)


def _desenhar_heroi(tela, fase, est, cam_x, cam_y, espera, y):
    if est.vivo and est.invuln > 0.0 and int(est.tempo * 20) % 2 == 0:
        return                                   # piscando
    anim, i = _pose(fase, est, espera)
    cx = est.x + JOGADOR_TAM * 0.5 - cam_x
    pes = y + JOGADOR_TAM - cam_y
    # sombra no chao: e ela que diz a que altura Leo esta (a alpha nao tem)
    chao = fase.chao_col.get(int((est.x + JOGADOR_TAM * 0.5) // TILE))
    if chao is not None and y + JOGADOR_TAM <= chao * TILE + 1 and not fase.alpha:
        dist = min(1.0, max(0.0, (chao * TILE - y - JOGADOR_TAM) / (TILE * 4)))
        larg = int(JOGADOR_TAM * (1.1 - 0.5 * dist))
        sombra = pygame.Surface((larg, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, int(120 * (1 - dist * 0.6))), (0, 0, larg, 8))
        tela.blit(sombra, (cx - larg // 2, chao * TILE - cam_y - 4))
    arte.desenhar_heroi(tela, anim, i, cx, pes, _elastico(est, espera))


def _elastico(est, espera):
    """
    Esticar e amassar: o corpo estica na saida do pulo e amassa no pouso, e
    volta ao normal em uma fracao de segundo. Em degraus de 5%, para caber
    no cache de quadros ja escalados.
    """
    if espera is not None:
        return (1.0, 1.0)
    t = est.tempo - est.pulo
    if 0.0 <= t < ESTICA and not est.no_chao:
        k = 1.0 - t / ESTICA
        sx, sy = 1.0 - 0.14 * k, 1.0 + 0.16 * k
    else:
        t = est.tempo - est.pouso
        if not (0.0 <= t < AMASSA) or not est.no_chao:
            return (1.0, 1.0)
        k = 1.0 - t / AMASSA
        sx, sy = 1.0 + 0.16 * k, 1.0 - 0.14 * k
    return (round(sx * 20) / 20, round(sy * 20) / 20)


# ---------------------------------------------------------------- ambiente
_sombras = {}


def _sombra(larg, alto, alfa):
    chave = (larg, alto, alfa)
    if chave not in _sombras:
        s = pygame.Surface((larg, alto), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, alfa), (0, 0, larg, alto))
        _sombras[chave] = s
    return _sombras[chave]


def _base_do_bloco(tela, fase, tx, ty, bx, by, amb):
    """Sombra de contato e um pouco de cascalho: o bloco esta no chao, nao colado."""
    chao = fase.chao_col.get(tx)
    if chao is None or chao != ty + 1:
        return
    tela.blit(_sombra(TILE + 16, 10, 120), (bx - 8, by + TILE - 5))
    escura, media, clara = amb[2]
    for k, (dx, cor) in enumerate(((-7, media), (-3, clara), (TILE + 2, media), (TILE - 1, escura))):
        if (tx * 7 + k * 3) % 4 != 0:                       # nem todo bloco tem todas
            tela.fill(cor, (bx + dx, by + TILE - 4, 4, 4))


_cache_leitos = {}


def _leitos(fase):
    """
    [(tx0, tx1, y)]: faixas de cacos que nao estao em cima de chao nenhum (no
    fundo de uma fenda). Cada faixa ganha um leito de
    rocha: caco solto no ar e o que mais parece erro no quadro.
    """
    if fase.ident not in _cache_leitos:
        soltos = sorted({(int(p.x // TILE), int((p.y + p.h) // TILE)) for p in fase.perigos
                         if (int(p.x // TILE), int((p.y + p.h) // TILE)) not in fase.solidos},
                        key=lambda t: (t[1], t[0]))
        faixas = []
        for tx, ty in soltos:
            if faixas and faixas[-1][2] == ty * TILE and faixas[-1][1] == tx:
                faixas[-1][1] = tx + 1
            else:
                faixas.append([tx, tx + 1, ty * TILE])
        _cache_leitos[fase.ident] = [tuple(f) for f in faixas]
    return _cache_leitos[fase.ident]


def _desenhar_leito(tela, a, b, y, cam_x, cam_y, cores):
    """Uma prateleira de rocha sob os cacos: topo reto, fundo irregular."""
    escura, media, clara = cores
    x0, x1 = a * TILE - 6, b * TILE + 6
    sy = y - cam_y
    for x in range(int(x0), int(x1), 4):
        fundo = 10 + ((x * 7919) >> 3) % 3 * 4             # 10, 14 ou 18 px de espessura
        tela.fill(media, (x - cam_x, sy, 4, fundo))
        tela.fill(escura, (x - cam_x, sy + fundo - 4, 4, 4))
    tela.fill(clara, (x0 - cam_x, sy, x1 - x0, 2))

