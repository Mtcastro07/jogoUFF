"""
Arte: os quadros do heroi (recortados da spritesheet) e os poucos desenhos
gerados por codigo (cacos, blocos, coracoes, enfeites). Tudo fica em cache:
cada desenho e feito uma vez e depois so e copiado para a tela.
"""

import os
import re

import pygame

from .config import SPRITESHEET, TILE, RAIZ, LEO_DESENHADO

DIR_ART = os.path.join(RAIZ, "assets", "art")

# A spritesheet e uma grade de celulas de 128x128. Dentro de cada celula o
# heroi ocupa um retangulo pequeno; recortamos so ele e ampliamos 2x.
CELULA = 128
RECORTE = pygame.Rect(28, 24, 72, 60)
ESCALA = 2
PES = 56 * ESCALA          # linha dos pes dentro do quadro ampliado
CENTRO = 32 * ESCALA       # centro horizontal do heroi dentro do quadro

# nome -> (linha da spritesheet, numero de quadros)
ANIMACOES = {"parado": (1, 10), "corre": (3, 10), "pula": (4, 6), "segura": (5, 3)}

# O Leo desenhado para o jogo (assets/art/personagens/), no formato do gerador:
# uma pasta por animacao com frame_000.png, frame_001.png... ou uma imagem so.
# Sem ele, o jogo volta para a spritesheet da Ozzbit.
PERSONAGEM = {
    "parado": "east.png",
    "corre": "Full_Sprint/east",
    "pula": "Running_Jump/east",
}
# O pulo e escolhido pela VELOCIDADE vertical, nao pelo tempo: RAMPA sao os
# quadros do ar em ordem, do impulso ao pe descendo. TEM_POUSO diz se ha a
# animacao "pouso", o quadro do pe tocando o chao. Na Ozzbit: 1..5 no ar, sem pouso.
RAMPA = [1, 2, 3, 4, 5]
TEM_POUSO = False
# A Ozzbit tem folhas separadas de QUEDA (do apice para baixo) e de laco de
# queda, alem do pulo: com elas, a subida usa os quadros de subida e a descida
# os de queda. SUBIDA fica None quando o heroi e o Leo gerado (uma rampa so).
FOLHAS = os.path.join(os.path.dirname(SPRITESHEET), "individual_sheets")
SUBIDA = None
# Sem pose propria de sustentar a nota, o Leo corre em cima da ponte de luz --
# no compasso, como no chao.
SEGURA_CORRE = False

_quadros = {}
_ancoras = {}          # nome -> (x, y) do quadro que vai no centro do corpo e nos pes
_cache = {}
_pngs = {}


# ------------------------------------------------------- pecas geradas fora
def png(*partes):
    """Carrega assets/art/<partes>, ou None se a peca ainda nao existe."""
    chave = partes
    if chave not in _pngs:
        caminho = os.path.join(DIR_ART, *partes)
        try:
            _pngs[chave] = pygame.image.load(caminho).convert_alpha()
        except (pygame.error, FileNotFoundError):
            _pngs[chave] = None
    return _pngs[chave]


def tira(img, quadros):
    """Fatia uma tira horizontal em `quadros` superficies."""
    w = img.get_width() // quadros
    return [img.subsurface((i * w, 0, w, img.get_height())) for i in range(quadros)]


def tingir(img, cor):
    """Branco vira `cor`, cinza vira a versao escura dela. Preserva o alfa."""
    s = img.copy()
    s.fill((*cor[:3], 255), special_flags=pygame.BLEND_RGBA_MULT)
    return s


_listas = {}


def _arquivos(*pasta):
    """Nomes dos arquivos de assets/art/<pasta> (lidos uma vez)."""
    if pasta not in _listas:
        try:
            _listas[pasta] = sorted(os.listdir(os.path.join(DIR_ART, *pasta)))
        except OSError:
            _listas[pasta] = []
    return _listas[pasta]


def _achar(pasta, base):
    """
    (arquivo, quadros) da peca `base` em `pasta`, ou (None, 0). O numero de
    quadros vem do nome: `caco1_4f.png` e uma tira de 4, `caco1.png` e parada.
    Havendo as duas, vale a animada.
    """
    padrao = re.compile(re.escape(base) + r"_(\d+)f\.png")
    for nome in _arquivos(*pasta):
        m = padrao.fullmatch(nome)
        if m:
            return nome, int(m.group(1))
    if f"{base}.png" in _arquivos(*pasta):
        return f"{base}.png", 1
    return None, 0


def _peca(base, i, cor, fase=None):
    """
    Um quadro de uma peca de jogo, ou None (quem chamou desenha por codigo).
    Procura nesta ordem:

        objetos/jogo/<fase>/   colorida, do jeito que veio: so existe nesta fase
        objetos/jogo/          branca e cinza, tingida com `cor`: serve a todas
    """
    if fase is not None:
        nome, n = _achar(("objetos", "jogo", fase), base)
        if nome:
            img = png("objetos", "jogo", fase, nome)
            return _memo(("png_fase", fase, nome), lambda: tira(img, n))[int(i) % n]
    nome, n = _achar(("objetos", "jogo"), base)
    if not nome:
        return None
    img = png("objetos", "jogo", nome)
    return _memo(("png", nome, cor), lambda: [tingir(q, cor) for q in tira(img, n)])[int(i) % n]


def tem_peca(base, fase=None, so_animada=False):
    """Existe arte para esta peca (na pasta da fase ou na comum)?"""
    for pasta in ((("objetos", "jogo", fase),) if fase else ()) + (("objetos", "jogo"),):
        nome, n = _achar(pasta, base)
        if nome and (n > 1 or not so_animada):
            return True
    return False


def _variantes(fase, base):
    """[base_1, base_2, ...] que existirem, ou [base], ou []: para sortear desenhos."""
    achadas = [f"{base}_{k}" for k in range(1, 10) if tem_peca(f"{base}_{k}", fase)]
    return achadas or ([base] if tem_peca(base, fase) else [])


def recuar(img, cor, k):
    """
    Copia puxada `k` (0..1) na direcao de `cor`, mantendo o alfa: o que e
    cenario vai para tras e sai da faixa em que o jogador le o que importa.
    """
    def faz():
        s = img.copy()
        s.fill((int(255 * (1 - k)),) * 3, special_flags=pygame.BLEND_RGB_MULT)
        s.fill(tuple(int(c * k) for c in cor[:3]), special_flags=pygame.BLEND_RGB_ADD)
        return s
    return _memo(("recuar", id(img), cor, k), faz)


def fantasma(img, alfa):
    """Copia translucida (cache): a ponte apagada nao pode parecer chao firme."""
    def faz():
        s = img.copy()
        s.set_alpha(alfa)
        return s
    return _memo(("fantasma", id(img), alfa), faz)


def carregar():
    """Carrega os quadros do heroi. Chamar uma vez, depois de abrir a janela."""
    global RAMPA, TEM_POUSO, SEGURA_CORRE, SUBIDA
    proprio = _carregar_personagem() if LEO_DESENHADO else None
    if proprio is not None:
        # o pulo correndo termina no pouso: os quadros de antes sao o ar
        *ar, pouso = proprio["pula"]
        proprio["pula"] = ar
        _quadros.update(proprio)
        for nome, qs in proprio.items():
            _ancoras[nome] = _ancora(qs)
        RAMPA = list(range(len(ar)))
        # o pouso tem os PROPRIOS pes (os do ar ficam mais baixos, com a perna
        # esticada), mas o centro do pulo: chega do ar sem deslizar de lado
        _quadros["pouso"] = [pouso]
        _ancoras["pouso"] = (_ancoras["pula"][0], pouso.get_bounding_rect(min_alpha=8).bottom)
        TEM_POUSO = True
        _quadros["segura"], _ancoras["segura"] = _quadros["corre"], _ancoras["corre"]
        SEGURA_CORRE = True
        return
    folha = pygame.image.load(SPRITESHEET).convert_alpha()
    for nome, (linha, n) in ANIMACOES.items():
        _quadros[nome] = [
            pygame.transform.scale_by(
                folha.subsurface((i * CELULA + RECORTE.x, linha * CELULA + RECORTE.y,
                                  RECORTE.w, RECORTE.h)), ESCALA)
            for i in range(n)]
        _ancoras[nome] = (CENTRO, PES)
    # queda e laco de queda (folhas individuais, mesma grade de 128 px)
    queda = [(n, a) for n, a in (("cai", "male_hero-fall.png"), ("caindo", "male_hero-fall_loop.png"))
             if os.path.exists(os.path.join(FOLHAS, a))]
    for nome, arq in queda:
        tira_ = pygame.image.load(os.path.join(FOLHAS, arq)).convert_alpha()
        _quadros[nome] = [
            pygame.transform.scale_by(
                tira_.subsurface((i * CELULA + RECORTE.x, RECORTE.y, RECORTE.w, RECORTE.h)), ESCALA)
            for i in range(tira_.get_width() // CELULA)]
        _ancoras[nome] = (CENTRO, PES)
    if len(queda) == 2:
        SUBIDA = [1, 2, 3, 4, 5]
        # o quadro 0 do pulo (agachado) nunca aparecia: vira a pose do pouso
        _quadros["pouso"], _ancoras["pouso"] = [_quadros["pula"][0]], (CENTRO, PES)
        TEM_POUSO = True


def _carregar_personagem():
    """{animacao: [quadros]} do Leo desenhado para o jogo, ou None se faltar algo."""
    base = os.path.join(DIR_ART, "personagens")
    anims = {}
    for nome, rel in PERSONAGEM.items():
        caminho = os.path.join(base, rel)
        if os.path.isdir(caminho):
            arqs = sorted(a for a in os.listdir(caminho) if a.endswith(".png"))
            anims[nome] = [pygame.image.load(os.path.join(caminho, a)).convert_alpha() for a in arqs]
        elif os.path.exists(caminho):
            anims[nome] = [pygame.image.load(caminho).convert_alpha()]
        if not anims.get(nome):
            return None
    return anims


def _ancora(quadros):
    """
    O ponto de cada quadro que vai no (centro do corpo, pes) do jogador. Os pes
    sao a linha mais baixa que um pe alcanca na animacao; o centro e o da
    CABECA (as 10 linhas de cima), porque o cachecol esticado para tras puxaria
    a conta. Cada animacao do gerador tem a propria tela (a corrida e 72x72 e
    o resto 56x56, com o corpo em lugares diferentes): ancorar assim e o que
    impede o Leo de deslizar para o lado quando troca de animacao.
    """
    pes = max(q.get_bounding_rect(min_alpha=8).bottom for q in quadros)
    centros = []
    for q in quadros:
        bb = q.get_bounding_rect(min_alpha=8)
        xs = [x for y in range(bb.y, min(bb.bottom, bb.y + 10))
              for x in range(bb.x, bb.right) if q.get_at((x, y)).a > 128]
        centros.append(sum(xs) / len(xs))
    centros.sort()
    return centros[len(centros) // 2], pes


def quadro(nome, i):
    q = _quadros[nome]
    return q[int(i) % len(q)]


def n_quadros(nome):
    return len(_quadros[nome])


def quadro_do_pulo(k):
    """Quadro do pulo para `k` = 0 (acabou de sair do chao) ... 1 (caindo rapido)."""
    return RAMPA[min(len(RAMPA) - 1, max(0, int(k * len(RAMPA))))]


def quadro_no_ar(vy, v_pulo, tempo):
    """
    (animacao, quadro) do heroi no ar. Subindo, os quadros de subida pela
    velocidade (0 = acabou de sair do chao, 1 = apice); descendo, os de queda;
    caindo alem de um pulo normal (degrau abaixo, buraco), o laco de queda.
    """
    if SUBIDA is None:
        return "pula", quadro_do_pulo((vy + v_pulo) / (2.0 * v_pulo))
    if vy < 0.0:
        k = 1.0 + vy / v_pulo
        return "pula", SUBIDA[min(len(SUBIDA) - 1, max(0, int(k * len(SUBIDA))))]
    k = vy / v_pulo
    if k < 1.0:
        return "cai", min(n_quadros("cai") - 1, int(k * n_quadros("cai")))
    return "caindo", tempo * 10


def desenhar_heroi(tela, nome, i, cx, pes_y, escala=(1.0, 1.0)):
    """
    Desenha o quadro com os pes em (cx, pes_y). `escala` (largura, altura) e o
    esticar-e-amassar do pulo: cresce a partir dos pes, que nao saem do lugar.
    """
    ax, ay = _ancoras[nome]
    q = quadro(nome, i)
    sx, sy = escala
    if (sx, sy) != (1.0, 1.0):
        def faz():
            return pygame.transform.scale(q, (max(1, round(q.get_width() * sx)),
                                              max(1, round(q.get_height() * sy))))
        q = _memo(("heroi", id(q), sx, sy), faz)
        ax, ay = ax * sx, ay * sy
    tela.blit(q, (int(cx - ax), int(pes_y - ay)))


# --------------------------------------------------------------------- cores
def clarear(cor, k):
    return tuple(min(255, int(c + (255 - c) * k)) for c in cor[:3])


def escurecer(cor, k):
    return tuple(max(0, int(c * (1.0 - k))) for c in cor[:3])


# ------------------------------------------------------------------ desenhos
def _memo(chave, faz):
    s = _cache.get(chave)
    if s is None:
        s = _cache[chave] = faz()
    return s


def caco(quantidade, cor, i=0, fase=None):
    """Um tile com 1, 2 ou 3 triangulos pontudos. `i` e o quadro do glitch."""
    pronto = _peca(f"caco{quantidade}", i, cor, fase)
    if pronto is not None:
        return pronto
    def faz():
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        larg = TILE // quantidade
        for i in range(quantidade):
            x0 = i * larg
            pontos = [(x0 + 2, TILE), (x0 + larg - 2, TILE), (x0 + larg // 2, 3)]
            pygame.draw.polygon(s, cor, pontos)
            pygame.draw.polygon(s, clarear(cor, 0.5), pontos, 2)
        return s
    return _memo(("caco", quantidade, cor), faz)


def chao(fase):
    """Topo do chao proprio da fase (objetos/jogo/<fase>/chao.png), ou None."""
    return png("objetos", "jogo", fase, "chao.png")


def bloco(cor, cor_borda, fase=None):
    # tingido com a cor da BORDA, a clara: o bloco e solido como o chao, e e o
    # topo claro do chao que diz ao jogador "aqui da para pisar"
    pronto = _peca("bloco", 0, cor_borda, fase)
    if pronto is not None:
        return pronto
    def faz():
        s = pygame.Surface((TILE, TILE))
        s.fill(cor)
        pygame.draw.rect(s, cor_borda, (0, 0, TILE, TILE), 3)
        pygame.draw.rect(s, clarear(cor, 0.15), (6, 6, TILE - 12, TILE - 12), 2)
        return s
    return _memo(("bloco", cor, cor_borda), faz)


def coracao(tam, cor, cheio, pulsando=False):
    """Quadro 0 cheio, 1 cheio na batida, 2 vazio."""
    img = png("ui", "coracao_3f.png")
    if img is not None:
        quadros = _memo(("png_coracao",), lambda: tira(img, 3))
        return quadros[(1 if pulsando else 0) if cheio else 2]
    def faz():
        s = pygame.Surface((tam, tam), pygame.SRCALPHA)
        r = tam // 4
        pontos = [(1, tam * 0.4), (tam // 2, tam - 2), (tam - 1, tam * 0.4)]
        if cheio:
            pygame.draw.circle(s, cor, (r + 1, r + 2), r)
            pygame.draw.circle(s, cor, (tam - r - 1, r + 2), r)
            pygame.draw.polygon(s, cor, pontos)
        else:
            pygame.draw.circle(s, cor, (r + 1, r + 2), r, 2)
            pygame.draw.circle(s, cor, (tam - r - 1, r + 2), r, 2)
            pygame.draw.polygon(s, cor, pontos, 2)
        return s
    return _memo(("coracao", tam, cor, cheio), faz)


def coluna(w, h, cor, cor_borda, aceso=False, fase=None, variante=0):
    """`variante` escolhe entre coluna_1, coluna_2... quando a fase tem varias."""
    for base in (f"coluna_{h}", "coluna"):
        nomes = _variantes(fase, base)
        if nomes:
            return _peca(nomes[variante % len(nomes)], 1 if aceso else 0, cor, fase)
    def faz():
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, cor, (w // 4, 8, w // 2, h - 8))
        pygame.draw.rect(s, cor_borda, (2, 0, w - 4, 10))
        pygame.draw.rect(s, cor_borda, (w // 4, 8, w // 2, h - 8), 2)
        return s
    return _memo(("coluna", w, h, cor, cor_borda), faz)


def portal(w, h, cor, i=0, fase=None):
    pronto = _peca("portal", i, cor, fase)
    if pronto is not None:
        return pronto
    def faz():
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, escurecer(cor, 0.6), (0, 0, w, h))
        pygame.draw.ellipse(s, cor, (0, 0, w, h), 5)
        pygame.draw.ellipse(s, clarear(cor, 0.4), (w // 4, h // 4, w // 2, h // 2), 3)
        return s
    return _memo(("portal", w, h, cor), faz)


def chevron(cor, tam, aceso=False, fase=None):
    """Setinha apontando para baixo: a guia de "pule aqui"."""
    pronto = _peca("chevron", 1 if aceso else 0, cor, fase)
    if pronto is not None:
        if tem_peca("chevron", fase, so_animada=True):
            return pronto                  # a tira ja traz o quadro aceso
        # parada: o pulso vira tamanho, como no desenho por codigo (tam 10..16)
        def faz():
            w = max(1, pronto.get_width() * tam // 16)
            return pygame.transform.scale(pronto, (w, max(1, pronto.get_height() * tam // 16)))
        return _memo(("chevron_png", fase, cor, tam), faz)
    def faz():
        s = pygame.Surface((tam * 2, tam), pygame.SRCALPHA)
        pygame.draw.polygon(s, cor, [(0, 0), (tam * 2, 0), (tam, tam)])
        return s
    return _memo(("chevron", cor, tam), faz)


def ponte(estado, cor, i=0, fase=None, variante=0):
    """
    Um segmento de 1 tile da ponte de eco: "off" (longe dela), "pronta" (Leo na
    zona, o botao ja vale sustentar) ou "viva" (a nota esta sendo sustentada).
    `variante` alterna entre ponte_off_1, ponte_off_2... quando houver.
    None se nao ha arte: a ponte e desenhada por codigo.
    """
    nomes = _variantes(fase, f"ponte_{estado}")
    return _peca(nomes[variante % len(nomes)], i, cor, fase) if nomes else None


def ponte_pilar(cor, fase=None, variante=0):
    """O pilar que emoldura o vao da ponte, ou None. Alterna ponte_pilar_1, _2..."""
    nomes = _variantes(fase, "ponte_pilar")
    return _peca(nomes[variante % len(nomes)], 0, cor, fase) if nomes else None
