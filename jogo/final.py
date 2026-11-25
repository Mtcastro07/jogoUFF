import pygame

from . import fases, menus, ui
from .abertura import QuartoDoLeo, dica_de_tecla, falhas, fase, balao_de_pensamento, acabou_de_pular, suaviza
from .audio import audio
from .cena import TelaQualquer
from .config import LARG_TELA, ALT_TELA, BRANCO, CINZA, AMARELO, CONTORNO
from .imagem import Desenho
from .impacto import Impacto
from .tempo import Agenda

RESULTADO = 3.4
SAIDA = (3.4, 4.9)
EJETA = (5.0, 6.2)
MUSICA = 6.6
CASA = (7.0, 9.6)
DESLIGA = 10.0
CHEGA = (11.0, 13.6)
ESCURECE = (13.6, 14.6)
CARTOES = ((15.0, 19.8), (20.2, 25.6), (26.0, 29.8))
FIM = 30.4
FALA_CASA = "...CASA."
FALA_CHEGA = "CHEGA DE JOGO POR HOJE."


def tem_final(save, fase_que_ganhou):
    todas = fases.todas()
    quantas_completas, _ = save.progresso([f.nome_da_musica for f in todas])
    if quantas_completas < len(todas):
        return False
    if not save.final_visto:
        return True
    return fase_que_ganhou.qual_fase == len(todas) - 1


class Finalzinho(TelaQualquer):
    def __init__(self, joguinho, dados):
        super().__init__(joguinho)
        self.tempo = 0.0
        self.ta_saindo = False
        self.despertador = Agenda.nova()
        self.despertador.after(EJETA[0], self.toca_som, "orbe")
        self.despertador.after(EJETA[1], self.toca_som, "eco")
        self.impacto = Impacto.novo()
        self.despertador.after(EJETA[1], self.impacto.flash, BRANCO, 0.3, EJETA[1])
        self.despertador.after(DESLIGA, self.toca_som, "clique")
        self.despertador.after(MUSICA, self.desenha_musica)
        self.despertador.after(FIM, self.vai_embora)
        self.resultado_final = menus.TelaGanhou(joguinho, dados)
        self.fase = self.resultado_final.fase
        self.imagem_da_tv = pygame.Surface((LARG_TELA, ALT_TELA)).convert()
        self.resultado_final.mostra_na_tela(self.imagem_da_tv)
        self.quarto = QuartoDoLeo("quarto_manha.png", "south.png", self.imagem_da_tv)
        self.fundo = menus.TelaBase(joguinho, fases.carrega_fase(0))
        self.lista_de_cartoes = []
        for i in range(len(CARTOES)):
            linhas = []
            for img, y in self.faz_cartao(i):
                linha = Desenho(img)
                linha.bota_no_meio(LARG_TELA // 2, y)
                linhas.append(linha)
            self.lista_de_cartoes.append(linhas)
        self.fundo.mostra_na_tela(pygame.Surface((LARG_TELA, ALT_TELA)).convert())
        self.veu = pygame.Surface((LARG_TELA, ALT_TELA)).convert()
        self.dica = dica_de_tecla()
        joguinho.save.final_visto = True
        joguinho.save.salva()

    def ve_teclas(self):
        if acabou_de_pular(self) and self.tempo > 0.8:
            self.vai_embora()

    def vai_embora(self):
        if self.ta_saindo:
            return
        self.ta_saindo = True
        audio.para_musica()
        self.joguinho.vai_pro_menu()

    def toca_som(self, nome):
        audio.toca(nome)

    def desenha_musica(self):
        audio.toca_musica("bosque")

    def atualiza(self, dt):
        if self.ta_saindo:
            return
        self.tempo += min(dt, 1.0 / 30.0)
        t = self.tempo
        if t < DESLIGA + 0.5:
            self.resultado_final.atualiza(dt)
        if audio.ta_tocando() and t > FIM - 1.8:
            audio.volume(max(0.0, (FIM - t) / 1.8))
        self.despertador.vai_ate(t)

    def mostra_na_tela(self, tela):
        t = self.tempo
        if t >= ESCURECE[1]:
            self.mostra_creditos(tela, t)
            return
        if t < DESLIGA + 0.5:
            self.resultado_final.mostra_na_tela(self.imagem_da_tv)
        if t < RESULTADO:
            tela.blit(self.imagem_da_tv, (0, 0))
            return
        u = 1.0 - fase(t, SAIDA)
        puxao = 1.0 - fase(t, EJETA)
        branco = 0.9 * suaviza(fase(t, (4.5, EJETA[0]))) * (1 - suaviza(fase(t, (EJETA[1] - 0.2, EJETA[1] + 0.4))))
        z0 = 1.0 + 0.06 * suaviza(fase(t, (EJETA[1], ESCURECE[1])))
        d = t - DESLIGA
        brilho = None
        if d <= 0.2:
            brilho = max(branco, suaviza(puxao))
        r = self.quarto.pega_quadro(tela, t, puxao, brilho, z0, u)
        if d < 0:
            self.quarto.tv(tela, r, self.imagem_da_tv, branco, u)
        else:
            self.vai_apagando(tela, r, d)
        falhas(tela, t, (EJETA[0] + 0.1, EJETA[0] + 0.6))
        balao_de_pensamento(tela, FALA_CASA, t - CASA[0], CASA[1] - t)
        balao_de_pensamento(tela, FALA_CHEGA, t - CHEGA[0], CHEGA[1] - t)
        if t > 0.8:
            self.dica.draw(tela)
        self.impacto.draw_flash(tela, self.veu, t, 0.6 * 255)
        if t > ESCURECE[0]:
            self.veuzinho(tela, (0, 0, 0), suaviza(fase(t, ESCURECE)))

    def veuzinho(self, tela, cor, a):
        if a >= 0.999:
            tela.fill(cor)
            return
        self.veu.fill(cor)
        self.veu.set_alpha(int(255 * a))
        tela.blit(self.veu, (0, 0))

    def vai_apagando(self, tela, r, d):
        tela.fill((14, 16, 22), r)
        if d < 0.22:
            k = suaviza(d / 0.22)
            h = max(2, int(r.h * (1 - k)))
            faixa = pygame.transform.scale(pygame.transform.smoothscale(self.imagem_da_tv, r.size), (r.w, h))
            claro = pygame.Surface(faixa.get_size()).convert()
            claro.fill(BRANCO)
            claro.set_alpha(int(220 * k))
            faixa.blit(claro, (0, 0))
            tela.blit(faixa, faixa.get_rect(center=r.center))
        elif d < 0.4:
            w = max(4, int(r.w * (1 - suaviza((d - 0.22) / 0.18))))
            tela.fill(BRANCO, pygame.Rect(0, 0, w, 3).move(r.centerx - w // 2, r.centery - 1))
        elif d < 0.8:
            v = int(255 * (1 - (d - 0.4) / 0.4))
            tela.fill((v, v, v), pygame.Rect(r.centerx - 2, r.centery - 2, 4, 4))
        tela.blit(self.quarto.linhas, r)

    def mostra_creditos(self, tela, t):
        self.fundo.tempo = t
        self.fundo.mostra_na_tela(tela)
        for i, (t0, t1) in enumerate(CARTOES):
            a = suaviza((t - t0) / 0.6) * suaviza((t1 - t) / 0.6)
            if a > 0:
                alfa = 255
                if a < 1:
                    alfa = max(16, int(255 * a) // 16 * 16)
                for linha in self.lista_de_cartoes[i]:
                    linha.set_transparency(alfa)
                    linha.draw(tela)
        entra = 1 - suaviza((t - ESCURECE[1]) / 0.8)
        fim = suaviza((t - (FIM - 0.6)) / 0.6)
        if max(entra, fim) > 0:
            self.veuzinho(tela, (0, 0, 0), max(entra, fim))

    def faz_cartao(self, i):
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
            return [(ui.texto(s, tam, cor, CONTORNO), y) for s, tam, cor, y in linhas]
        return ((ui.texto("OBRIGADO POR JOGAR!", 48, AMARELO, CONTORNO), 330),
                (ui.texto("O LÉO ESTÁ EM CASA.", 22, BRANCO, CONTORNO), 400))
