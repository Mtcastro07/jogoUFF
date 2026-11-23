"""
Rhythm Striker -- TRAILER FINAL, para o YouTube em 4K.

    ./.venv/bin/python ferramentas/trailer_final.py [saida.mp4] [--escala 1] [--preview DIR]

O trailer conta o enredo do GDD em tres atos, com o jogo de verdade:

  I.   CASA      03:12 da madrugada. O Leo, de pijama, na frente da TV, aperta
                 START -- e a tela o puxa.
  II.  O REINO   Ele cai no Bosque, parado, sem saber onde esta. O Rhythm Kingdom
                 dita as regras (tudo e musica; quem sai do compasso vira ruido).
                 O mapa: cinco mundos ate em casa. Dunas, Ilhas, Geleira, cada uma
                 mais rapida, e a montagem que acelera.
  III. A VOLTA   Na Cidadela ele erra com um coracao so e vira ruido. No escuro, a
                 foto da familia. "De novo." O drop do ultimo mundo, o portal, e o
                 quarto as 06:00, com a nota S na TV. A TV ainda chia.

Duas vozes no texto: o Leo pensa em branco, letra por letra; o Reino fala na cor
do mundo, entrando com falha de imagem.

A pos-producao trabalha em 3840x2160: o quadro (1280x720) e ampliado 3x sem
suavizar e so entao recebe zoom, tremor e texto. `--escala 1` renderiza em 720p
(rapido, para conferir o roteiro). O audio sai da mesma timeline, mixado por
ferramentas/geradores/trailer_mix.py. Precisa do ffmpeg no PATH e do numpy.
"""
import json
import math
import os
import random
import subprocess
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.dont_write_bytecode = True
import pygame


def _arg(nome, padrao=None):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


SAIDA = next((a for a in sys.argv[1:] if a.endswith(".mp4")),
             os.path.join(RAIZ, "trailer_rhythm_striker_final.mp4"))
PREVIEW = _arg("--preview")
K = int(_arg("--escala", "3"))           # 3 = 3840x2160 (4K), 1 = 1280x720
TITULO = "Rhythm Striker - Trailer"
FPS = 60
DT = 1.0 / FPS

import main
from jogo import arte, fases, menus, ui
from jogo import partida as P
from jogo.audio import audio, TRILHAS
from jogo.config import (LARGURA, ALTURA, CONTORNO, BRANCO, CINZA, AMARELO, PASSO_FISICA,
                         JOGADOR_TAM)
from jogo.arte import DIR_ART
from jogo.save import save

W4, H4 = LARGURA * K, ALTURA * K

random.seed(7)
save.salvar = lambda: None
save.recordes = {}                       # o Leo acabou de chegar: nada vencido ainda
app = main.App()
app.transicao.estado = 0
sfx, synth, musica = [], [], []
gravando = [False]
audio.tocar = lambda nome: gravando[0] and nome not in ("navegar", "clique") and sfx.append((t_video(), nome))
for m in ("tocar_musica", "parar_musica", "pausar_musica", "retomar_musica"):
    setattr(audio, m, lambda *a: None)

tmp = tempfile.mkdtemp(prefix="trailer_final_")
MUDO = os.path.join(tmp, "video.mp4")
ff = None if PREVIEW else subprocess.Popen(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
     "-s", f"{W4}x{H4}", "-r", str(FPS), "-i", "-",
     "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-tune", "animation",
     "-g", "30", "-bf", "2", "-pix_fmt", "yuv420p", MUDO], stdin=subprocess.PIPE)
quadros = [0]
planos = []


def t_video():
    return quadros[0] / FPS


def plano(nome):
    planos.append((round(t_video(), 3), nome))
    print(f"{t_video():6.2f}s  {nome}", flush=True)


def som(tipo, t=None, **k):
    synth.append({"t": t_video() if t is None else t, "tipo": tipo, **k})


def efeito(nome, t=None):
    """Um som do proprio jogo (assets/sfx), fora da partida."""
    sfx.append((t_video() if t is None else t, nome))


def clip(cancao, origem, dur, ent=0.01, sai=0.01, ganho=1.0, tapestop=0.0, abafado=False):
    musica.append({"t": t_video(), "arquivo": f"{RAIZ}/assets/music/{cancao}.mp3", "origem": origem,
                   "dur": dur, "ent": ent, "sai": sai, "ganho": ganho, "tapestop": tapestop,
                   "abafado": abafado})


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------- pos-producao
class FX:
    def __init__(self):
        self.zooms, self.flashes, self.trancos, self.glitches, self.textos = [], [], [], [], []
        self.empurra = None
        self.z_manual = 1.0
        self.barras = 0.0
        self.foco = (LARGURA / 2, ALTURA / 2)

    def zoom(self, t, pico=1.12, dur=0.45):
        self.zooms.append((t, pico, dur))

    def flash(self, t, dur=0.08, cor=(255, 255, 255), forca=1.0):
        self.flashes.append((t, dur, cor, forca))

    def tranco(self, t, amp=14, dur=0.3):
        self.trancos.append((t, amp, dur))

    def glitch(self, t, dur=0.08, k=1.0):
        self.glitches.append((t, dur, k))

    def texto(self, s, t0, t1, tam=56, cor=BRANCO, y=None, estilo="pop"):
        self.textos.append((s, t0, t1, tam, cor, ALTURA // 2 if y is None else y, estilo))

    def z_agora(self, t):
        z = self.z_manual
        if self.empurra and self.empurra[0] <= t <= self.empurra[1]:
            t0, t1, z0, z1 = self.empurra
            z = max(z, z0 + (z1 - z0) * suave((t - t0) / (t1 - t0)))
        for t0, pico, dur in self.zooms:
            d = t - t0
            if 0 <= d < dur:
                k = suave(d / 0.07) if d < 0.07 else 1 - suave((d - 0.07) / (dur - 0.07))
                z = max(z, 1 + (pico - 1) * k)
        return z


fx = FX()
veu = pygame.Surface((W4, H4))
_texto_cache = {}
LETRA = 0.045                    # o Leo "pensa" uma letra a cada 45 ms
Y_LEG = 585                      # as falas ficam no terco de baixo; o PERFEITO! aparece no alto
Y_QUARTO = 678                   # no quarto, abaixo dos pes do Leo


def _txt(s, tam, cor, tinta=None):
    """O texto na fonte do jogo, ampliado K vezes sem suavizar. `tinta` tinge (a falha do Reino)."""
    k = (s, tam, cor, tinta)
    if k not in _texto_cache:
        if tinta is None:
            img = ui.texto(s, tam, cor, CONTORNO)
            img = pygame.transform.scale_by(img, K) if K > 1 else img
        else:
            img = _txt(s, tam, cor).copy()
            img.fill((*tinta, 255), special_flags=pygame.BLEND_RGBA_MULT)
        _texto_cache[k] = img
    return _texto_cache[k]


def leo(s, t0, t1, tam=36, y=Y_LEG):
    """O Leo pensando: branco, letra por letra, com o tique de cada letra."""
    fx.texto(s, t0, t1, tam, BRANCO, y, "leo")
    for i, ch in enumerate(s):
        if ch not in " .":
            som("tick", t=t0 + i * LETRA, ganho=0.32)


def reino(s, t0, t1, cor, tam=52, y=Y_LEG):
    """O Rhythm Kingdom falando: na cor do mundo, entrando com falha de imagem."""
    fx.texto(s, t0, t1, tam, cor, y, "reino")
    som("glitch", t=t0, dur=0.2, ganho=0.4)


def _glitchar(tela, k, rnd):
    w, h = tela.get_size()
    src = tela.copy()
    dx = int(3 + 12 * k) * K
    r = src.copy(); r.fill((255, 0, 0), special_flags=pygame.BLEND_MULT)
    gb = src.copy(); gb.fill((0, 255, 255), special_flags=pygame.BLEND_MULT)
    tela.fill((0, 0, 0))
    tela.blit(r, (dx, 0), special_flags=pygame.BLEND_ADD)
    tela.blit(gb, (-dx, 0), special_flags=pygame.BLEND_ADD)
    for _ in range(int(3 + 9 * k)):
        y = rnd.randrange(h // K) * K
        hh = min(rnd.randrange(4, 44) * K, h - y)
        off = rnd.randint(-int(70 * k), int(70 * k)) * K
        tela.blit(tela.subsurface((0, y, w, hh)).copy(), (off, y))


def _desenhar_textos(tela, t):
    for s, t0, t1, tam, cor, y, estilo in fx.textos:
        if not (t0 <= t < t1):
            continue
        d = t - t0
        if estilo == "leo":
            cheio = _txt(s, tam, cor)
            n = min(len(s), int(d / LETRA) + 1)
            img = _txt(s[:n], tam, cor)
            if t1 - t < 0.2:
                img = img.copy()
                img.set_alpha(int(255 * (t1 - t) / 0.2))
            r = img.get_rect(midleft=(W4 // 2 - cheio.get_width() // 2, int(y) * K))
            sombra = _txt(s[:n], tam, (0, 0, 0))
            tela.blit(sombra, r.move(4 * K, 4 * K))
            tela.blit(img, r)
            continue
        img = _txt(s, tam, cor)
        esc = 1 + 0.6 * (1 - suave(d / 0.12)) if estilo in ("pop", "reino") else 1.0
        if t1 - t < 0.1:
            esc *= 0.6 + 0.4 * (t1 - t) / 0.1
        def escalar(i):
            if abs(esc - 1) <= 0.01:
                return i
            return pygame.transform.scale(i, (max(1, int(i.get_width() * esc)), max(1, int(i.get_height() * esc))))
        img2 = escalar(img)
        r = img2.get_rect(center=(W4 // 2, int(y) * K))
        sombra = img2.copy(); sombra.fill((0, 0, 0, 160), special_flags=pygame.BLEND_RGBA_MULT)
        tela.blit(sombra, r.move(5 * K, 5 * K))
        if estilo == "reino" and d < 0.35:
            # a fala do Reino chega quebrada: as cores separadas que se juntam
            k = 1 - d / 0.35
            dx = int(14 * k) * K
            tela.blit(escalar(_txt(s, tam, cor, (255, 70, 190))), r.move(-dx, 0), special_flags=pygame.BLEND_ADD)
            tela.blit(escalar(_txt(s, tam, cor, (80, 235, 255))), r.move(dx, int(3 * k) * K),
                      special_flags=pygame.BLEND_ADD)
        tela.blit(img2, r)


def pos_producao(tela, t):
    """Tudo em 4K: o quadro ja chegou ampliado, sem suavizar."""
    rnd = random.Random(quadros[0])
    z = fx.z_agora(t)
    if z > 1.001:
        cw, ch = int(W4 / z), int(H4 / z)
        x = min(max(int(fx.foco[0] * K - cw / 2), 0), W4 - cw)
        y = min(max(int(fx.foco[1] * K - ch / 2), 0), H4 - ch)
        tela.blit(pygame.transform.smoothscale(tela.subsurface((x, y, cw, ch)), (W4, H4)), (0, 0))
    amp = 0.0
    for t0, a, dur in fx.trancos:
        if 0 <= t - t0 < dur:
            amp = max(amp, a * (1 - (t - t0) / dur))
    if amp >= 1:
        copia = tela.copy()
        tela.fill((0, 0, 0))
        # tremor em pixels inteiros do jogo: as bordas do pixel art nao tremulam
        tela.blit(copia, (rnd.randint(-int(amp), int(amp)) * K, rnd.randint(-int(amp), int(amp)) * K))
    for t0, dur, k in fx.glitches:
        if 0 <= t - t0 < dur:
            _glitchar(tela, k * (1 - 0.5 * (t - t0) / dur), rnd)
            break
    _desenhar_textos(tela, t)
    for t0, dur, cor, forca in fx.flashes:
        if 0 <= t - t0 < dur:
            veu.fill(cor)
            veu.set_alpha(int(255 * forca * (1 - (t - t0) / dur)))
            tela.blit(veu, (0, 0))
    if fx.barras > 0:
        b = int(92 * fx.barras) * K
        tela.fill((0, 0, 0), (0, 0, W4, b))
        tela.fill((0, 0, 0), (0, H4 - b, W4, b))


def emitir(tela, escuro=0.0, claro=0.0):
    grande = pygame.transform.scale(tela, (W4, H4)) if K > 1 else tela.copy()
    pos_producao(grande, t_video())
    for cor, a in (((0, 0, 0), escuro), ((255, 255, 255), claro)):
        if a > 0:
            veu.fill(cor)
            veu.set_alpha(int(255 * min(1.0, a)))
            grande.blit(veu, (0, 0))
    if PREVIEW:
        if quadros[0] % 30 == 0:
            pygame.image.save(pygame.transform.smoothscale(grande, (640, 360)),
                              os.path.join(PREVIEW, f"q{quadros[0]:05d}.png"))
    else:
        ff.stdin.write(pygame.image.tobytes(grande, "RGB"))
    quadros[0] += 1


# ------------------------------------------------------------------ o quarto
def _png(nome):
    return pygame.image.load(os.path.join(DIR_ART, "trailer", nome)).convert_alpha()


TV = pygame.Rect(232 * 4, 88 * 4, 57 * 4, 32 * 4)     # a tela da TV no quadro de 1280x720
PES_LEO = (176 * 4, 162 * 4)
_linhas = pygame.Surface(TV.size, pygame.SRCALPHA)     # as linhas de varredura do tubo
for _y in range(0, TV.h, 2):
    _linhas.fill((0, 0, 0, 70), (0, _y, TV.w, 1))
_ruido_tv = []
for _s in range(4):
    _r = random.Random(100 + _s)
    _img = pygame.Surface((TV.w // 4, TV.h // 4))
    for _yy in range(_img.get_height()):
        for _xx in range(_img.get_width()):
            _v = _r.randrange(30, 230)
            _img.set_at((_xx, _yy), (_v, _v, _v))
    _ruido_tv.append(pygame.transform.scale(_img, TV.size))


class Quarto:
    """O quarto do Leo (ferramentas/geradores/pintar_quarto.py), com a TV mostrando o jogo de verdade."""

    def __init__(self, nome, leo_png):
        self.base = pygame.transform.scale(_png(f"{nome}.png"), (LARGURA, ALTURA)).convert()
        self.brilho = pygame.transform.scale(_png("brilho_tv.png"), (LARGURA, ALTURA)).convert()
        self.leo = pygame.transform.scale_by(arte.png("personagens", leo_png), 4)
        self.branco = self.leo.copy()
        self.branco.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        self.tela_jogo = pygame.Surface((LARGURA, ALTURA)).convert()

    def desenhar(self, tela, t, tv=None, puxao=0.0, luz=0.55, chiado=0.0):
        tela.blit(self.base, (0, 0))
        if puxao < 1.0:
            self._leo(tela, t, puxao)
        if tv is not None:
            pequena = pygame.transform.smoothscale(tv, TV.size)
            cor = pygame.transform.average_color(pequena)[:3]
            g = self.brilho.copy()
            k = luz + 1.2 * suave(puxao)
            g.fill(tuple(min(255, int((40 + c * 0.8) * k)) for c in cor), special_flags=pygame.BLEND_MULT)
            tela.blit(g, (0, 0), special_flags=pygame.BLEND_ADD)
            tela.blit(pequena, TV.topleft)
            if chiado > 0:
                r = _ruido_tv[int(t * 30) % 4].copy()
                r.set_alpha(int(255 * min(1.0, chiado)))
                tela.blit(r, TV.topleft)
            if puxao > 0:
                veu_tv = pygame.Surface(TV.size)
                veu_tv.fill((255, 255, 255))
                veu_tv.set_alpha(int(230 * suave(puxao * 1.4)))
                tela.blit(veu_tv, TV.topleft)
            tela.blit(_linhas, TV.topleft)

    def _leo(self, tela, t, puxao):
        respira = 4 if math.sin(t * 2.6) > 0.55 else 0        # um pixel do Leo: ele respira
        if puxao <= 0:
            tela.blit(self.leo, (PES_LEO[0] - self.leo.get_width() // 2, PES_LEO[1] - self.leo.get_height() + respira))
            return
        # a tela o puxa: o corpo clareia, espicha na direcao da TV e some dentro dela
        e = suave(puxao)
        corpo = self.leo.copy()
        b = self.branco.copy(); b.set_alpha(int(255 * min(1.0, e * 1.6)))
        corpo.blit(b, (0, 0))
        sx, sy = 1 + 2.2 * e, max(0.04, 1 - 0.9 * e)
        corpo = pygame.transform.scale(corpo, (max(1, int(corpo.get_width() * sx)), max(1, int(corpo.get_height() * sy))))
        m = e ** 1.6
        cx = PES_LEO[0] + (TV.centerx - PES_LEO[0]) * m
        cy = (PES_LEO[1] - self.leo.get_height() / 2) + (TV.centery - (PES_LEO[1] - self.leo.get_height() / 2)) * m
        tela.blit(corpo, corpo.get_rect(center=(int(cx), int(cy))))


def jogo_na_tv(tela_app, dt):
    """Atualiza e desenha uma tela do jogo (menu, resultado) num quadro de 1280x720 para a TV."""
    tela_app.atualizar(dt)
    s = pygame.Surface((LARGURA, ALTURA)).convert()
    tela_app.desenhar(s)
    return s


# ------------------------------------------------------------------ o jogo
class Robo:
    def __init__(self, p, semente, pular=()):
        rnd = random.Random(semente)
        dur = p.fase.dur_batida
        self.toques = [(b + (rnd.uniform(-0.12, 0.12) if rnd.random() < 0.06 else rnd.uniform(-0.03, 0.03))) * dur
                       for i, b in enumerate(p.fase.acoes) if i not in pular]
        self.i = 0
        orig = p._passo

        def passo():
            if self.i < len(self.toques) and self.toques[self.i] <= p.est.tempo + PASSO_FISICA:
                p.apertou = True
                self.i += 1
            orig()
        p._passo = passo


def nova_partida(mundo, semente, pular=(), comecar=True):
    p = P.Partida(app, fases.do_mundo(mundo))
    if comecar:
        p._comecar()
        Robo(p, semente, pular)
    app.tela = p
    return p


def avancar(p, ate):
    while p.modo == P.JOGANDO and p.est.tempo < ate:
        p.atualizar(DT)


def quadro_app():
    tela = app.janela.screen
    if not (app.transicao.cobrindo and isinstance(app.tela, P.Partida)):
        app.tela.atualizar(DT)
    app.transicao.atualizar(DT)
    tela.fill((0, 0, 0))
    app.tela.desenhar(tela)
    app.transicao.desenhar(tela)
    pygame.event.pump()
    return tela


def foco_heroi(p):
    hx = p.est.x - p.cam.x + JOGADOR_TAM * 0.5
    hy = p.est.y - p.cam.y + JOGADOR_TAM * 0.5
    return (hx * 0.6 + LARGURA * 0.5 * 0.4 + 60, hy * 0.6 + ALTURA * 0.5 * 0.4)


avisos = []


def gravar_partida(p, n, cada_quadro=None, mundo=""):
    gravando[0] = True
    for k in range(n):
        tela = quadro_app()
        fx.foco = foco_heroi(p)
        if cada_quadro:
            cada_quadro(p, k, tela)
        if p.est.dano:
            avisos.append(f"dano fora do roteiro: {mundo} t={p.est.tempo:.2f}")
        emitir(tela)
    gravando[0] = False


def cena(mundo, beat0, beats, semente=1, pular=(), musica_on=True, ent=0.01, sai=0.01,
         ganho=1.0, cada_quadro=None):
    """`beats` batidas do `mundo` a partir da batida `beat0`, com a faixa no mesmo trecho."""
    p = nova_partida(mundo, semente, pular)
    dur = p.fase.dur_batida
    if beat0 > 0:
        avancar(p, beat0 * dur - DT)
    # o fim do plano pelo tempo ABSOLUTO do video: arredondar cada plano
    # sozinho acumularia erro e, depois de 20 cortes, sairia do pulso
    n = round((t_video() + beats * dur) * FPS) - quadros[0]
    if musica_on:
        clip(p.fase.cancao, TRILHAS[p.fase.cancao].inicio + p.est.tempo + DT, n / FPS, ent, sai, ganho)
    gravar_partida(p, n, cada_quadro, mundo)
    return p


def tb(t0, beat0, dur, b):
    """O instante do video em que cai a batida `b` de um plano que comecou em `t0` na batida `beat0`."""
    return t0 + (b - beat0) * dur


def achar_tropeco(mundo, b_min, semente):
    """A primeira acao, depois de `b_min`, que pulada faz o Leo bater num perigo (nao cair)."""
    f = fases.do_mundo(mundo)
    for i, b in enumerate(f.acoes):
        if b < b_min:
            continue
        p = nova_partida(mundo, semente, pular={i})
        avancar(p, b * f.dur_batida - 0.5)
        while p.modo == P.JOGANDO and p.est.tempo < b * f.dur_batida + 1.5:
            p.atualizar(DT)
            if p.est.dano:
                if p.est.dano == "perigo":
                    return i, p.est.tempo
                break
    raise SystemExit(f"nenhum tropeco achado em {mundo}")


F = {m: fases.do_mundo(m) for m in ("bosque", "dunas", "ilhas", "geleira", "eclipse")}
DB, DD, DI, DG, DE = (F[m].dur_batida for m in ("bosque", "dunas", "ilhas", "geleira", "eclipse"))
COR = {m: F[m].tema.destaque for m in F}

TROPECO_B = achar_tropeco("bosque", 20, 9)
TROPECO_E = achar_tropeco("eclipse", 56, 5)          # no primeiro drop
print(f"tropecos: bosque acao {TROPECO_B[0]} ({TROPECO_B[1]:.2f}s), cidadela acao {TROPECO_E[0]} ({TROPECO_E[1]:.2f}s)")

ruidos = []
for s in range(4):
    r = random.Random(s)
    img = pygame.Surface((320, 180))
    for y in range(180):
        for x in range(320):
            v = r.randrange(0, 34)
            img.set_at((x, y), (v, v, v + 6))
    ruidos.append(pygame.transform.scale(img, (LARGURA, ALTURA)))
estatica = []                    # a tela fora do ar do "...vira ruido": chiado forte, em pixels do jogo
for s in range(4):
    r = random.Random(50 + s)
    img = pygame.Surface((640, 360))
    for y in range(360):
        faixa = 30 if (y + s * 7) % 23 < 2 else 0
        for x in range(640):
            v = min(255, r.randrange(20, 215) + faixa)
            img.set_at((x, y), (v, v, min(255, v + 10)))
    estatica.append(pygame.transform.scale(img, (LARGURA, ALTURA)))


def preto(dur, desenhar=None):
    for n in range(round(dur * FPS)):
        tela = app.janela.screen
        tela.fill((0, 0, 0))
        if desenhar:
            desenhar(tela, n * DT)
        emitir(tela)


class Logo(menus.TelaMenu):
    """O menu sem rodape nem botoes: so o cenario e o logo, que bate ao entrar."""
    def __init__(self, app):
        super().__init__(app)
        self.menu = None
        self.tempo_logo = 0.0

    def desenhar(self, tela):
        menus.Tela.desenhar(self, tela)
        logo = ui.imagem("logo.png", 3)
        esc = 1 + 0.7 * (1 - suave(self.tempo_logo / 0.14))
        if esc > 1.001:
            logo = pygame.transform.scale(logo, (int(logo.get_width() * esc), int(logo.get_height() * esc)))
        y = 220 + math.sin(self.tempo * 2.0) * 6
        tela.blit(logo, logo.get_rect(center=(LARGURA // 2, int(y) - 22)))

    def atualizar(self, dt):
        super().atualizar(dt)
        self.tempo_logo += dt


# =========================================================== I. CASA (03:12)
plano("1 o quarto, 03:12")
noite = Quarto("quarto_noite", "east.png")
tv_menu = menus.TelaMenu(app)
FOCO_QUARTO = ((PES_LEO[0] + TV.centerx) / 2, 400)
fx.foco = FOCO_QUARTO
DUR_QUARTO = 6.2
fx.empurra = (0.0, DUR_QUARTO, 1.0, 1.14)
clip("bosque", TRILHAS["bosque"].inicio, DUR_QUARTO + 0.1, ent=1.0, ganho=0.45, tapestop=0.5, abafado=True)
som("drone", dur=DUR_QUARTO + 1.6, ganho=0.35)
leo("SÓ MAIS UMA FASE...", 1.8, DUR_QUARTO - 0.2, y=Y_QUARTO)
for n in range(round(DUR_QUARTO * FPS)):
    t = n * DT
    tela = app.janela.screen
    noite.desenhar(tela, t, jogo_na_tv(tv_menu, DT))
    emitir(tela, escuro=max(0.0, 1 - t / 1.2))

plano("2 START: a tela puxa o Leo")
t0 = t_video()
efeito("clique", t0 + 0.05)
fx.empurra = (t0, t0 + 1.9, 1.14, 2.3)
som("riser", t=t0 + 0.1, dur=1.8, ganho=0.85)
DUR_PUXAO = 1.9
for n in range(round(DUR_PUXAO * FPS)):
    t = n * DT
    tela = app.janela.screen
    k = max(0.0, (t - 0.25) / (DUR_PUXAO - 0.35))
    noite.desenhar(tela, DUR_QUARTO + t, jogo_na_tv(tv_menu, DT), puxao=min(1.0, k))
    if n in (int(0.5 * FPS), int(1.0 * FPS), int(1.4 * FPS)):
        fx.glitch(t_video(), 0.12 + 0.08 * (n / FPS), 0.6 + 0.5 * (n / FPS))
        som("glitch", dur=0.2, ganho=0.5)
    emitir(tela, claro=max(0.0, (t - (DUR_PUXAO - 0.3)) / 0.3))
fx.empurra = None
fx.foco = (LARGURA / 2, ALTURA / 2)
som("boom", ganho=1.0)
fx.flash(t_video(), 0.25)
preto(0.7)

# =========================================================== II. O REINO
plano("3 o Bosque, parado")
p = nova_partida("bosque", 1, comecar=False)
som("drone", dur=4.4, ganho=0.4)
t0 = t_video()
leo("ONDE EU ESTOU?", t0 + 0.7, t0 + 2.5)
reino("RHYTHM KINGDOM.", t0 + 2.7, t0 + 4.3, COR["bosque"])
fx.empurra = (t0, t0 + 4.4, 1.08, 1.0)
for n in range(round(4.4 * FPS)):
    tela = quadro_app()
    fx.foco = foco_heroi(p)
    emitir(tela)
fx.empurra = None

plano("4 a largada: tudo e musica")
p._comecar()
Robo(p, 1)
t0 = t_video()
reino("AQUI, TUDO É MÚSICA.", tb(t0, 0, DB, 0.3), tb(t0, 0, DB, 3.8), COR["bosque"], 46)
reino("PULE NA BATIDA.", tb(t0, 0, DB, 4.0), tb(t0, 0, DB, 7.8), COR["bosque"], 52)
fx.zoom(tb(t0, 0, DB, 4), 1.1, 0.5)
n = round((t_video() + 8 * DB) * FPS) - quadros[0]
clip("bosque", TRILHAS["bosque"].inicio + DT, n / FPS, ent=0.01, sai=0.01)
gravar_partida(p, n, mundo="bosque")

plano("5 quem sai do compasso...")
i_b, t_b = TROPECO_B
b_ini = math.floor(t_b / DB) - 3          # tres batidas antes do tropeco
fx.glitch(t_video(), 0.08, 0.8)
p = nova_partida("bosque", 9, pular={i_b})
avancar(p, b_ini * DB - DT)
t0 = t_video()
reino("QUEM SAI DO COMPASSO...", t0 + 0.15, t0 + 60, COR["bosque"], 46)
clip("bosque", TRILHAS["bosque"].inicio + p.est.tempo + DT, 0.0, tapestop=0.35)
inicio = t_video()
gravando[0] = True
batido = None
while True:
    tela = quadro_app()
    fx.foco = foco_heroi(p)
    emitir(tela)
    if p.est.dano and batido is None:
        batido = t_video()
    if batido is not None and t_video() - batido >= 0.3:
        break
gravando[0] = False
musica[-1]["dur"] = batido - inicio
fx.textos[-1] = fx.textos[-1][:2] + (t_video(),) + fx.textos[-1][3:]
t0 = t_video()
som("estatica", dur=1.5, ganho=1.0)
reino("...VIRA RUÍDO.", t0 + 0.1, t0 + 1.5, (255, 70, 190), 60)
for n in range(round(1.5 * FPS)):
    tela = app.janela.screen
    tela.blit(estatica[(n // 2) % 4], (0, 0))
    emitir(tela)
preto(0.35)

plano("6 o mapa: cinco mundos ate em casa")
save.recordes = {}                    # o mapa de quem acabou de chegar: nada vencido
mapa = menus.TelaFases(app)
dicas_orig = ui.dicas
ui.dicas = lambda *a, **k: None                       # o mapa sem o rodape de teclas
DUR_MAPA = 4.8
t0 = t_video()
som("drone", dur=DUR_MAPA, ganho=0.35)
som("riser", t=t0 + DUR_MAPA - 1.6, dur=1.6, ganho=0.6)
leo("CINCO MUNDOS...", t0 + 0.3, t0 + 2.4, y=668)
leo("...ATÉ EM CASA.", t0 + 2.6, t0 + DUR_MAPA - 0.1, y=668)
movimentos = {round(x * FPS) for x in (0.7, 1.35, 2.0, 2.65)}
for n in range(round(DUR_MAPA * FPS)):
    if n in movimentos:
        mapa.evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0, unicode=""))
        efeito("navegar")
    mapa.atualizar(DT)
    tela = app.janela.screen
    mapa.desenhar(tela)
    emitir(tela, escuro=max(0.0, 1 - n / 12))
ui.dicas = dicas_orig

plano("7 Dunas, mundo 2 de 5")
t0 = t_video()
fx.flash(t0, 0.1)
fx.tranco(t0, 12, 0.3)
som("boom", t=t0, ganho=0.7)
reino("MUNDO 2 DE 5", tb(t0, 16, DD, 16.1), tb(t0, 16, DD, 18.3), COR["dunas"], 44)
leo("NEM TODA BATIDA É PULO.", tb(t0, 16, DD, 18.6), tb(t0, 16, DD, 23.8))


def no_drop_dunas(p, k, tela):
    if k == 0:
        p.cam.sacudir(10.0)
cena("dunas", 16, 8, semente=4, cada_quadro=no_drop_dunas)

plano("8 Ilhas, mundo 3 de 5")
fx.glitch(t_video(), 0.08, 0.8)
som("whoosh", t=t_video() - 0.15, dur=0.25, ganho=0.45)
t0 = t_video()
som("riser", t=t0, dur=4 * DI, ganho=0.55)
t_drop = tb(t0, 12, DI, 16)
fx.flash(t_drop, 0.1)
fx.tranco(t_drop, 14, 0.3)
som("boom", t=t_drop, ganho=0.6)
reino("MUNDO 3 DE 5", tb(t0, 12, DI, 12.2), tb(t0, 12, DI, 15.8), COR["ilhas"], 44)
leo("O CHÃO FICOU PARA TRÁS.", tb(t0, 12, DI, 17), tb(t0, 12, DI, 23.8))


def no_drop_ilhas(p, k, tela):
    if abs(k / FPS - 4 * DI) < DT / 2:
        p.cam.sacudir(12.0)
cena("ilhas", 12, 12, semente=2, cada_quadro=no_drop_ilhas)

plano("9 Geleira, mundo 4 de 5")
fx.glitch(t_video(), 0.08, 0.8)
som("whoosh", t=t_video() - 0.15, dur=0.25, ganho=0.45)
t0 = t_video()
som("riser", t=t0, dur=4 * DG, ganho=0.6)
t_drop = tb(t0, 140, DG, 144)
fx.flash(t_drop, 0.1)
fx.tranco(t_drop, 14, 0.3)
som("boom", t=t_drop, ganho=0.65)
reino("MUNDO 4 DE 5", tb(t0, 140, DG, 140.2), tb(t0, 140, DG, 143.8), COR["geleira"], 44)
leo("AQUI, SÓ UM TOQUE.", tb(t0, 140, DG, 145), tb(t0, 140, DG, 151.8))


def no_drop_geleira(p, k, tela):
    if abs(k / FPS - 4 * DG) < DT / 2:
        p.cam.sacudir(12.0)
cena("geleira", 140, 12, semente=6, cada_quadro=no_drop_geleira)

plano("10 a montagem: o mundo acelera")
CORTES = [("dunas", 136, 2), ("ilhas", 152, 2), ("geleira", 196, 2), ("eclipse", 64, 2),
          ("bosque", 92, 1), ("dunas", 152, 1), ("ilhas", 160, 1), ("geleira", 200, 1), ("eclipse", 68, 1)]
for j, (mundo, b0, nb) in enumerate(CORTES):
    t0 = t_video()
    fx.glitch(t0, 0.07 if nb > 1 else 0.05, 0.9)
    som("whoosh", t=t0 - 0.12, dur=0.22, ganho=0.45)
    if mundo == "eclipse":
        fx.flash(t0, 0.06, forca=0.6)
    cena(mundo, b0, nb, semente=20 + j)

# =========================================================== III. A VOLTA
plano("11 a queda: o Leo vira ruido")
i_e, t_e = TROPECO_E
b_ini = 4 * int(t_e / DE / 4) - 4
fx.flash(t_video(), 0.06, forca=0.6)
p = nova_partida("eclipse", 5, pular={i_e})
p.est.vidas = 1                                        # um coracao so: agora e de verdade
avancar(p, b_ini * DE - DT)
clip("eclipse", TRILHAS["eclipse"].inicio + p.est.tempo + DT, 0.0, tapestop=0.55)
inicio = t_video()
gravando[0] = True
batido = None
while True:
    tela = quadro_app()
    fx.foco = foco_heroi(p)
    emitir(tela)
    if p.est.dano and batido is None:
        batido = t_video()
        fx.z_manual = 1.0
    if batido is not None:
        fx.z_manual = 1 + 0.12 * suave((t_video() - batido) / 1.2)
        if p.morte is not None and p.morte.t >= 1.35:
            break
gravando[0] = False
fx.z_manual = 1.0
musica[-1]["dur"] = batido - inicio

plano("12 no escuro: a familia")
t0 = t_video()
som("coracao", t=t0 + 0.2, ganho=1.0)
som("coracao", t=t0 + 1.0, ganho=0.85)
leo("EU PRECISO VOLTAR...", t0 + 0.35, t0 + 2.0)
preto(2.0)
foto = pygame.transform.scale_by(_png("foto.png"), 20)
calor = pygame.Surface((LARGURA, ALTURA))
for r in range(330, 0, -6):
    pygame.draw.circle(calor, (int(60 * (1 - r / 330)), int(36 * (1 - r / 330)), int(20 * (1 - r / 330))),
                       (LARGURA // 2, 320), r)
t0 = t_video()
som("coracao", t=t0 + 0.5, ganho=0.7)
leo("...PARA CASA.", t0 + 0.3, t0 + 2.0)
fx.foco = (LARGURA / 2, 320)
fx.empurra = (t0, t0 + 2.0, 1.0, 1.08)
for n in range(round(2.0 * FPS)):
    tela = app.janela.screen
    tela.blit(calor, (0, 0))
    tela.blit(foto, foto.get_rect(center=(LARGURA // 2, 320)))
    emitir(tela, escuro=max(0.0, 1 - n / 18, (n - 1.6 * FPS) / (0.4 * FPS)))
fx.empurra = None

plano("13 de novo: a Cidadela, mundo 5 de 5")
t0 = t_video()
som("riser", t=t0, dur=8 * DE, ganho=0.75)
leo("DE NOVO.", tb(t0, 24, DE, 24.15), tb(t0, 24, DE, 27.8), 44)
reino("MUNDO 5 DE 5", tb(t0, 24, DE, 28), tb(t0, 24, DE, 31.7), COR["eclipse"], 52)
t_drop = tb(t0, 24, DE, 32)
fx.flash(t_drop, 0.14)
fx.tranco(t_drop, 20, 0.4)
som("boom", t=t_drop, ganho=1.0)
for b in (36, 40):
    fx.zoom(tb(t0, 24, DE, b), 1.12, 0.45)
fx.zoom(t_drop, 1.15, 0.5)


def no_drop_eclipse(p, k, tela):
    if abs(k / FPS - 8 * DE) < DT / 2:
        p.cam.sacudir(18.0)
cena("eclipse", 24, 20, semente=3, cada_quadro=no_drop_eclipse)

plano("14 o portal de volta")
fx.glitch(t_video(), 0.06, 0.7)
p = nova_partida("eclipse", 3)
avancar(p, 248 * DE - DT)                         # o eclipse total, ate o portal
clip("eclipse", TRILHAS["eclipse"].inicio + p.est.tempo + DT, 30.0, sai=0.01)
inicio = t_video()
gravando[0] = True
venceu_em = None
while True:
    tela = quadro_app()
    if isinstance(app.tela, P.Partida):
        fx.foco = foco_heroi(app.tela)
    if venceu_em is None and p.est.venceu:
        venceu_em = t_video()
    claro = 0.0 if venceu_em is None else max(0.0, (t_video() - venceu_em - 0.5) / 0.45)
    emitir(tela, claro=claro)
    if claro >= 1.0:
        break
gravando[0] = False
musica[-1].update(dur=t_video() - inicio + 0.8, sai=1.2)
# fora da tela, o jogo segue ate a tela de resultado carimbar a nota: e ela que a TV mostra
for _ in range(int(12 * FPS)):
    quadro_app()
    if isinstance(app.tela, menus.TelaResultado) and app.tela.tempo > 2.6:
        break
resultado = app.tela

plano("15 casa, 06:00")
manha = Quarto("quarto_manha", "south.png")
DUR_MANHA = 6.6
DUR_FINAL = 6.0
t0 = t_video()
clip("bosque", TRILHAS["bosque"].inicio + 104 * DB, DUR_MANHA + DUR_FINAL, ent=0.9, sai=1.8, ganho=0.85)
leo("CASA.", t0 + 1.7, t0 + 4.4, 40, y=Y_QUARTO)
fx.foco = FOCO_QUARTO
fx.empurra = (t0, t0 + DUR_MANHA, 1.0, 1.06)
for n in range(round(DUR_MANHA * FPS)):
    t = n * DT
    tela = app.janela.screen
    chiado = 0.0
    if t > 4.9:                                       # a TV ainda nao terminou com ele
        chiado = 0.9 if int(t * 14) % 3 else 0.4
    if n == round(4.9 * FPS):
        som("estatica", dur=DUR_MANHA - 4.9, ganho=0.7)
        som("glitch", dur=0.3, ganho=0.6)
        fx.glitch(t_video(), 0.1, 0.5)
    manha.desenhar(tela, t, jogo_na_tv(resultado, DT), luz=0.35, chiado=chiado)
    emitir(tela, claro=max(0.0, 1 - t / 0.9))
fx.empurra = None

plano("16 logo final")
t0 = t_video()
fx.flash(t0, 0.2)
fx.tranco(t0, 10, 0.3)
som("boom", ganho=1.0)
menu = Logo(app)
fx.texto("UM BOTÃO. CINCO MUNDOS. O CAMINHO DE CASA.", t0 + 0.5, t0 + DUR_FINAL, 24, AMARELO, 414)
fx.texto("FEITO POR: MATHEUS CASTRO E HENRIQUE MENDES", t0 + 0.9, t0 + DUR_FINAL, 20, BRANCO, 458, "fixo")
creditos = [
    ("DESENVOLVIDO COM POWER PPLAY 2.0  -  IC-UFF", 18, 540),
    ("MÚSICAS: DOSI & AISAKE, CLARX & HARDDOPE, SHIP WREK & ZOOKEEPERS", 16, 580),
    ("MUSIC PROVIDED BY NOCOPYRIGHTSOUNDS - NCS.IO", 16, 606),
    ("TRILHAS ORIGINAIS: CHOCALHO DAS DUNAS, AURORA DE CRISTAL", 16, 632),
    ("HERÓI: OZZBIT GAMES", 16, 658),
]
for n in range(round(DUR_FINAL * FPS)):
    t = n * DT
    menu.atualizar(DT)
    tela = app.janela.screen
    menu.desenhar(tela)
    a = suave((t - 1.0) / 0.4)
    if a > 0:
        for s, tam, y in creditos:
            img = ui.texto(s, tam, CINZA, CONTORNO)
            if a < 1:
                img = arte.fantasma(img, max(16, int(255 * a) // 16 * 16))
            tela.blit(img, img.get_rect(center=(LARGURA // 2, y)))
    emitir(tela, max(0.0, (t - (DUR_FINAL - 1.1)) / 1.1))

total = t_video()
print(f"video: {total:.2f}s, {quadros[0]} quadros, {len(sfx)} efeitos do jogo, {len(synth)} sintetizados")
for a in sorted(set(avisos)):
    print("   [aviso]", a)
timeline = os.path.join(tmp, "timeline.json")
json.dump({"dur": total, "musica": musica, "sfx": sfx, "synth": synth, "planos": planos,
           "sfx_dir": f"{RAIZ}/assets/sfx"}, open(timeline, "w"), indent=1)
if PREVIEW:
    json.dump(planos, open(os.path.join(PREVIEW, "planos.json"), "w"), indent=1)
    raise SystemExit(0)

ff.stdin.close()
ff.wait()
wav = os.path.join(tmp, "audio.wav")
# a mixagem usa numpy, que nao e dependencia do jogo: vale o python do sistema se o do .venv nao tiver
try:
    import numpy  # noqa: F401
    py = sys.executable
except ImportError:
    py = "python3"
subprocess.run([py, os.path.join(RAIZ, "ferramentas", "geradores", "trailer_mix.py"), timeline, wav], check=True)
# o YouTube toca tudo a -14 LUFS: o audio ja sai nesse nivel (medido e corrigido aqui)
medida = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af", "ebur128", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
lufs = float([l for l in medida.splitlines() if l.strip().startswith("I:")][-1].split()[1])
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", MUDO, "-i", wav,
                "-c:v", "copy", "-af", f"volume={-14.0 - lufs:.2f}dB", "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
                "-metadata", f"title={TITULO}", "-movflags", "+faststart", "-shortest", SAIDA], check=True)
subprocess.run(["rm", "-rf", tmp])
print(f"pronto: {SAIDA}  (audio corrigido de {lufs:.1f} para -14 LUFS)")
