"""
Renderiza o trailer do jogo: o jogo de verdade rodando sem janela, com um robo
tocando no tempo das partituras, e cada quadro indo para o ffmpeg.

    ./.venv/bin/python ferramentas/trailer.py [saida.mp4]

Segue o roteiro de estudo_direcao_trailer.md (gancho, premissa, escalada, crise,
climax e assinatura). Os cortes sao contados em batidas da musica de cada mundo,
e a trilha de cada plano e o mesmo trecho da faixa que a fase toca ali -- por
isso os pulos caem na batida. Os efeitos sonoros de trailer (riser, boom,
whoosh, coracao) sao sintetizados aqui mesmo. Precisa do ffmpeg no PATH.
"""

import array
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import wave

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.dont_write_bytecode = True

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame

import main
from jogo import fases, menus, mundo, ui, partida as P
from jogo.audio import audio, TRILHAS
from jogo.config import (LARGURA as W, ALTURA as H, PASSO_FISICA, DIR_MUSICA, DIR_SFX,
                         BRANCO, AMARELO, VERMELHO, VERDE, AZUL, ROXO, CONTORNO)
from jogo.save import save

FPS = 60
DT = 1.0 / FPS
TAXA = 44100
BARRA = int((H - W / 2.39) / 2)            # faixa preta do formato de cinema
LEO = (int(W * mundo.ANCORA_X) + 16, 430)  # onde o Leo fica na tela: o centro dos zooms
rnd = random.Random(7)


# ------------------------------------------------------------------- o som
class Som:
    """A trilha do trailer: trechos das musicas (ffmpeg corta) e efeitos (somados aqui)."""

    def __init__(self):
        self.musicas = []          # (cancao, inicio na faixa, duracao, instante no video, volume, fade)
        self.fx = array.array("f")
        self.jogo = {}
        for nome in ("pulo", "perfeito", "bom", "erro", "quebra", "vitoria", "morte"):
            with wave.open(os.path.join(DIR_SFX, f"{nome}.wav")) as w:
                bruto = array.array("h", w.readframes(w.getnframes()))
            self.jogo[nome] = [v / 32768.0 for v in bruto]

    def musica(self, cancao, tempo_fase, dur, t, vol=1.0, sai=0.03):
        self.musicas.append((cancao, TRILHAS[cancao].inicio + tempo_fase, dur, t, vol, sai))

    def somar(self, amostras, t, vol=1.0):
        i0 = int(t * TAXA)
        if len(self.fx) < i0 + len(amostras):
            self.fx.extend([0.0] * (i0 + len(amostras) - len(self.fx)))
        fx = self.fx
        for i, v in enumerate(amostras):
            fx[i0 + i] += v * vol

    def do_jogo(self, nome, t):
        if nome in self.jogo:
            self.somar(self.jogo[nome], t, {"pulo": 0.22, "perfeito": 0.3, "bom": 0.3}.get(nome, 0.5))

    def gravar(self, caminho, dur):
        n = int(dur * TAXA)
        self.fx.extend([0.0] * max(0, n - len(self.fx)))
        with wave.open(caminho, "w") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(TAXA)
            w.writeframes(array.array("h", (max(-32767, min(32767, int(v * 32767))) for v in self.fx[:n])).tobytes())


def riser(dur):
    fase, s = 0.0, []
    for i in range(int(dur * TAXA)):
        k = i / (dur * TAXA)
        fase += math.tau * (180 + 1500 * k * k) / TAXA
        s.append((rnd.uniform(-1, 1) * 0.30 * k * k + math.sin(fase) * 0.22 * k) * min(1.0, (1 - k) * 60))
    return s


def boom(dur=1.5):
    fase, s = 0.0, []
    for i in range(int(dur * TAXA)):
        t = i / TAXA
        fase += math.tau * (38 + 72 * math.exp(-t * 7)) / TAXA
        s.append(math.sin(fase) * math.exp(-t * 3.0) * 0.95 + (rnd.uniform(-1, 1) * 0.5 if t < 0.012 else 0.0))
    return s


def whoosh(dur=0.3):
    y, s = 0.0, []
    for i in range(int(dur * TAXA)):
        k = i / (dur * TAXA)
        y += (rnd.uniform(-1, 1) - y) * (0.05 + 0.5 * k)
        s.append(y * math.sin(math.pi * k) ** 2 * 0.7)
    return s


def coracao():
    s = [0.0] * int(0.6 * TAXA)
    for inicio, forca in ((0.0, 1.0), (0.26, 0.7)):
        for i in range(int(0.3 * TAXA)):
            t = i / TAXA
            s[int(inicio * TAXA) + i] += math.sin(math.tau * 52 * t) * math.exp(-t * 16) * forca * 0.9
    return s


def tique():
    return [(rnd.uniform(-1, 1) * 0.5 + math.sin(math.tau * 1900 * i / TAXA) * 0.4) * math.exp(-i / TAXA * 420) * 0.5
            for i in range(int(0.03 * TAXA))]


def zumbido(dur):
    return [(math.sin(math.tau * 60 * i / TAXA) * 0.05 + math.sin(math.tau * 120 * i / TAXA) * 0.025
             + rnd.uniform(-1, 1) * 0.012) * min(1.0, i / 4000, (dur * TAXA - i) / 4000) for i in range(int(dur * TAXA))]


def estalo_glitch():
    s = []
    for i in range(int(0.12 * TAXA)):
        degrau = (i // 90) * 7919 % 13 / 13.0 - 0.5
        s.append(degrau * 0.5 * (1 - i / (0.12 * TAXA)))
    return s


# ---------------------------------------------------------------- a imagem
_brancos = {}


def veu(tela, cor, alfa):
    if alfa <= 0:
        return
    s = _brancos.get(cor)
    if s is None:
        s = _brancos[cor] = pygame.Surface((W, H))
        s.fill(cor)
    s.set_alpha(min(255, int(alfa)))
    tela.blit(s, (0, 0))


def zoom(img, z, centro=LEO):
    if z <= 1.001:
        return img
    w, h = int(W / z), int(H / z)
    x = min(max(0, centro[0] - w // 2), W - w)
    y = min(max(0, centro[1] - h // 2), H - h)
    return pygame.transform.scale(img.subsurface((x, y, w, h)), (W, H))


def glitch(img, forca):
    """Separacao RGB com fatias fora do lugar: o glitch dos cacos, na tela inteira."""
    d = int(10 * forca) + 2
    ciano = img.copy(); ciano.fill((0, 255, 255), special_flags=pygame.BLEND_MULT)
    verm = img.copy(); verm.fill((255, 0, 0), special_flags=pygame.BLEND_MULT)
    s = pygame.Surface((W, H))
    s.blit(ciano, (-d, 0))
    s.blit(verm, (d, 0), special_flags=pygame.BLEND_ADD)
    for _ in range(int(3 + 6 * forca)):
        y, alto = rnd.randrange(0, H - 40), rnd.randrange(8, 44)
        s.blit(s, (rnd.randrange(-70, 70), y), (0, y, W, alto))
    return s


def letterbox(tela, k=1.0):
    a = int(BARRA * k)
    if a > 0:
        tela.fill((0, 0, 0), (0, 0, W, a))
        tela.fill((0, 0, 0), (0, H - a, W, a))


def cartela(tela, s, tam, y, cor, idade, dura=None, x=W // 2):
    """Texto que entra com um 'pop' (estoura e assenta) e some no fim."""
    if idade < 0 or (dura is not None and idade > dura):
        return
    img = ui.texto(s, tam, cor, CONTORNO)
    k = 1.0 + 0.35 * max(0.0, 1.0 - idade / 0.10)
    if k > 1.01:
        img = pygame.transform.scale(img, (int(img.get_width() * k), int(img.get_height() * k)))
    if dura is not None and dura - idade < 0.12:
        img = img.copy(); img.set_alpha(int(255 * (dura - idade) / 0.12))
    tela.blit(img, (x - img.get_width() // 2, y - img.get_height() // 2))


# ------------------------------------------------------------------ o jogo
class Jogo:
    """Uma partida de verdade, tocada pelo robo, adiantada ate a batida pedida."""

    def __init__(self, app, indice, batida, parar_de_tocar=None):
        self.app = app
        f = self.fase = fases.carregar(indice)
        p = self.p = P.Partida(app, f)
        app.tela = p
        app.transicao.estado = 0
        p._comecar()
        toques = [b * f.dur_batida for b in f.acoes
                  if parar_de_tocar is None or b < parar_de_tocar]
        k, orig = [0], p._passo
        self.dano = None

        def passo():
            if k[0] < len(toques) and toques[k[0]] <= p.est.tempo + PASSO_FISICA:
                p.apertou = True
                k[0] += 1
            orig()
            if p.est.dano and self.dano is None:
                self.dano = p.est.dano
        p._passo = passo
        self.mudo = True
        while p.modo == P.JOGANDO and p.est.tempo < batida * f.dur_batida - 1e-6:
            p.atualizar(DT)
        self.mudo = False

    @property
    def tempo(self):
        return self.p.est.tempo

    def quadro(self):
        """Avanca 1/60 s e devolve a tela do jogo (a mesma superficie a cada vez)."""
        app = self.app
        tr = app.transicao
        if not (tr.cobrindo and isinstance(app.tela, P.Partida)):
            app.tela.atualizar(DT)
        tr.atualizar(DT)
        tela = app.janela.screen
        app.tela.desenhar(tela)
        tr.desenhar(tela)
        return tela


class Trailer:
    def __init__(self, saida):
        self.saida = saida
        self.tmp = tempfile.mkdtemp(prefix="trailer_")
        self.som = Som()
        self.n = 0                                   # quadros ja gravados
        self.jogo = None
        self.planos = []
        save.salvar = lambda: None
        for m in ("tocar_musica", "parar_musica", "pausar_musica", "retomar_musica"):
            setattr(audio, m, lambda *a: None)
        audio.tocar = self._sfx
        self.app = main.App()
        self.app.transicao.estado = 0
        self.video = os.path.join(self.tmp, "video.mp4")
        self.ff = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
             "-pix_fmt", "yuv420p", self.video], stdin=subprocess.PIPE)
        self.fora = pygame.Surface((W, H))

    @property
    def t(self):
        return self.n / FPS

    def _sfx(self, nome):
        if self.jogo is not None and not self.jogo.mudo:
            self.som.do_jogo(nome, self.t)

    def gravar(self, img, treme=0.0):
        if treme > 0.5:
            self.fora.fill((0, 0, 0))
            self.fora.blit(img, (rnd.uniform(-treme, treme), rnd.uniform(-treme, treme)))
            img = self.fora
        self.ff.stdin.write(pygame.image.tobytes(img, "RGB"))
        self.n += 1

    def plano(self, nome):
        self.planos.append((nome, self.t))
        print(f"  {self.t:6.2f}s  {nome}", flush=True)

    # ---------------------------------------------------------------- pecas
    def preto(self, dur, desenha=None):
        tela = pygame.Surface((W, H))
        for i in range(int(round(dur * FPS))):
            tela.fill((0, 0, 0))
            if desenha:
                desenha(tela, i / FPS)
            self.gravar(tela)

    def jogar(self, indice, b0, b1, por_cima=None, fx=None, musica=True, corte_glitch=True, vol=1.0,
              parar_de_tocar=None, ate_dano=False):
        """
        O jogo da batida b0 a b1 da fase. `por_cima(tela, t, batida)` desenha
        cartelas; `fx(t, batida)` devolve dict(zoom, flash, treme, caixa).
        """
        jogo = self.jogo = Jogo(self.app, indice, b0, parar_de_tocar)
        f = jogo.fase
        dur = (b1 - b0) * f.dur_batida
        if musica:
            self.som.musica(f.cancao, jogo.tempo, dur, self.t, vol)
        if corte_glitch:
            self.som.somar(whoosh(), max(0.0, self.t - 0.12), 0.5)
        n = int(round(dur * FPS))
        tela_fx = pygame.Surface((W, H))
        for i in range(n):
            t = i / FPS
            img = jogo.quadro()
            batida = b0 + t / f.dur_batida
            e = fx(t, batida) if fx else {}
            img = zoom(img, e.get("zoom", 1.0))
            if corte_glitch and i < 5:
                img = glitch(img, 1.0 - i / 5)
            tela_fx.blit(img, (0, 0))
            if por_cima:
                por_cima(tela_fx, t, batida)
            veu(tela_fx, (255, 255, 255), e.get("flash", 0))
            letterbox(tela_fx, e.get("caixa", 0.0))
            self.gravar(tela_fx, e.get("treme", 0.0))
            if ate_dano and jogo.dano:
                return tela_fx.copy()
        return tela_fx

    # --------------------------------------------------------------- roteiro
    def rodar(self):
        som = self.som
        compasso = {i: fases.carregar(i).dur_batida * 4 for i in range(3)}

        def impacto(t, forca=1.0):
            """flash e tranco que somem em ~0,3 s"""
            return {"flash": max(0.0, 230 * forca * (1 - t / 0.09)), "treme": max(0.0, 14 * forca * (1 - t / 0.3))}

        # 0 -- preto e o riser
        self.plano("0 preto")
        som.somar(riser(0.8), 0.0, 0.8)
        self.preto(0.8)

        # 1 -- o gancho: a Cidadela no drop final, em formato de cinema
        self.plano("1 gancho: cidadela, drop final")
        som.somar(boom(), self.t, 0.7)
        self.jogar(2, 224, 232, corte_glitch=False,
                   fx=lambda t, b: {**impacto(t), "zoom": 1.0 + 0.08 * t / 3.2, "caixa": 1.0})

        # 2 -- a premissa, no escuro
        self.plano("2 premissa")
        som.somar(boom(), self.t, 0.9)
        som.somar(zumbido(3.4), self.t)
        frases = ("LEO JOGAVA DE MADRUGADA...", "...ATE A TELA O PUXAR.")
        t0 = self.t
        for j, frase in enumerate(frases):
            for c in range(len(frase)):
                if frase[c] != " ":
                    som.somar(tique(), t0 + 0.25 + j * 1.55 + c * 0.035, 0.6)
        som.somar(estalo_glitch(), t0 + 2.75, 0.8)

        def premissa(tela, t):
            for _ in range(140):                                         # o chuvisco
                c = rnd.randrange(14, 46)
                tela.fill((c, c, c + 6), (rnd.randrange(W), rnd.randrange(H), rnd.randrange(2, 30), 2))
            for j, frase in enumerate(frases):
                idade = t - 0.25 - j * 1.55
                if idade < 0:
                    continue
                letras = frase[:int(idade / 0.035) + 1]
                img = ui.texto(letras, 40, BRANCO if j == 0 else AZUL, CONTORNO)
                x, y = W // 2 - ui.texto(frase, 40, BRANCO, CONTORNO).get_width() // 2, 300 + j * 70
                if j == 1 and t > 2.75:
                    x += rnd.randrange(-6, 7); y += rnd.randrange(-3, 4)
                tela.blit(img, (x, y))
            if t > 2.75:
                tela.blit(glitch(tela.copy(), min(1.0, (t - 2.75) * 2)), (0, 0))
            letterbox(tela)
        self.preto(3.4, premissa)

        # 3 e 4 -- o logo sobre o Bosque, e o Bosque: a mesma partida, sem corte
        self.plano("3 logo sobre o bosque")
        som.somar(boom(), self.t, 1.0)
        logo = pygame.transform.scale_by(ui.imagem("logo.png"), 3)
        d = fases.carregar(0).dur_batida
        entrada = 4 * d

        def bosque_cima(tela, t, b):
            if t < entrada + 0.4:
                k = 1.0 if t < entrada - 0.15 else max(0.0, 1.0 - (t - entrada + 0.15) / 0.5)
                veu(tela, (6, 10, 22), 150 * k)
                img = logo
                if k < 1.0:
                    img = logo.copy(); img.set_alpha(int(255 * k))
                pulo = 1.0 + 0.3 * max(0.0, 1.0 - t / 0.12)
                if pulo > 1.01:
                    img = pygame.transform.scale(img, (int(img.get_width() * pulo), int(img.get_height() * pulo)))
                tela.blit(img, (W // 2 - img.get_width() // 2, 250 - img.get_height() // 2))
                cartela(tela, "UM BOTAO. NO RITMO.", 34, 500, AMARELO, t - d, entrada - d - 0.1)
            cartela(tela, "PULE", 72, 112, VERDE, t - entrada - 2 * d, 2 * d - 0.1)
            cartela(tela, "NA BATIDA", 72, 112, VERDE, t - entrada - 4 * d, 3 * d)

        def bosque_fx(t, b):
            e = impacto(t)
            e["caixa"] = max(0.0, 1.0 - t / 0.9)
            if t >= entrada:
                e["zoom"] = 1.0 + 0.10 * max(0.0, 1.0 - (t - entrada) / 0.35)
            return e
        self.jogar(0, 8, 20, bosque_cima, bosque_fx, corte_glitch=False)
        self.planos.append(("4 bosque", self.planos[-1][1] + entrada))

        # 5 -- as Ilhas: um compasso de subida e o drop
        self.plano("5 ilhas: subida e drop")
        d = fases.carregar(1).dur_batida
        som.somar(riser(4 * d), self.t, 0.7)
        som.somar(boom(), self.t + 4 * d, 0.8)

        def ilhas_fx(t, b):
            if b >= 32:
                e = impacto(t - 4 * d)
                e["zoom"] = 1.0 + 0.12 * max(0.0, 1.0 - (t - 4 * d) / 0.4)
                return e
            return {"zoom": 1.0 + 0.04 * t / (4 * d)}

        def ilhas_cima(tela, t, b):
            cartela(tela, "110 BPM", 72, 100, AMARELO, t - 4 * d, 4 * d - 0.1)
            cartela(tela, "O MUNDO ACELERA", 56, 112, BRANCO, t - 8 * d, 6 * d)
        self.jogar(1, 28, 44, ilhas_cima, ilhas_fx)

        # 6 -- a montagem: cada plano mais curto que o anterior
        self.plano("6 montagem")
        for indice, b0, batidas in ((0, 140, 4), (1, 160, 4), (2, 100, 4), (1, 168, 2),
                                    (2, 108, 2), (1, 176, 1), (2, 116, 1)):
            self.jogar(indice, b0, b0 + batidas,
                       fx=lambda t, b: {"zoom": 1.0 + 0.08 * max(0.0, 1.0 - t / 0.25)})

        # 7 -- a crise: o Leo erra, o quadro congela, silencio
        self.plano("7 crise")
        b0, parar = self._achar_erro()
        t_ini = self.t
        ultimo = self.jogar(2, b0, b0 + 12, parar_de_tocar=parar, ate_dano=True)
        # a musica desse plano vai so ate o impacto, e morre depressa
        c, ini, _, t_m, vol, _ = som.musicas.pop()
        som.musicas.append((c, ini, self.t - t_ini + 0.25, t_m, vol, 0.28))
        som.somar(boom(1.0), self.t, 0.8)
        cinza = pygame.transform.grayscale(ultimo)
        t0 = self.t
        for i in range(int(1.2 * FPS)):
            t = i / FPS
            img = zoom(cinza, 1.0 + 0.10 * t / 1.2 + 0.05 * min(1.0, t / 0.08))
            tela = img.copy()
            veu(tela, (255, 40, 60), 150 * max(0.0, 1 - t / 0.25) + 26)
            cartela(tela, "ERROU A BATIDA?", 64, 250, VERMELHO, t - 0.25)
            self.gravar(tela, 16 * max(0.0, 1 - t / 0.3))
        for k in range(2):
            som.somar(coracao(), self.t + 0.1 + k * 0.8, 1.0)
        self.preto(1.5, lambda tela, t: cartela(tela, "O RITMO NAO PERDOA.", 44, H // 2, BRANCO, t - 0.15, 1.3))

        # 8 -- a Cidadela: construcao e drop
        self.plano("8 cidadela: construcao e drop")
        d = fases.carregar(2).dur_batida
        som.somar(riser(8 * d), self.t, 0.9)
        som.somar(boom(), self.t + 8 * d, 1.0)

        def eclipse_fx(t, b):
            if b >= 64:
                tb = (t - 8 * d) % (4 * d)                               # um soco a cada compasso
                e = impacto(t - 8 * d)
                e["zoom"] = 1.0 + 0.11 * max(0.0, 1.0 - tb / 0.3)
                return e
            return {"zoom": 1.0 + 0.05 * t / (8 * d)}

        def eclipse_cima(tela, t, b):
            cartela(tela, "CIDADELA DO ECLIPSE", 50, 112, ROXO, t - 0.05, 8 * d - 0.2)
            cartela(tela, "150 BPM", 72, 100, AMARELO, t - 8 * d, 4 * d - 0.1)
        self.jogar(2, 56, 76, eclipse_cima, eclipse_fx, corte_glitch=False)

        # 9 -- o fim da Cidadela: FASE COMPLETA e o carimbo da nota
        self.plano("9 vitoria e nota")
        jogo = self.jogo = Jogo(self.app, 2, 320)
        som.musica("eclipse", jogo.tempo, 7.0, self.t, 1.0, 1.5)
        limite = self.n + int(7.5 * FPS)
        while self.n < limite:
            img = jogo.quadro()
            self.gravar(img)
            tela = self.app.tela
            if isinstance(tela, menus.TelaResultado) and tela.tempo > 2.0:
                break

        # 10 -- o logo e os creditos, sobre o fim do Bosque
        self.plano("10 logo e creditos")
        som.somar(boom(), self.t, 1.0)
        dur = 5.0
        creditos = ["MUSICAS: " + " / ".join(TRILHAS[c].creditos.upper() for c in ("bosque", "ilhas", "eclipse")),
                    "MUSIC PROVIDED BY NOCOPYRIGHTSOUNDS (NCS.IO)",
                    "FEITO COM POWER PPLAY 2.0 (IC-UFF)   PERSONAGEM: OZZBIT GAMES, MALE_HERO"]

        def fim_cima(tela, t, b):
            veu(tela, (6, 10, 22), 170)
            pulo = 1.0 + 0.3 * max(0.0, 1.0 - t / 0.12)
            img = logo if pulo < 1.01 else pygame.transform.scale(
                logo, (int(logo.get_width() * pulo), int(logo.get_height() * pulo)))
            tela.blit(img, (W // 2 - img.get_width() // 2, 220 - img.get_height() // 2))
            cartela(tela, "3 MUNDOS. 3 MUSICAS. 1 BOTAO.", 36, 440, AMARELO, t - 0.6)
            for i, linha in enumerate(creditos):
                if t > 1.4:
                    ui.desenhar_texto_ajustado(tela, linha, 16, W // 2, 560 + i * 34, W - 120, BRANCO)
            veu(tela, (0, 0, 0), 255 * max(0.0, (t - dur + 0.9) / 0.9))
        d = fases.carregar(0).dur_batida
        self.jogar(0, 196, 196 + dur / d, fim_cima, lambda t, b: impacto(t), corte_glitch=False)
        self.som.musicas[-1] = self.som.musicas[-1][:5] + (0.9,)

        self.fechar()

    def _achar_erro(self):
        """(batida inicial, batida em que o robo para de tocar): um erro que acaba num CACO, logo."""
        f = fases.carregar(2)
        for parar in [b for b in f.acoes if 110 <= b <= 150]:
            jogo = Jogo(self.app, 2, parar - 4, parar)
            limite = (parar + 3) * f.dur_batida
            while jogo.p.modo == P.JOGANDO and jogo.tempo < limite and not jogo.dano:
                jogo.p.atualizar(DT)
            if jogo.dano == "perigo":
                return math.floor(parar / 4) * 4 - 4, parar
        raise SystemExit("nao achei um erro que termina num caco")

    # ------------------------------------------------------------------ fim
    def fechar(self):
        self.ff.stdin.close()
        self.ff.wait()
        dur = self.t
        fx = os.path.join(self.tmp, "fx.wav")
        self.som.gravar(fx, dur)
        entradas, filtros, nomes = ["-i", fx], [], ["[1:a]"]          # 0 e o video, 1 os efeitos
        for i, (cancao, ini, d, t, vol, sai) in enumerate(self.som.musicas, 2):
            entradas += ["-ss", f"{ini:.4f}", "-t", f"{d:.4f}", "-i", self._wav(cancao)]
            filtros.append(f"[{i}:a]afade=t=in:d=0.012,afade=t=out:st={max(0.0, d - sai):.4f}:d={sai:.3f},"
                           f"volume={vol * 0.8:.2f},adelay={int(t * 1000)}:all=1[m{i}]")
            nomes.append(f"[m{i}]")
        filtros.append("".join(nomes) + f"amix=inputs={len(nomes)}:normalize=0,"
                       f"loudnorm=I=-14:TP=-1.5:LRA=11,apad,atrim=duration={dur:.3f}[a]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", self.video, *entradas,
                        "-filter_complex", ";".join(filtros), "-map", "0:v", "-map", "[a]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-movflags", "+faststart", self.saida], check=True)
        shutil.rmtree(self.tmp, ignore_errors=True)
        print(f"\n{self.saida}: {dur:.1f} s, {self.n} quadros")
        for nome, t in self.planos:
            print(f"  {t:6.2f}s  {nome}")

    _wavs = {}

    def _wav(self, cancao):
        """A faixa em WAV: cortar um MP3 pelo meio nao cai exatamente na amostra pedida."""
        if cancao not in self._wavs:
            destino = os.path.join(self.tmp, f"{cancao}.wav")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i",
                            os.path.join(DIR_MUSICA, f"{cancao}.mp3"), destino], check=True)
            self._wavs[cancao] = destino
        return self._wavs[cancao]


if __name__ == "__main__":
    Trailer(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "trailer_rhythm_striker_3.mp4")).rodar()
