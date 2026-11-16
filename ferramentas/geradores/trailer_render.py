"""Trailer: roda o jogo sem janela, aplica a direcao (cortes no compasso, punch-in,
flash, tranco, glitch, letterbox, texto cinetico) e manda cada quadro ao ffmpeg.
Uso: render.py <video_mudo.mp4> <timeline.json> [--preview DIR]"""
import json, math, os, random, subprocess, sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = "/home/matheus/Documentos/jogoUFF"
sys.path.insert(0, RAIZ)
sys.dont_write_bytecode = True
import pygame

SAIDA, TIMELINE = sys.argv[1], sys.argv[2]
PREVIEW = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None
FPS = 60
DT = 1.0 / FPS

import main
from jogo import arte, fases, menus, ui
from jogo import partida as P
from jogo.audio import audio, TRILHAS
from jogo.config import LARGURA, ALTURA, CONTORNO, BRANCO, CINZA, AMARELO, VERMELHO, PASSO_FISICA, JOGADOR_TAM
from jogo.save import save

random.seed(7)
save.salvar = lambda: None
app = main.App()
app.transicao.estado = 0
sfx, synth, musica = [], [], []
gravando = [False]
audio.tocar = lambda nome: gravando[0] and nome not in ("navegar", "clique") and sfx.append((t_video(), nome))
for m in ("tocar_musica", "parar_musica", "pausar_musica", "retomar_musica"):
    setattr(audio, m, lambda *a: None)

ff = None if PREVIEW else subprocess.Popen(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
     "-s", f"{LARGURA}x{ALTURA}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
     "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", SAIDA], stdin=subprocess.PIPE)
quadros = [0]
planos = []


def t_video():
    return quadros[0] / FPS


def plano(nome):
    planos.append((round(t_video(), 3), nome))
    print(f"{t_video():6.2f}s  {nome}")


def som(tipo, t=None, **k):
    synth.append({"t": t_video() if t is None else t, "tipo": tipo, **k})


def clip(cancao, origem, dur, ent=0.01, sai=0.01, ganho=1.0, tapestop=0.0):
    musica.append({"t": t_video(), "arquivo": f"{RAIZ}/assets/music/{cancao}.mp3", "origem": origem,
                   "dur": dur, "ent": ent, "sai": sai, "ganho": ganho, "tapestop": tapestop})


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


class FX:
    def __init__(self):
        self.zooms, self.flashes, self.trancos, self.glitches, self.textos = [], [], [], [], []
        self.empurra = None
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

    def texto(self, s, t0, t1, tam=56, cor=BRANCO, y=None, pop=True):
        self.textos.append((s, t0, t1, tam, cor, ALTURA // 2 if y is None else y, pop))

    def z_agora(self, t):
        z = 1.0
        if self.empurra and self.empurra[0] <= t <= self.empurra[1]:
            t0, t1, z0, z1 = self.empurra
            z = z0 + (z1 - z0) * suave((t - t0) / (t1 - t0))
        for t0, pico, dur in self.zooms:
            d = t - t0
            if 0 <= d < dur:
                k = suave(d / 0.07) if d < 0.07 else 1 - suave((d - 0.07) / (dur - 0.07))
                z = max(z, 1 + (pico - 1) * k)
        return z


fx = FX()
veu = pygame.Surface((LARGURA, ALTURA))
_texto_cache = {}


def _txt(s, tam, cor):
    k = (s, tam, cor)
    if k not in _texto_cache:
        _texto_cache[k] = ui.texto(s, tam, cor, CONTORNO)
    return _texto_cache[k]


def _glitchar(tela, k, rnd):
    w, h = tela.get_size()
    src = tela.copy()
    dx = int(3 + 12 * k)
    r = src.copy(); r.fill((255, 0, 0), special_flags=pygame.BLEND_MULT)
    gb = src.copy(); gb.fill((0, 255, 255), special_flags=pygame.BLEND_MULT)
    tela.fill((0, 0, 0))
    tela.blit(r, (dx, 0), special_flags=pygame.BLEND_ADD)
    tela.blit(gb, (-dx, 0), special_flags=pygame.BLEND_ADD)
    for _ in range(int(3 + 9 * k)):
        y = rnd.randrange(h)
        hh = min(rnd.randrange(4, 44), h - y)
        off = rnd.randint(-int(70 * k), int(70 * k))
        tela.blit(tela.subsurface((0, y, w, hh)).copy(), (off, y))


def pos_producao(tela, t):
    rnd = random.Random(quadros[0])
    z = fx.z_agora(t)
    if z > 1.001:
        cw, ch = int(LARGURA / z), int(ALTURA / z)
        x = min(max(int(fx.foco[0] - cw / 2), 0), LARGURA - cw)
        y = min(max(int(fx.foco[1] - ch / 2), 0), ALTURA - ch)
        tela.blit(pygame.transform.smoothscale(tela.subsurface((x, y, cw, ch)), (LARGURA, ALTURA)), (0, 0))
    amp = 0.0
    for t0, a, dur in fx.trancos:
        if 0 <= t - t0 < dur:
            amp = max(amp, a * (1 - (t - t0) / dur))
    if amp >= 1:
        copia = tela.copy()
        tela.fill((0, 0, 0))
        tela.blit(copia, (rnd.randint(-int(amp), int(amp)), rnd.randint(-int(amp), int(amp))))
    for t0, dur, k in fx.glitches:
        if 0 <= t - t0 < dur:
            _glitchar(tela, k * (1 - 0.5 * (t - t0) / dur), rnd)
            break
    for s, t0, t1, tam, cor, y, pop in fx.textos:
        if not (t0 <= t < t1):
            continue
        img = _txt(s, tam, cor)
        d = t - t0
        esc = 1 + 0.6 * (1 - suave(d / 0.12)) if pop else 1.0
        if t1 - t < 0.1:
            esc *= 0.6 + 0.4 * (t1 - t) / 0.1
        if abs(esc - 1) > 0.01:
            img = pygame.transform.scale(img, (max(1, int(img.get_width() * esc)), max(1, int(img.get_height() * esc))))
        sombra = img.copy(); sombra.fill((0, 0, 0, 160), special_flags=pygame.BLEND_RGBA_MULT)
        r = img.get_rect(center=(LARGURA // 2, int(y)))
        tela.blit(sombra, r.move(5, 5))
        tela.blit(img, r)
    for t0, dur, cor, forca in fx.flashes:
        if 0 <= t - t0 < dur:
            veu.fill(cor)
            veu.set_alpha(int(255 * forca * (1 - (t - t0) / dur)))
            tela.blit(veu, (0, 0))
    if fx.barras > 0:
        b = int(92 * fx.barras)
        tela.fill((0, 0, 0), (0, 0, LARGURA, b))
        tela.fill((0, 0, 0), (0, ALTURA - b, LARGURA, b))


def emitir(tela, escuro=0.0):
    pos_producao(tela, t_video())
    if escuro > 0:
        veu.fill((0, 0, 0))
        veu.set_alpha(int(255 * min(1.0, escuro)))
        tela.blit(veu, (0, 0))
    if PREVIEW:
        if quadros[0] % 45 == 0:
            pygame.image.save(tela, os.path.join(PREVIEW, f"q{quadros[0]:05d}.png"))
    else:
        ff.stdin.write(pygame.image.tobytes(tela, "RGB"))
    quadros[0] += 1


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


def nova_partida(indice, semente, pular=()):
    p = P.Partida(app, fases.carregar(indice))
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


def cena(indice, beat0, beats, semente=1, pular=(), musica_on=True, ent=0.01, sai=0.01,
         ganho=1.0, cada_quadro=None):
    p = nova_partida(indice, semente, pular)
    dur = p.fase.dur_batida
    if beat0 > 0:
        avancar(p, beat0 * dur - DT)
    n = round(beats * dur * FPS)
    if musica_on:
        clip(p.fase.cancao, TRILHAS[p.fase.cancao].inicio + p.est.tempo + DT, n / FPS, ent, sai, ganho)
    gravando[0] = True
    for k in range(n):
        tela = quadro_app()
        fx.foco = foco_heroi(p)
        if cada_quadro:
            cada_quadro(p, k, tela)
        if p.est.dano:
            print(f"   [aviso] dano fora do roteiro: fase {indice} t={p.est.tempo:.2f}")
        emitir(tela)
    gravando[0] = False
    return p


def tb(t0, beat0, dur, b):
    return t0 + (b - beat0) * dur


bosque, ilhas, eclipse = (fases.carregar(i) for i in range(3))
DB, DI, DE = bosque.dur_batida, ilhas.dur_batida, eclipse.dur_batida
Y_LEG = 585


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


def achar_tropeco():
    for i, b in enumerate(eclipse.acoes):
        if b < 140:
            continue
        p = nova_partida(2, 5, pular={i})
        avancar(p, b * DE - 0.5)
        while p.modo == P.JOGANDO and p.est.tempo < b * DE + 1.5:
            p.atualizar(DT)
            if p.est.dano:
                if p.est.dano == "perigo":
                    return i, p.est.tempo
                break
    raise SystemExit("nenhum tropeco achado")

TROPECO_I, TROPECO_T = achar_tropeco()
print(f"tropeco: acao {TROPECO_I}, dano em {TROPECO_T:.2f}s (batida {TROPECO_T / DE:.1f})")

ruidos = []
for s in range(4):
    r = random.Random(s)
    img = pygame.Surface((320, 180))
    for y in range(180):
        for x in range(320):
            v = r.randrange(0, 34)
            img.set_at((x, y), (v, v, v + 6))
    ruidos.append(pygame.transform.scale(img, (LARGURA, ALTURA)))

# ================================================================ roteiro
plano("0 preto")
fx.barras = 1.0
som("riser", dur=0.8, ganho=0.8)
for n in range(int(0.8 * FPS)):
    tela = app.janela.screen
    tela.fill((0, 0, 0))
    emitir(tela)

plano("1 gancho - cidadela drop final")
t0 = t_video()
fx.flash(t0, 0.12)
fx.tranco(t0, 18, 0.35)
fx.empurra = (t0, t0 + 8 * DE, 1.0, 1.1)
fx.zoom(tb(t0, 224, DE, 228), 1.16, 0.4)
som("boom", ganho=0.7)


def no_gancho(p, k, tela):
    if k == 0:
        p.cam.sacudir(16.0)
cena(2, 224, 8, semente=11, cada_quadro=no_gancho, sai=0.005)
fx.empurra = None

plano("2 premissa")
som("boom", ganho=0.9)
som("drone", dur=3.4)
L1, L2 = "LEO JOGAVA DE MADRUGADA...", "...ATE A TELA O PUXAR."
for n in range(int(3.4 * FPS)):
    t = n * DT
    tela = app.janela.screen
    tela.blit(ruidos[(n // 3) % 4], (0, 0))
    ui.escurecer_tela(tela, 120)
    if 0.25 <= t < 1.85:
        k = min(len(L1), int((t - 0.25) / 0.045) + 1)
        if n % 3 == 0 and (t - 0.25) / 0.045 < len(L1) and L1[k - 1] != " ":
            som("tick", ganho=0.5)
        img = _txt(L1[:k], 46, BRANCO)
        tela.blit(img, img.get_rect(midleft=(LARGURA // 2 - _txt(L1, 46, BRANCO).get_width() // 2, ALTURA // 2)))
    if 1.95 <= t:
        img = _txt(L2, 50, BRANCO)
        tela.blit(img, img.get_rect(center=(LARGURA // 2, ALTURA // 2)))
    if n == int(1.95 * FPS):
        fx.glitch(t_video(), 0.35, 1.0)
        som("glitch", dur=0.4, ganho=0.7)
    if n == int(2.9 * FPS):
        fx.glitch(t_video(), 0.5, 1.4)
        som("glitch", dur=0.5, ganho=0.8)
        som("riser", dur=0.5, ganho=0.6)
    emitir(tela)

plano("3 logo")
t0 = t_video()
fx.barras = 0.0
fx.flash(t0, 0.18)
fx.tranco(t0, 12, 0.3)
som("boom", ganho=1.0)
clip("bosque", TRILHAS["bosque"].inicio + 8 * DB, 4 * DB + 0.05, ent=0.02, sai=0.01)
menu = Logo(app)
fx.texto("UM BOTAO. NO RITMO.", t0 + 0.9, t0 + 4 * DB - 0.05, 30, bosque.tema.destaque, y=430)
for n in range(round(4 * DB * FPS)):
    menu.atualizar(DT)
    tela = app.janela.screen
    menu.desenhar(tela)
    emitir(tela)

plano("4 bosque")
t0 = t_video()
fx.texto("PULE", tb(t0, 12, DB, 12.0), tb(t0, 12, DB, 15.8), 64, bosque.tema.destaque, y=Y_LEG)
fx.texto("NA BATIDA", tb(t0, 12, DB, 16.0), tb(t0, 12, DB, 19.8), 64, BRANCO, y=Y_LEG)
fx.zoom(tb(t0, 12, DB, 16), 1.12, 0.6)
cena(0, 12, 8, semente=1, musica_on=False)
musica[-1]["dur"] += 8 * DB
fx.glitch(t_video() - 0.05, 0.12, 0.8)
som("whoosh", t=t_video() - 0.25, dur=0.35, ganho=0.6)

plano("5 ilhas")
t0 = t_video()
som("riser", t=t0, dur=4 * DI, ganho=0.55)
t_drop = tb(t0, 28, DI, 32)
fx.flash(t_drop, 0.1)
fx.tranco(t_drop, 14, 0.3)
som("boom", t=t_drop, ganho=0.6)
fx.texto("110 BPM", t_drop, tb(t0, 28, DI, 35.8), 72, ilhas.tema.destaque, y=Y_LEG)
fx.texto("O MUNDO ACELERA", tb(t0, 28, DI, 36), tb(t0, 28, DI, 39.8), 56, BRANCO, y=Y_LEG)
fx.zoom(tb(t0, 28, DI, 36), 1.1, 0.5)


def no_drop_ilhas(p, k, tela):
    if abs(k / FPS - 4 * DI) < DT / 2:
        p.cam.sacudir(12.0)
cena(1, 28, 16, semente=2, cada_quadro=no_drop_ilhas)

plano("6 montagem")
CORTES = [(0, 140, 4), (1, 164, 4), (2, 100, 4), (1, 172, 2), (2, 108, 2), (1, 176, 1), (2, 112, 1)]
for j, (ind, b0, nb) in enumerate(CORTES):
    t0 = t_video()
    if j:
        fx.glitch(t0, 0.07 if nb > 1 else 0.05, 0.9)
        som("whoosh", t=t0 - 0.12, dur=0.22, ganho=0.45)
    if ind == 2:
        fx.flash(t0, 0.06, forca=0.6)
    if nb >= 4:
        fx.zoom(t0 + 0.02, 1.1, 0.4)
    cena(ind, b0, nb, semente=20 + j)

plano("7 tropeco")
b_ini = 4 * int(TROPECO_T / DE / 4) - 4
fx.flash(t_video(), 0.06, forca=0.6)
p = nova_partida(2, 5, pular={TROPECO_I})
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
    if batido is not None and t_video() - batido >= 0.12:
        break
gravando[0] = False
musica[-1]["dur"] = t_video() - inicio
congelado = app.janela.screen.copy()
foco = fx.foco
t0 = t_video()
fx.flash(t0, 0.15, VERMELHO, 0.7)
fx.texto("ERROU A BATIDA?", t0 + 0.12, t0 + 0.85, 52, VERMELHO, y=Y_LEG)
DUR_GELO = 0.9
for n in range(int(DUR_GELO * FPS)):
    cinza = pygame.transform.grayscale(congelado)
    cinza.set_alpha(int(255 * suave(n / (DUR_GELO * FPS * 0.6))))
    tela = app.janela.screen
    tela.blit(congelado, (0, 0))
    tela.blit(cinza, (0, 0))
    z = 1 + 0.18 * suave(n / (DUR_GELO * FPS))
    cw, ch = int(LARGURA / z), int(ALTURA / z)
    x = min(max(int(foco[0] - cw / 2), 0), LARGURA - cw)
    y = min(max(int(foco[1] - ch / 2), 0), ALTURA - ch)
    tela.blit(pygame.transform.smoothscale(tela.subsurface((x, y, cw, ch)).copy(), (LARGURA, ALTURA)), (0, 0))
    emitir(tela)
t0 = t_video()
som("coracao", t=t0 + 0.15, ganho=1.0)
som("coracao", t=t0 + 0.85, ganho=0.8)
fx.texto("O RITMO NAO PERDOA.", t0 + 0.2, t0 + 1.6, 48, BRANCO, pop=False)
for n in range(int(1.6 * FPS)):
    tela = app.janela.screen
    tela.fill((0, 0, 0))
    emitir(tela)

plano("8 climax cidadela")
t0 = t_video()
som("riser", t=t0, dur=8 * DE, ganho=0.75)
fx.texto("CIDADELA DO ECLIPSE", tb(t0, 56, DE, 56.3), tb(t0, 56, DE, 59.8), 52, eclipse.tema.destaque, y=Y_LEG)
fx.texto("A PROVA FINAL", tb(t0, 56, DE, 60), tb(t0, 56, DE, 63.6), 52, BRANCO, y=Y_LEG)
t_drop = tb(t0, 56, DE, 64)
fx.flash(t_drop, 0.14)
fx.tranco(t_drop, 20, 0.4)
som("boom", t=t_drop, ganho=1.0)
fx.texto("150 BPM", t_drop, tb(t0, 56, DE, 67.8), 84, eclipse.tema.perigo, y=Y_LEG)
for b in (68, 72):
    fx.zoom(tb(t0, 56, DE, b), 1.12, 0.45)
fx.zoom(t_drop, 1.15, 0.5)


def no_drop_eclipse(p, k, tela):
    if abs(k / FPS - 8 * DE) < DT / 2:
        p.cam.sacudir(18.0)
cena(2, 56, 20, semente=3, cada_quadro=no_drop_eclipse)

plano("9 vitoria")
fx.glitch(t_video(), 0.06, 0.7)
p = nova_partida(2, 3)
avancar(p, 320 * DE - DT)
clip("eclipse", TRILHAS["eclipse"].inicio + p.est.tempo + DT, 30.0, sai=0.01)
inicio = t_video()
gravando[0] = True
for n in range(int(14 * FPS)):
    tela = quadro_app()
    if isinstance(app.tela, P.Partida):
        fx.foco = foco_heroi(app.tela)
    emitir(tela)
    if isinstance(app.tela, menus.TelaResultado) and app.tela.tempo > 2.2:
        break
gravando[0] = False
musica[-1].update(dur=t_video() - inicio + 0.6, sai=1.0)

plano("10 logo final")
t0 = t_video()
FINAL = 5.2
fx.flash(t0, 0.2)
fx.tranco(t0, 10, 0.3)
som("boom", ganho=1.0)
clip("bosque", TRILHAS["bosque"].inicio + 196 * DB, FINAL, ent=0.05, sai=1.6, ganho=0.9)
menu = Logo(app)
fx.texto("3 MUNDOS. 3 MUSICAS. 1 BOTAO.", t0 + 0.5, t0 + FINAL, 28, AMARELO, y=420)
creditos = [
    ("FEITO COM POWER PPLAY 2.0  -  IC-UFF", 18, 540),
    ("MUSICAS: DOSI & AISAKE, CLARX & HARDDOPE, SHIP WREK & ZOOKEEPERS", 16, 584),
    ("MUSIC PROVIDED BY NOCOPYRIGHTSOUNDS - NCS.IO", 16, 610),
    ("HEROI: OZZBIT GAMES", 16, 636),
]
for n in range(int(FINAL * FPS)):
    t = n * DT
    menu.atualizar(DT)
    tela = app.janela.screen
    menu.desenhar(tela)
    a = suave((t - 1.0) / 0.4)
    if a > 0:
        for s, tam, y in creditos:
            img = _txt(s, tam, CINZA)
            if a < 1:
                img = arte.fantasma(img, max(16, int(255 * a) // 16 * 16))
            tela.blit(img, img.get_rect(center=(LARGURA // 2, y)))
    emitir(tela, max(0.0, (t - (FINAL - 1.1)) / 1.1))

total = t_video()
if ff:
    ff.stdin.close()
    ff.wait()
json.dump({"dur": total, "musica": musica, "sfx": sfx, "synth": synth, "planos": planos,
           "sfx_dir": f"{RAIZ}/assets/sfx"}, open(TIMELINE, "w"), indent=1)
print(f"video: {total:.2f}s, {quadros[0]} quadros, {len(sfx)} efeitos do jogo, {len(synth)} sintetizados")
assert total <= 60.0, "passou de 60 s"
