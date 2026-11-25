import math

import pygame
from PPlay.input_manager import InputManager
from PPlay.uikit import Button

from . import efeitos, fases, ui
from .audio import audio
from .camera import Camera
from .cena import TelaQualquer
from .cenario import FundoTodo, ceu
from .config import (LARG_TELA, ALT_TELA, BRANCO, CINZA, AMARELO, VERDE, VERMELHO,
                     AZUL, COR_DA_DIFICULDADE, COR_DA_NOTA, CONTORNO)
from .kit import Botao, Pauzinhos, BarraQueEnche, LinhaDeOpcao, Menu
from .leo import Bonequinho
from .tempo import Agenda, Curvas


def deixa_pronto():
    rascunho = pygame.Surface((LARG_TELA, ALT_TELA)).convert()
    for f in fases.todas():
        FundoTodo(f.cores_da_fase).mostra_na_tela(rascunho, Camera(), 0.0, 0.0)
        efeitos.Ar(f.cores_da_fase).draw(rascunho, Camera(), 0.0)
        ceu(f.cores_da_fase)


class TelaBase(TelaQualquer):
    def __init__(self, joguinho, fase=None, botoes=()):
        super().__init__(joguinho)
        self.fase = fase or fases.carrega_fase(joguinho.fase_escolhida)
        self.cenario = FundoTodo(self.fase.cores_da_fase)
        self.ar = efeitos.Ar(self.fase.cores_da_fase)
        self.menu = None
        if botoes:
            self.menu = Menu(botoes)
        self.tempo = 0.0
        self.despertador, self.animacoes = Agenda.nova(), Curvas.nova()

    def ve_teclas(self):
        if self.menu is None:
            return
        escolha = self.menu.ve_teclas(self.mouse, audio.toca)
        if escolha:
            audio.toca("clique")
            self.escolheu(escolha)

    def escolheu(self, rotulo):
        pass

    def atualiza(self, dt):
        self.tempo += dt
        self.animacoes.vai_ate(self.tempo)
        self.despertador.vai_ate(self.tempo)

    def fundo(self, tela):
        pulso = max(0.0, 1.0 - (self.tempo * 2.0 % 1.0) * 3.0)
        cam = Camera(self.tempo * 40.0)
        self.cenario.mostra_na_tela(tela, cam, self.tempo, pulso)
        self.ar.draw(tela, cam, self.tempo)

    def mostra_na_tela(self, tela):
        self.fundo(tela)
        ui.escurece_tela(tela, 130)
        if self.menu is not None:
            self.menu.mostra_na_tela(tela)

    def titulo(self, tela, s, tam, y, cor):
        ui.escreve(tela, s, tam, LARG_TELA // 2, y, cor, borda_cor=CONTORNO)


class TelaInicial(TelaBase):
    def __init__(self, joguinho):
        x = LARG_TELA // 2 - 200
        super().__init__(joguinho, botoes=[Botao("JOGAR", x, 418, 400, 52, VERDE),
                                           Botao("OPCOES", x, 480, 400, 52, AZUL),
                                           Botao("SAIR", x, 542, 400, 52, VERMELHO)])
        self.mundos_vencidos = Pauzinhos(len(fases.todas()), 16, 16, 44, borda=3, cor=AMARELO, brilho=4)
        self.mundos_vencidos.set_position(LARG_TELA // 2 - (self.mundos_vencidos.valor_max - 1) * 22 - 8, 609)

    def escolheu(self, rotulo):
        if rotulo == "JOGAR":
            self.joguinho.vai_pras_fases()
        elif rotulo == "OPCOES":
            self.joguinho.vai_pras_opcoes()
        else:
            self.joguinho.sai_daqui()

    def mostra_na_tela(self, tela):
        super().mostra_na_tela(tela)
        y = 200 + math.sin(self.tempo * 2.0) * 4
        logo = ui.objeto("logo.png", 3)
        logo.bota_no_meio(LARG_TELA // 2, int(y))
        logo.draw(tela)
        total = len(fases.todas())
        quantas_completas, pontos = self.joguinho.save.progresso([f.nome_da_musica for f in fases.todas()])
        lema = ("UM BOTAO.", "CINCO MUNDOS.", "NO RITMO.")
        quantas = min(len(lema), int(self.tempo * 2.0))
        if quantas:
            self.titulo(tela, "  ".join(lema[:quantas]), 20, 396, self.fase.cores_da_fase.destaque)
        if pontos:
            self.mundos_vencidos.set_value(quantas_completas)
            self.mundos_vencidos.draw(tela)
            cor = ui.COR_APAGADA
            if quantas_completas == total:
                cor = AMARELO
            self.titulo(tela, f"{quantas_completas} DE {total} MUNDOS VENCIDOS  -  {pontos} PTS", 18, 646, cor)
        ui.dicas(tela, (("SETAS", "ESCOLHEM"), ("ENTER", "CONFIRMA"), ("F11", "TELA CHEIA")), ALT_TELA - 36)


class TelaConfig(TelaBase):
    def __init__(self, joguinho):
        super().__init__(joguinho)
        self.indice = 0
        self.opcoes = joguinho.save.opcoes
        cor = self.fase.cores_da_fase.destaque
        self.linhas = [LinhaDeOpcao("VOLUME DA MUSICA", 300, "musica", 10, cor),
                       LinhaDeOpcao("VOLTAR", 390, None, 0, cor)]

    def muda(self, d):
        linha = self.linhas[self.indice]
        if linha.chave is None:
            return
        novo = linha.ta_mudado(self.opcoes[linha.chave], d)
        if novo != self.opcoes[linha.chave]:
            self.opcoes[linha.chave] = novo
            audio.aplica(self.opcoes)
            audio.toca("navegar")

    def vai_embora(self):
        self.joguinho.save.salva()
        audio.toca("clique")
        self.joguinho.vai_pro_menu()

    def ve_teclas(self):
        for linha in self.linhas:
            linha.update()
        ta_no_voltar = self.linhas[self.indice].chave is None
        if InputManager.action_pressed("baixo"):
            self.indice = (self.indice + 1) % len(self.linhas)
            audio.toca("navegar")
        elif InputManager.action_pressed("cima"):
            self.indice = (self.indice - 1) % len(self.linhas)
            audio.toca("navegar")
        elif InputManager.action_pressed("esquerda"):
            self.muda(-1)
        elif InputManager.action_pressed("direita"):
            self.muda(1)
        elif InputManager.action_pressed("voltar"):
            self.vai_embora()
            return
        elif ta_no_voltar and InputManager.action_pressed("confirmar"):
            self.vai_embora()
            return
        for i, linha in enumerate(self.linhas):
            if linha.pressed or (linha.hovered and self.mouse.mouse_mexeu()):
                self.indice = i
            if linha.pressed and linha.chave is None:
                self.vai_embora()
            elif linha.pressed:
                if self.mouse.get_position()[0] > LARG_TELA // 2 + 100:
                    self.muda(1)
                else:
                    self.muda(-1)

    def mostra_na_tela(self, tela):
        super().mostra_na_tela(tela)
        self.titulo(tela, "OPCOES", 56, 160, self.fase.cores_da_fase.destaque)
        for i, linha in enumerate(self.linhas):
            linha.draw(tela, i == self.indice, self.opcoes.get(linha.chave, 0), self.tempo)
        ui.dicas(tela, (("SETAS", "ESCOLHEM E MUDAM"), ("ESC", "VOLTA")), ALT_TELA - 36)


class TelaEscolheFase(TelaBase):
    ALT, VAO = 420, 18
    TEMPO_DE_TROCA = 0.35

    def __init__(self, joguinho):
        super().__init__(joguinho)
        self.lista = fases.todas()
        leo = Bonequinho()
        self.indice = joguinho.fase_escolhida
        self.cartas = []
        for i, f in enumerate(self.lista):
            self.cartas.append(CartaDoMundo(f, self.retangulo_da_carta(i), leo, joguinho.save))
        self.acende_botao()
        self.cartas[self.indice].foco = 1.0
        self.fotos = [pygame.Surface((LARG_TELA, ALT_TELA)).convert() for _ in range(2)]
        self.foto_saindo = None
        self.troca = 1.0
        self.embaixo_do_mouse = self.carta_no_mouse()

    def retangulo_da_carta(self, i):
        n = len(self.lista)
        larg = (LARG_TELA - 64 - (n - 1) * self.VAO) // n
        x0 = (LARG_TELA - n * larg - (n - 1) * self.VAO) // 2
        return pygame.Rect(x0 + i * (larg + self.VAO), 190, larg, self.ALT)

    def carta_no_mouse(self):
        for carta in self.cartas:
            carta.update()
        for i, carta in enumerate(self.cartas):
            if carta.hovered:
                return i
        return None

    def acende_botao(self):
        for i, carta in enumerate(self.cartas):
            carta.ta_no_foco(i == self.indice)

    def seleciona(self, i):
        self.indice = self.joguinho.fase_escolhida = i
        self.acende_botao()
        foto = self.fotos[0]
        if self.foto_saindo is foto:
            foto = self.fotos[1]
        self.fundo(foto)
        self.desmancha(foto)
        self.foto_saindo, self.troca = foto, 0.0
        self.animacoes.limpar()
        self.animacoes.to(self, "troca", 1.0, self.TEMPO_DE_TROCA, inicio=self.tempo)
        self.cenario = FundoTodo(self.lista[i].cores_da_fase)
        self.ar = efeitos.Ar(self.lista[i].cores_da_fase)
        audio.toca("navegar")

    def desmancha(self, tela):
        if self.foto_saindo is None:
            return
        if self.troca >= 1.0:
            self.foto_saindo = None
            return
        self.foto_saindo.set_alpha(int(255 * (1.0 - ui.suaviza(self.troca))))
        tela.blit(self.foto_saindo, (0, 0))

    def ve_teclas(self):
        joguinho = self.joguinho
        if InputManager.action_pressed("direita"):
            self.seleciona((self.indice + 1) % len(self.lista))
        elif InputManager.action_pressed("esquerda"):
            self.seleciona((self.indice - 1) % len(self.lista))
        if InputManager.action_pressed("confirmar"):
            audio.toca("clique")
            joguinho.vai_pro_jogo(self.indice)
            return
        if InputManager.action_pressed("voltar"):
            audio.toca("clique")
            joguinho.vai_pro_menu()
            return
        if self.mouse.mouse_mexeu():
            i = self.carta_no_mouse()
            if i != self.embaixo_do_mouse:
                self.embaixo_do_mouse = i
                if i is not None and i != self.indice:
                    self.seleciona(i)
        for i, carta in enumerate(self.cartas):
            if carta.is_clicked() and i == self.indice:
                audio.toca("clique")
                joguinho.vai_pro_jogo(i)
                return
            if carta.is_clicked():
                self.seleciona(i)
                return

    def mostra_na_tela(self, tela):
        self.fundo(tela)
        self.desmancha(tela)
        ui.escurece_tela(tela, 130)
        self.titulo(tela, "ESCOLHA A FASE", 48, 100, BRANCO)
        ui.dicas(tela, (("SETAS", "ESCOLHEM"), ("ENTER", "JOGA"), ("ESC", "VOLTA")), ALT_TELA - 36)
        for carta in self.cartas:
            carta.draw(tela, self.tempo)


class CartaDoMundo(Button):
    def __init__(self, fase, lugar, leo, save):
        super().__init__(lugar.w, lugar.h, fase.nome, cor_base=COR_DA_DIFICULDADE[fase.dificil_quanto],
                         cor_hover=fase.cores_da_fase.destaque)
        self.cor_texto = BRANCO
        self.fase, self.lugar, self.leo, self.save = fase, lugar, leo, save
        self.foco = 0.0
        self.ta_no_foco(False)
        niveis = list(COR_DA_DIFICULDADE)
        self.n_degraus = Pauzinhos(len(niveis), 10, 12, 14, cor=self.cor_base)
        self.n_degraus.set_value(niveis.index(fase.dificil_quanto) + 1)
        self.melhor = BarraQueEnche(0, 6, self.cor_hover)

    def ta_no_foco(self, sim):
        self.ta_escolhida = sim
        r = self.lugar.inflate(20, 20).move(0, -14) if sim else self.lugar
        self.set_position(r.x, r.y)
        self.width, self.height = r.size

    def draw(self, tela, tempo):
        alvo = 1.0 if self.ta_escolhida else 0.0
        self.foco += (alvo - self.foco) * 0.25
        foco = self.foco
        r = self.lugar.inflate(int(20 * foco), int(20 * foco)).move(0, -int(14 * foco))
        if foco > 0.05:
            self.brilho_em_volta(tela, r, tempo)
        alfa = 200
        if self.ta_escolhida:
            alfa = 255
        ui.desenha_moldura(tela, self.fase.nome_da_musica, r.x, r.y, r.w, r.h, alfa)
        self.amostrinha(tela, pygame.Rect(r.x + 20, r.y + 20, r.w - 40, 120), tempo)
        ui.escreve_cabendo(tela, self.texto, 22, r.centerx, r.y + 172, r.w - 36, self.cor_texto)
        self.mostra_dados(tela, r)
        if not self.ta_escolhida:
            veu = pygame.Surface(r.size, pygame.SRCALPHA)
            veu.fill((8, 6, 20, int(96 * (1.0 - foco))))
            tela.blit(veu, r.topleft)

    def brilho_em_volta(self, tela, r, tempo):
        brilho = pygame.Surface((r.w + 36, r.h + 36), pygame.SRCALPHA)
        forca = (0.75 + 0.25 * math.sin(tempo * 4.0)) * self.foco
        for i, alfa in enumerate((26, 44, 70)):
            pygame.draw.rect(brilho, (*self.cor_hover, int(alfa * forca)),
                             (i * 6, i * 6, r.w + 36 - i * 12, r.h + 36 - i * 12), border_radius=10)
        tela.blit(brilho, (r.x - 18, r.y - 18))

    def amostrinha(self, tela, amostra, tempo):
        cores_da_fase = self.fase.cores_da_fase
        tela.blit(pygame.transform.scale(ceu(cores_da_fase), amostra.size), amostra.topleft)
        pygame.draw.rect(tela, cores_da_fase.chao, (amostra.x, amostra.bottom - 30, amostra.w, 30))
        pygame.draw.rect(tela, cores_da_fase.chao_topo, (amostra.x, amostra.bottom - 30, amostra.w, 5))
        emblema = ui.objeto(f"emblema_{self.fase.nome_da_musica}.png")
        emblema.bota_no_meio(amostra.centerx + amostra.w * 3 // 16, amostra.centery)
        emblema.draw(tela)
        self.leo.pose("parado", tempo * 8)
        self.leo.set_position(amostra.x + amostra.w * 7 // 32, amostra.bottom - 30)
        self.leo.draw(tela)
        pygame.draw.rect(tela, self.cor_base, amostra, 2)

    def mostra_dados(self, tela, r):
        f, cor, cx = self.fase, self.cor_base, r.centerx
        ui.escreve(tela, f.dificil_quanto, 16, cx, r.y + 198, cor)
        rotulo = ui.texto(f"{f.bpm_da_musica:.0f} BPM", 16, cor)
        marcos = self.n_degraus.valor_max * self.n_degraus.passo + 8
        x0 = cx - (rotulo.get_width() + marcos) // 2
        self.n_degraus.set_position(x0, r.y + 214)
        tela.blit(rotulo, (x0 + marcos, r.y + 220 - rotulo.get_height() // 2))
        self.n_degraus.draw(tela)

        y = r.y + 266
        util = r.w - 44
        rec = self.save.recorde(f.nome_da_musica)
        if rec["nota"] == "-":
            ui.desenha_moldura(tela, "padrao", cx - 32, y - 32, 64, 64)
            ui.escreve(tela, "?", 36, cx, y, COR_DA_NOTA["-"])
        else:
            medalha = ui.objeto(f"nota_{rec['nota'].lower()}.png")
            medalha.bota_no_meio(cx, y)
            medalha.draw(tela)
        placar = f"{rec['melhor']:.0f}%  -  {rec['pontos']} PTS"
        ecos = f"ECOS {rec['ecos']}/{len(f.bolinhas)}"
        ui.escreve_cabendo(tela, placar, 16, cx, y + 42, util, ui.COR_APAGADA)
        ui.escreve_cabendo(tela, ecos, 16, cx, y + 59, util, ui.COR_APAGADA)
        y += 74
        self.melhor.width = r.w - 90
        self.melhor.set_position(cx - self.melhor.width // 2, y - 3)
        self.melhor.set_value(rec["melhor"])
        self.melhor.draw(tela)
        ui.escreve_cabendo(tela, f.info_da_musica.titulo, 18, cx, y + 22, util, AMARELO)
        ui.escreve_cabendo(tela, f.info_da_musica.quem_canta, 16, cx, y + 44, util, ui.COR_APAGADA)


class TelaGanhou(TelaBase):
    CONTA, CARIMBO, QUEDA = 0.8, 0.95, 0.22

    def __init__(self, joguinho, dados):
        x = LARG_TELA // 2 - 200
        super().__init__(joguinho, dados["fase"], [
            Botao("JOGAR DE NOVO", x, 520, 400, 48, AZUL),
            Botao("PROXIMA FASE", x, 578, 400, 48, VERDE),
            Botao("MENU DE FASES", x, 636, 400, 48, AMARELO)])
        self.dados = dados
        self.menu.indice = 1
        self.faiscas = efeitos.UmMonteDeFaisca()
        self.conta = self.queda = 0.0
        self.animacoes.to(self, "conta", 1.0, self.CONTA)
        self.animacoes.to(self, "queda", 1.0, self.QUEDA, inicio=self.CARIMBO)
        self.despertador.after(self.CARIMBO + self.QUEDA, self.carimba)

    def atualiza(self, dt):
        self.faiscas.update(dt)
        super().atualiza(dt)

    def carimba(self):
        x, y = (LARG_TELA - 900) // 2 + 190, 136 + 140
        nota = self.dados["nota"]
        self.faiscas.solta_aqui(x, y, COR_DA_NOTA[nota], 18)
        self.faiscas.solta_aqui(x, y, BRANCO, 10)
        audio.toca("perfeito" if nota in ("S", "A") else "bom")

    def escolheu(self, rotulo):
        joguinho, f = self.joguinho, self.fase
        if rotulo == "JOGAR DE NOVO":
            joguinho.vai_pro_jogo(f.qual_fase)
        elif rotulo == "PROXIMA FASE":
            joguinho.vai_pro_jogo((f.qual_fase + 1) % len(fases.todas()))
        else:
            joguinho.vai_pras_fases()

    def mostra_na_tela(self, tela):
        super().mostra_na_tela(tela)
        d = self.dados
        self.titulo(tela, "FASE COMPLETA", 52, 56, VERDE)
        self.titulo(tela, self.fase.nome, 22, 102, CINZA)

        x, y, w, h = (LARG_TELA - 900) // 2, 136, 900, 360
        ui.desenha_moldura(tela, self.fase.nome_da_musica, x, y, w, h)
        nota = d["nota"]
        medalha = ui.objeto(f"nota_{nota.lower()}.png", 2)
        k = self.queda
        if k < 1.0:
            medalha.set_scale(1.0 + 1.4 * (1.0 - k) ** 2)
            medalha.set_transparency(max(16, int(255 * min(1.0, k * 2)) // 16 * 16))
        else:
            medalha.set_scale(1.0)
            medalha.set_transparency(255)
        medalha.bota_no_meio(x + 190, y + 140)
        if k > 0.0:
            medalha.draw(tela)
        ui.escreve(tela, f"{d['precisao'] * 100:.1f}%", 36, x + 190, y + 262, BRANCO)
        ui.escreve(tela, "DE PRECISAO", 16, x + 190, y + 300, CINZA)
        mostra = int(d["pontos"] * self.conta)
        ui.escreve(tela, "PONTUACAO", 18, x + 620, y + 50, CINZA)
        ui.escreve(tela, str(mostra), 64, x + 620, y + 100, BRANCO)
        if d["recorde"]:
            ui.escreve(tela, "NOVO RECORDE!", 20, x + 620, y + 150, AMARELO)
        linhas = (("PERFEITO", d["perfeitos"], VERDE), ("BOM", d["bons"], AMARELO),
                  ("ERROU", d["erros"], VERMELHO), ("MAIOR SEQUENCIA", d["combo"], BRANCO),
                  ("ECOS", f"{d['ecos']}/{d['ecos_total']}", self.fase.cores_da_fase.destaque))
        for i, (rotulo, valor, c) in enumerate(linhas):
            k = ui.suaviza((self.tempo - 0.15 - i * 0.12) / 0.2)
            if k <= 0.0:
                continue
            yy = y + 192 + i * 29 + int(8 * (1.0 - k))
            ui.escreve(tela, rotulo, 18, x + 440, yy, CINZA, "esquerda")
            ui.escreve(tela, str(valor), 22, x + 820, yy, c, "direita")
        ui.escreve_cabendo(tela, self.fase.info_da_musica.creditos, 16, LARG_TELA // 2,
                           y + h - 22, w - 40, CINZA)
        self.faiscas.draw(tela)


class TelaPerdeu(TelaBase):
    def __init__(self, joguinho, dados):
        x = LARG_TELA // 2 - 200
        super().__init__(joguinho, dados["fase"], [
            Botao("TENTAR DE NOVO", x, 430, 400, 56, AZUL),
            Botao("MENU DE FASES", x, 500, 400, 56, AMARELO),
            Botao("MENU PRINCIPAL", x, 570, 400, 56, VERMELHO)])
        self.dados = dados

    def escolheu(self, rotulo):
        joguinho = self.joguinho
        if rotulo == "TENTAR DE NOVO":
            joguinho.vai_pro_jogo(self.fase.qual_fase)
        elif rotulo == "MENU DE FASES":
            joguinho.vai_pras_fases()
        else:
            joguinho.vai_pro_menu()

    def mostra_na_tela(self, tela):
        super().mostra_na_tela(tela)
        d = self.dados
        tremidao = math.sin(self.tempo * 30) * max(0.0, 1.0 - self.tempo * 2) * 8
        ui.escreve(tela, "FIM DE JOGO", 80, LARG_TELA // 2 + tremidao, 170, VERMELHO,
                   borda_cor=CONTORNO)
        x, y, w = (LARG_TELA - 800) // 2, 260, 800
        ui.desenha_moldura(tela, self.fase.nome_da_musica, x, y, w, 120)
        campos = (("FASE", self.fase.nome), ("PROGRESSO", f"{d['progresso']:.0f}%"),
                  ("PONTUACAO", str(d["pontos"])),
                  ("ECOS", f"{d['ecos']}/{d['ecos_total']}"))
        for i, (rotulo, valor) in enumerate(campos):
            cx = x + w * (0.19 + i * 0.22)
            util = 250
            if i > 0:
                cx += 30
                util = 160
            ui.escreve(tela, rotulo, 16, cx, y + 40, CINZA)
            ui.escreve_cabendo(tela, valor, 22, cx, y + 80, util, BRANCO)
