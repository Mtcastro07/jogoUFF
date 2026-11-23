"""
O final: o caminho de volta, quando o jogador vence os cinco mundos.

A cena comeca na tela de resultado da fase que acabou de ser vencida (a nota
carimba como sempre). Entao a camera sai de dentro dela: era a TV do quarto
do Leo, agora as 06:00, com o sol nascendo. A TV devolve o Leo -- o mesmo
puxao da abertura, ao contrario -- e ele cai de pe no tapete. "...Casa." Ele
desliga a TV. Depois, os creditos, com a musica do Bosque, e o menu.

Toca na primeira vez que todos os mundos ficam vencidos e, dali em diante,
sempre que a Cidadela (o portal de casa) e vencida de novo. Qualquer tecla,
clique ou botao do controle pula para o menu.
"""

import pygame

from . import arte, fases, menus, ui
from .abertura import Quarto, falhas, fase, pensamento, pular, suave
from .audio import audio
from .config import LARGURA, ALTURA, BRANCO, CINZA, AMARELO, CONTORNO, VOLUME_MUSICA

# a linha do tempo, em segundos
RESULTADO = 3.4        # a tela de resultado, cheia
SAIDA = (3.4, 4.9)     # a camera sai de dentro da TV
EJETA = (5.0, 6.2)     # a TV devolve o Leo
MUSICA = 6.6
CASA = (7.0, 9.6)      # "...casa."
DESLIGA = 10.0         # o clique: a TV apaga
CHEGA = (11.0, 13.6)   # "chega de jogo por hoje."
ESCURECE = (13.6, 14.6)
CARTOES = ((15.0, 19.8), (20.2, 25.6), (26.0, 29.8))
FIM = 30.4
FALA_CASA = "...CASA."
FALA_CHEGA = "CHEGA DE JOGO POR HOJE."


def deve_tocar(save, fase_vencida):
    """O final toca quando a vitoria fecha os cinco mundos pela primeira vez, ou
    quando a Cidadela -- o portal de casa -- e vencida com todos ja fechados."""
    todas = fases.todas()
    completas, _ = save.progresso([f.cancao for f in todas])
    if completas < len(todas):
        return False
    return not save.final_visto or fase_vencida.ident == len(todas) - 1


class Final:
    """Uma tela como as de menus.py (evento, atualizar, desenhar)."""

    def __init__(self, app, dados):
        self.app = app
        self.tempo = 0.0
        self.saindo = False
        self.feito = set()                       # os sons que ja tocaram
        self.resultado = menus.TelaResultado(app, dados)
        self.fase = self.resultado.fase          # a cor da transicao (App._cor)
        self.tv_img = pygame.Surface((LARGURA, ALTURA)).convert()
        self.resultado.desenhar(self.tv_img)
        self.quarto = Quarto("quarto_manha.png", "south.png", self.tv_img)
        self.fundo = menus.Tela(app, fases.carregar(0))    # o bosque rolando atras dos creditos
        # os cartoes e o fundo dos creditos sao montados aqui: no primeiro quadro
        # deles, montar tudo na hora passava do tempo de um quadro
        self.cartoes = [self._cartao(i) for i in range(len(CARTOES))]
        self.fundo.desenhar(pygame.Surface((LARGURA, ALTURA)).convert())
        self.veu = pygame.Surface((LARGURA, ALTURA)).convert()
        self.dica = ui.texto("ESPACO PULA", 14, (150, 156, 190), CONTORNO)
        app.save.final_visto = True
        app.save.salvar()

    # ------------------------------------------------------------ controle
    def evento(self, ev):
        if pular(ev) and self.tempo > 0.8:
            self._sair()

    def _sair(self):
        if self.saindo:
            return
        self.saindo = True
        audio.parar_musica()
        self.app.ir_para_menu()

    def _uma_vez(self, nome, t0, som=None):
        if self.tempo >= t0 and nome not in self.feito:
            self.feito.add(nome)
            if som:
                audio.tocar(som)
            return True
        return False

    def atualizar(self, dt):
        if self.saindo:
            return
        self.tempo += min(dt, 1.0 / 30.0)
        t = self.tempo
        if t < DESLIGA + 0.5:
            self.resultado.atualizar(dt)        # a nota carimba, as faiscas caem
        self._uma_vez("sai", EJETA[0], "orbe")
        self._uma_vez("pousa", EJETA[1], "eco")
        self._uma_vez("desliga", DESLIGA, "clique")
        if self._uma_vez("musica", MUSICA):
            audio.tocar_musica("bosque")
        if audio.tocando and t > FIM - 1.8:     # a musica some junto com o ultimo cartao
            k = max(0.0, (FIM - t) / 1.8)
            pygame.mixer.music.set_volume(VOLUME_MUSICA * audio.vol_musica * k)
        if t >= FIM:
            self._sair()

    # -------------------------------------------------------------- desenho
    def desenhar(self, tela):
        t = self.tempo
        if t >= ESCURECE[1]:
            self._creditos(tela, t)
            return
        if t < DESLIGA + 0.5:
            self.resultado.desenhar(self.tv_img)
        if t < RESULTADO:
            tela.blit(self.tv_img, (0, 0))
            return
        u = 1.0 - fase(t, SAIDA)
        puxao = 1.0 - fase(t, EJETA)
        branco = 0.9 * suave(fase(t, (4.5, EJETA[0]))) * (1 - suave(fase(t, (EJETA[1] - 0.2, EJETA[1] + 0.4))))
        z0 = 1.0 + 0.06 * suave(fase(t, (EJETA[1], ESCURECE[1])))
        d = t - DESLIGA
        brilho = None if d > 0.2 else max(branco, suave(puxao))
        r = self.quarto.quadro(tela, t, puxao, brilho, z0, u)
        if d < 0:
            self.quarto.tv(tela, r, self.tv_img, branco, u)
        else:
            self._apagar(tela, r, d)
        falhas(tela, t, (EJETA[0] + 0.1, EJETA[0] + 0.6))
        pensamento(tela, FALA_CASA, t - CASA[0], CASA[1] - t)
        pensamento(tela, FALA_CHEGA, t - CHEGA[0], CHEGA[1] - t)
        if t > 0.8:
            tela.blit(self.dica, self.dica.get_rect(topright=(LARGURA - 22, 18)))
        e = t - EJETA[1]                                 # o clarao de quando o Leo cai no quarto
        if 0 <= e < 0.3:
            self._veu(tela, BRANCO, 0.6 * (1 - e / 0.3))
        if t > ESCURECE[0]:
            self._veu(tela, (0, 0, 0), suave(fase(t, ESCURECE)))

    def _veu(self, tela, cor, a):
        if a >= 0.999:
            # opaco, e so pintar a tela: o blit de uma superficie com alfa 255
            # cai num caminho lento do SDL (cerca de 20 ms em 1280x720)
            tela.fill(cor)
            return
        self.veu.fill(cor)
        self.veu.set_alpha(int(255 * a))
        tela.blit(self.veu, (0, 0))

    def _apagar(self, tela, r, d):
        """A TV de tubo desligando: a imagem vira uma linha, a linha vira um ponto, o ponto some."""
        tela.fill((14, 16, 22), r)
        if d < 0.22:
            k = suave(d / 0.22)
            h = max(2, int(r.h * (1 - k)))
            faixa = pygame.transform.scale(pygame.transform.smoothscale(self.tv_img, r.size), (r.w, h))
            claro = pygame.Surface(faixa.get_size()).convert()
            claro.fill(BRANCO)
            claro.set_alpha(int(220 * k))
            faixa.blit(claro, (0, 0))
            tela.blit(faixa, faixa.get_rect(center=r.center))
        elif d < 0.4:
            w = max(4, int(r.w * (1 - suave((d - 0.22) / 0.18))))
            tela.fill(BRANCO, pygame.Rect(0, 0, w, 3).move(r.centerx - w // 2, r.centery - 1))
        elif d < 0.8:
            v = int(255 * (1 - (d - 0.4) / 0.4))
            tela.fill((v, v, v), pygame.Rect(r.centerx - 2, r.centery - 2, 4, 4))
        tela.blit(self.quarto.linhas, r)

    def _creditos(self, tela, t):
        self.fundo.tempo = t
        self.fundo.desenhar(tela)
        for i, (t0, t1) in enumerate(CARTOES):
            a = suave((t - t0) / 0.6) * suave((t1 - t) / 0.6)
            if a > 0:
                for img, y in self.cartoes[i]:
                    if a < 1:
                        img = arte.fantasma(img, max(16, int(255 * a) // 16 * 16))
                    tela.blit(img, img.get_rect(center=(LARGURA // 2, y)))
        entra = 1 - suave((t - ESCURECE[1]) / 0.8)      # sai do escuro
        fim = suave((t - (FIM - 0.6)) / 0.6)
        if max(entra, fim) > 0:
            self._veu(tela, (0, 0, 0), max(entra, fim))

    def _cartao(self, i):
        if i == 0:
            logo = ui.imagem("logo.png", 3)
            return ((logo, 250),
                    (ui.texto("FEITO POR", 20, CINZA, CONTORNO), 452),
                    (ui.texto("MATHEUS CASTRO E HENRIQUE MENDES", 30, BRANCO, CONTORNO), 494))
        if i == 1:
            linhas = (("DESENVOLVIDO COM POWER PPLAY 2.0  -  IC-UFF", 22, BRANCO, 236),
                      ("MÚSICAS", 18, CINZA, 318),
                      ("DOSI & AISAKE  -  CLARX & HARDDOPE  -  SHIP WREK & ZOOKEEPERS", 18, BRANCO, 352),
                      ("MUSIC PROVIDED BY NOCOPYRIGHTSOUNDS - NCS.IO", 16, CINZA, 384),
                      ("TRILHAS ORIGINAIS: CHOCALHO DAS DUNAS, AURORA DE CRISTAL", 18, BRANCO, 432),
                      ("HERÓI: OZZBIT GAMES", 18, BRANCO, 498))
            return tuple((ui.texto(s, tam, cor, CONTORNO), y) for s, tam, cor, y in linhas)
        return ((ui.texto("OBRIGADO POR JOGAR!", 48, AMARELO, CONTORNO), 330),
                (ui.texto("O LÉO ESTÁ EM CASA.", 22, BRANCO, CONTORNO), 400))
