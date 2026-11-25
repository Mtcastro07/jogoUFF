import bisect
import math

from .audio import AS_MUSICAS
from .grupo import PorColuna, Monte
from .mapa import BlocoDuro, PedacoDeChao, MapaDaFase, Pontezinha, QUAO_FUNDO
from .objetos import (Arvorezona, Bolinha, Enfeite, Bichos, SetinhaGuia, Mola, Orbe,
                      CoisaQueMachuca, CoisaPendurada, PortalDeVelocidade,
                      PortalDoFim)
from .simulacao import ALTURA_DA_MOLA
from .config import (QUADRADO, LINHA_DO_CHAO, CORES_DAS_FASES, PULINHO, CORTA_O_PULO, TEMPO_BOM,
                     TAM_DO_LEO)

COMO_PULA = {"bosque": (1, 6, 3.5), "dunas": (1, 6, 3.5), "ilhas": (1, 6, 3.5),
             "geleira": (1, 6, 3.5), "eclipse": (1, 7, 3.5)}
FASE_SEM_SEGURAR = {"bosque"}
FASE_COM_SETINHA = {"bosque"}

ALTURA_PRA_CORTAR = (PULINHO - CORTA_O_PULO ** 2) / (1.0 - CORTA_O_PULO ** 2)

ENXAME = (30, 74, 198)
PINGENTE = (72, 180, 300)
TEMPO_SEM_NADA = 10
NOME_DO_BANDO = {"dunas": "ENXAME", "ilhas": "REVOADA", "geleira": "MORCEGOS", "eclipse": "MORCEGOS"}
NOME_DA_PENDURADA = {"ilhas": "CRISTAIS", "geleira": "PINGENTE", "eclipse": "ESPETOS"}


class Fasezinha:
    def __init__(self, qual_fase, nome, dificil_quanto, nome_da_musica):
        self.qual_fase = qual_fase
        self.semente = qual_fase
        self.nome = nome
        self.dificil_quanto = dificil_quanto
        self.nome_da_musica = nome_da_musica
        self.cores_da_fase = CORES_DAS_FASES[nome_da_musica]
        self.info_da_musica = AS_MUSICAS[nome_da_musica]

        self.bpm_da_musica = self.info_da_musica.bpm_do_jogo
        self.tempo_da_batida = 60.0 / self.bpm_da_musica
        self.batidas_do_pulo, self.quadrados_por_batida, altura = COMO_PULA[nome_da_musica]
        self.altura_do_pulo = altura * QUADRADO
        self.vx = self.quadrados_por_batida * QUADRADO / self.tempo_da_batida
        self.tempo_do_pulo = self.batidas_do_pulo * self.tempo_da_batida
        self.gravidade = 8.0 * self.altura_do_pulo / self.tempo_do_pulo ** 2
        self.forca_do_pulo = 4.0 * self.altura_do_pulo / self.tempo_do_pulo
        self.altura_pra_cortar = ALTURA_PRA_CORTAR * self.altura_do_pulo
        self.sem_segurar = nome_da_musica in FASE_SEM_SEGURAR
        self.setinhas = nome_da_musica in FASE_COM_SETINHA
        self.x_das_velocidades, self.velocidades = [-1e9], [self.vx]
        self.portais = Monte()

        self.y_do_chao = LINHA_DO_CHAO * QUADRADO
        self.y_do_abismo = (LINHA_DO_CHAO + QUAO_FUNDO) * QUADRADO

        self.chao = self.pontezinhas = self.torres = None
        self.solidos = {}
        self.chao_por_coluna = {}
        self.blocos = []
        self.coisas_que_machucam = Monte()
        self.perigos_por_coluna = PorColuna()
        self.toques_certos = Monte()
        self.saltos = []
        self.bolinhas = Monte()
        self.molas = Monte()
        self.orbes = Monte()
        self.bolinhas_extras = []
        self.pontes = set()
        self.duplas = []
        self.voadores = Monte()
        self.bandos, self.penduradas = Monte(), Monte()
        self.obstaculos_de_ritmo = []
        self.lugares_livres = []
        self.lugares_altos = []
        self.voadores_por_coluna = PorColuna()
        self.curtos = set()
        self.dicas = []
        self.enfeites = Monte()
        self.batidas_de_pular = []
        self.partes_da_musica = []
        self.x_das_partes = []
        self.x_do_fim = 0.0
        self.duracao = 0.0

    def ato(self, x):
        return max(0, bisect.bisect_right(self.x_das_partes, x) - 1)

    def velocidade_em(self, x):
        return self.velocidades[bisect.bisect_right(self.x_das_velocidades, x) - 1]

    def altura_do_chao(self, tx):
        for c in range(tx, tx + 40):
            if c in self.chao_por_coluna:
                return self.chao_por_coluna[c]
        return LINHA_DO_CHAO


class MontaFase:
    def __init__(self, fase):
        self.f = fase
        self.b = 0.0
        self.nivel = LINHA_DO_CHAO
        self.s = fase.quadrados_por_batida
        self.x_de_inicio, self.batida_de_inicio = 0.0, 0.0
        self.acabou_de_descer = False
        self.dicas_ditas = set()
        self.bota_bolinha = True
        self.bota_piso(-10, 0)

    def L(self):
        return round(self.f.batidas_do_pulo * self.s)

    def janela(self):
        return TEMPO_BOM * self.s

    def meio(self):
        return max(2, int(round(self.L() / 2)))

    def beirada(self):
        return max(2, math.ceil(self.janela() + 0.6))

    def pouso(self):
        return max(self.beirada() + 2, int(self.L() - self.janela() + 0.3))

    def degrauzinho(self):
        return self.L() // 2 + 1

    def margem_de_subida(self):
        return max(self.beirada() + 2, self.degrauzinho())

    def _x(self, batida_n):
        return self.x_de_inicio + (batida_n - self.batida_de_inicio) * self.s

    def coluna_da_batida(self, batida_n):
        return int(round(self._x(batida_n)))

    def velocidade(self, quadrados_na_batida):
        x = self._x(self.b)
        ta_rapido = quadrados_na_batida > self.s
        self.x_de_inicio, self.batida_de_inicio, self.s = x, self.b, quadrados_na_batida
        self.f.x_das_velocidades.append(x * QUADRADO)
        self.f.velocidades.append(quadrados_na_batida * QUADRADO / self.f.tempo_da_batida)
        self.f.portais.add(PortalDeVelocidade(x * QUADRADO, self.nivel * QUADRADO, ta_rapido))

    def bota_piso(self, c0, c1):
        self.abre_buraco(c0, c1)
        for tx in range(c0, c1):
            self.f.chao_por_coluna[tx] = self.nivel

    def abre_buraco(self, c0, c1):
        for tx in range(c0, c1):
            self.f.chao_por_coluna.pop(tx, None)

    def bloco(self, tx, ty):
        self.f.blocos.append((tx, ty))

    def caco(self, tx, ty=None, quantidade=1, mata_na_hora=False):
        if ty is None:
            ty = self.nivel
        self.f.coisas_que_machucam.add(CoisaQueMachuca(tx * QUADRADO, (ty - 1) * QUADRADO, QUADRADO, QUADRADO,
                                                       quantidade, mata_na_hora))

    def marca_toque(self, batida_n, eco=True, y=None):
        self.f.batidas_de_pular.append(round(batida_n, 3))
        if y is None:
            y = self.nivel * QUADRADO
        self.f.toques_certos.add(SetinhaGuia(self.coluna_da_batida(batida_n) * QUADRADO, y))
        if eco and self.bota_bolinha:
            self.f.saltos.append((batida_n, self._x(batida_n) * QUADRADO, self.nivel * QUADRADO))

    def bota_dica(self, chave, x, y, texto):
        if chave not in self.dicas_ditas:
            self.dicas_ditas.add(chave)
            self.f.dicas.append((x, y, texto))

    def lugar_da_dica_da_mola(self, x, chao):
        for v in self.f.voadores:
            if x - 3 * QUADRADO < v.x + v.width < x:
                x = v.x + v.width + 3 * QUADRADO
        if self.f.setinhas:
            return x, chao - 2.9 * QUADRADO
        return x, chao - 2.2 * QUADRADO

    def bota_mola(self, qtd_batidas, opcao, atraso=0):
        f, L, n = self.f, self.L(), self.nivel
        j, fim = self.coluna_da_batida(self.b), self.coluna_da_batida(self.b + qtd_batidas)
        x = self._x(self.b) * QUADRADO
        chao = n * QUADRADO
        self.bota_dica("mola", *self.lugar_da_dica_da_mola(x, chao), "MOLA: TOQUE NA BATIDA")
        if opcao == "orbe":
            self.bota_dica("orbe", x + L * QUADRADO, chao - (ALTURA_DA_MOLA + 1.6) * QUADRADO, "ORBE: TOQUE NO AR")
        self.marca_toque(self.b, eco=False)
        f.molas.add(Mola(x - (self.janela() + 0.15) * QUADRADO,
                         x + (self.janela() + 0.25 + atraso) * QUADRADO, chao))
        ecos = [0.5, 1.0, 1.5]
        if opcao is None:
            self.bota_piso(j, fim)
            for k in range(3):
                self.bloco(j + L, n - 1 - k)
            self.caco(j + L, n - 3)
            ecos = [0.5, 1.5]
        elif opcao == "vao":
            self.bota_piso(j, j + 2 + atraso)
            self.bota_buraco(j + 2 + atraso, j + 2 * L - 2, n + 3)
            self.bota_piso(j + 2 * L - 2, fim)
        elif opcao == "orbe":
            face = j + L + L // 2
            self.bota_piso(j, face)
            self.nivel -= 6
            self.bota_piso(face, fim)
            alcance = (self.janela() + 0.25) * QUADRADO
            f.orbes.add(Orbe(x + L * QUADRADO + TAM_DO_LEO * 0.5,
                             chao - ALTURA_DA_MOLA * QUADRADO - TAM_DO_LEO * 0.5,
                             alcance, 1.35 * QUADRADO))
            self.marca_toque(self.b + f.batidas_do_pulo, eco=False, y=chao - (ALTURA_DA_MOLA - 1.5) * QUADRADO)
            ecos = [0.5]
            f.bolinhas_extras.append(Bolinha(x + 1.5 * L * QUADRADO, chao - (ALTURA_DA_MOLA + 3.5) * QUADRADO, True))
        else:
            face = j + L + 2
            self.bota_piso(j, face)
            self.nivel += opcao
            self.bota_piso(face, fim)
            ecos = [0.5, 1.0]
        for k in ecos:
            alto = ALTURA_DA_MOLA * (1.0 - (k - 1.0) ** 2)
            f.bolinhas_extras.append(Bolinha(x + k * L * QUADRADO, chao - alto * QUADRADO, True))
        self.b += qtd_batidas

    def comeca_parte(self, nome):
        self.f.partes_da_musica.append((nome, self.b))
        self.f.x_das_partes.append(self.coluna_da_batida(self.b) * QUADRADO)

    def bota(self, *passos):
        for passo in passos:
            tipo, qtd_batidas = passo[0], passo[1]
            opcao = None
            if len(passo) > 2:
                opcao = passo[2]
            if tipo == "mola":
                self.bota_mola(qtd_batidas, opcao, 1 if self.acabou_de_descer else 0)
                self.acabou_de_descer = False
                continue
            if tipo == "pingente":
                self.bota_pendurada(qtd_batidas, opcao or 1)
                self.b += qtd_batidas
                self.acabou_de_descer = False
                continue
            pula = tipo not in ("pausa", "desce", "enxame")
            j, fim = self.coluna_da_batida(self.b), self.coluna_da_batida(self.b + qtd_batidas)
            q1 = self.beirada()
            if self.acabou_de_descer:
                q1 += 1
            elif self.bota_bolinha:
                self.anota_onde_cabe(tipo, qtd_batidas, opcao)
            self.acabou_de_descer = (tipo == "ilha" and (opcao or 0) > 0 and
                                     qtd_batidas <= self.f.batidas_do_pulo + 1e-9)
            if pula:
                self.marca_toque(self.b)
            if tipo == "desce":
                self.nivel += opcao or 1
            if tipo in ("caco", "torre", "vao", "pausa", "desce", "enxame"):
                self.bota_piso(j, fim)
            if tipo == "enxame":
                self.bota_bando(qtd_batidas)
            if tipo == "caco":
                self.caco(j + self.meio(), quantidade=opcao or 1)
            elif tipo == "torre":
                self.bloco(j + self.degrauzinho(), self.nivel - 1)
            elif tipo == "vao":
                self.bota_buraco(j + q1, j + self.pouso(), self.nivel + 3)
            elif tipo == "ilha":
                quanto_muda = opcao or 0
                q3 = self.pouso()
                if quanto_muda < 0:
                    q3 = self.margem_de_subida()
                self.bota_piso(j, j + q1)
                self.bota_buraco(j + q1, j + q3, max(self.nivel, self.nivel + quanto_muda) + 3)
                self.nivel += quanto_muda
                self.bota_piso(j + q3, fim)
            elif tipo == "sobe":
                q3 = self.degrauzinho()
                self.bota_piso(j, j + q3)
                self.nivel -= opcao or 1
                self.bota_piso(j + q3, fim)
            self.b += qtd_batidas

    def meio_do_pulo(self, batida_n):
        return (self._x(batida_n) + self.L() * 0.5) * QUADRADO + TAM_DO_LEO * 0.5

    def anota_onde_cabe(self, tipo, qtd_batidas, opcao):
        f = self.f
        chao = self.nivel * QUADRADO
        if tipo in ("caco", "torre", "vao", "pausa") and not f.sem_segurar:
            k = 0.0
            if tipo != "pausa":
                k = f.batidas_do_pulo
            while k <= qtd_batidas - 1.0 + 1e-9:
                f.lugares_livres.append((self.b + k, self.meio_do_pulo(self.b + k), chao))
                k += 1.0
        ta_nivelado = tipo in ("caco", "vao") or (tipo == "ilha" and not opcao)
        if ta_nivelado and f.nome_da_musica in NOME_DA_PENDURADA and qtd_batidas >= f.batidas_do_pulo - 1e-9:
            f.lugares_altos.append((self.b, self.meio_do_pulo(self.b), chao))

    def bota_bando(self, qtd_batidas):
        f = self.f
        chao = self.nivel * QUADRADO
        for k in range(int(qtd_batidas + 1e-9)):
            f.voadores.add(Bichos(self.meio_do_pulo(self.b + k), chao, ENXAME))
            f.obstaculos_de_ritmo.append(self.b + k)
        self.dica_do_bando((self._x(self.b) + self.L() * 0.5) * QUADRADO, chao)

    def dica_do_bando(self, x, chao):
        if self.f.nome_da_musica in NOME_DO_BANDO:
            self.bota_dica("enxame", x, chao - ENXAME[2] - 0.9 * QUADRADO,
                           f"{NOME_DO_BANDO[self.f.nome_da_musica]}: NAO PULE")

    def dica_da_pendurada(self, x, chao):
        self.bota_dica("pingente", x, chao - PINGENTE[2] - 0.9 * QUADRADO,
                       f"{NOME_DA_PENDURADA[self.f.nome_da_musica]}: SO UM TOQUE")

    def bota_pendurada(self, qtd_batidas, quantidade):
        f = self.f
        j, fim = self.coluna_da_batida(self.b), self.coluna_da_batida(self.b + qtd_batidas)
        self.bota_piso(j, fim)
        self.caco(j + self.meio(), quantidade=quantidade)
        self.marca_toque(self.b, eco=False)
        f.curtos.add(round(self.b, 3))
        chao = self.nivel * QUADRADO
        x = self.meio_do_pulo(self.b)
        f.voadores.add(CoisaPendurada(x, chao, PINGENTE))
        f.obstaculos_de_ritmo.append(self.b)
        f.bolinhas_extras.append(Bolinha(x - TAM_DO_LEO * 0.5, chao - f.altura_do_pulo * PULINHO, False))
        self.dica_da_pendurada(x, chao)

    def bota_buraco(self, c0, c1, ty):
        self.abre_buraco(c0, c1)
        for tx in range(c0, c1):
            self.caco(tx, ty, mata_na_hora=True)

    def dupla(self, *passos):
        f = self.f
        saltos, b = [], self.b
        for tipo, qtd_batidas, *_ in passos:
            if tipo != "pausa":
                saltos.append((self.coluna_da_batida(b), self._x(b) * QUADRADO))
            b += qtd_batidas
        topo = self.nivel - 2
        if not f.sem_segurar:
            self.bota_dica("dupla", saltos[0][1] + self.L() * QUADRADO * 0.5, (topo - 1.6) * QUADRADO,
                           "SEGURE: CAMINHO DE CIMA")
        f.duplas.append((self.b, b))
        self.bota_bolinha = False
        self.bota(*passos)
        self.bota_bolinha = True
        vaos = set()
        for j, _ in saltos[1:]:
            vaos.update(range(j + self.beirada(), j + self.pouso()))
        for tx in range(saltos[0][0] + self.pouso(), saltos[-1][0] + self.L() + 2):
            if tx not in vaos:
                f.pontes.add((tx, topo))
        for seta in f.toques_certos:
            if (int(seta.x // QUADRADO), topo) in f.pontes:
                seta.y = topo * QUADRADO
        for k, (_, x) in enumerate(saltos[1:]):
            if k % 2 == 0 or f.sem_segurar:
                f.bolinhas_extras.append(Bolinha(x + self.L() * QUADRADO * 0.5,
                                                 topo * QUADRADO - f.altura_do_pulo, True))
        if not f.sem_segurar:
            for _, x in saltos:
                f.bolinhas_extras.append(Bolinha(x + self.L() * QUADRADO * 0.5,
                                                 self.nivel * QUADRADO - f.altura_do_pulo * PULINHO, False))

    def repete(self, tipo, qtd_batidas, a_cada, opcao=None):
        n = int(qtd_batidas / a_cada + 1e-9)
        self.bota(*[(tipo, a_cada, opcao)] * n)
        self.descanso(qtd_batidas - n * a_cada)

    def descanso(self, qtd_batidas):
        if qtd_batidas > 1e-9:
            self.bota(("pausa", qtd_batidas))

    def cacos(self, qtd_batidas, a_cada=2, quantidade=1):
        self.repete("caco", qtd_batidas, a_cada, quantidade)

    def cacos_quebrados(self, qtd_batidas, quantidade=1):
        self.repete("caco", qtd_batidas, self.f.batidas_do_pulo + 0.5, quantidade)

    def torres(self, qtd_batidas, a_cada=2):
        self.repete("torre", qtd_batidas, a_cada)

    def ilhas(self, niveis_das_ilhas, a_cada=2):
        self.bota(*[("ilha", a_cada, d) for d in niveis_das_ilhas])

    def sobe_escada(self, n_degraus, a_cada=2, altura=1):
        self.bota(*[("sobe", a_cada, altura)] * n_degraus)

    def desce_escada(self, n_degraus):
        self.bota(*[("desce", 1)] * n_degraus)

    def bota_morro(self, altura, *topo):
        self.sobe_escada(altura)
        self.bota(*topo)
        self.desce_escada(altura)

    def zigzag(self, pares, a_cada=2):
        for k in range(pares * 2):
            ta_subindo = k % 2 == 0
            j = self.coluna_da_batida(self.b)
            corte = self.degrauzinho() if ta_subindo else self.meio()
            self.bota_piso(j, j + corte)
            self.marca_toque(self.b)
            self.nivel += -1 if ta_subindo else 1
            self.bota_piso(j + corte, self.coluna_da_batida(self.b + a_cada))
            self.b += a_cada
        self.acabou_de_descer = a_cada <= self.f.batidas_do_pulo + 1e-9

    def tira_tedio(self):
        f = self.f
        if f.sem_segurar:
            return
        obstaculos_de_ritmo = sorted(f.obstaculos_de_ritmo)
        lugares_livres = sorted(f.lugares_livres)
        ultimo, fim = min(f.batidas_de_pular), max(f.batidas_de_pular)
        while ultimo + TEMPO_SEM_NADA < fim:
            limite = ultimo + TEMPO_SEM_NADA
            ja = [g for g in obstaculos_de_ritmo if ultimo < g <= limite]
            if ja:
                ultimo = ja[-1]
                continue
            os_que_cabem = [p for p in lugares_livres if ultimo < p[0] <= limite]
            os_altos = [p for p in f.lugares_altos if ultimo < p[0] <= limite]
            if os_que_cabem:
                ultimo = self.bota_bando_em(*os_que_cabem[-1])
            elif os_altos:
                ultimo = self.pendura(*os_altos[-1])
            else:
                depois = [(g, None, None) for g in obstaculos_de_ritmo if g > limite]
                depois += [p for p in lugares_livres if p[0] > limite]
                depois += [p for p in f.lugares_altos if p[0] > limite]
                ultimo = min(p[0] for p in depois)
                if ultimo in [p[0] for p in lugares_livres]:
                    self.bota_bando_em(*[p for p in lugares_livres if p[0] == ultimo][0])
                elif ultimo in [p[0] for p in f.lugares_altos]:
                    self.pendura(*[p for p in f.lugares_altos if p[0] == ultimo][0])
            obstaculos_de_ritmo.append(ultimo)
            obstaculos_de_ritmo.sort()

    def bota_bando_em(self, b, x, chao):
        self.f.voadores.add(Bichos(x, chao, ENXAME))
        self.dica_do_bando(x, chao)
        return b

    def pendura(self, b, x, chao):
        f = self.f
        f.voadores.add(CoisaPendurada(x, chao, PINGENTE))
        f.curtos.add(round(b, 3))
        f.saltos = [s for s in f.saltos if abs(s[0] - b) > 1e-6]
        f.bolinhas_extras.append(Bolinha(x - TAM_DO_LEO * 0.5, chao - f.altura_do_pulo * PULINHO, False))
        self.dica_da_pendurada(x, chao)
        return b

    def fim(self, qtd_batidas=6):
        f = self.f
        self.tira_tedio()
        c1 = self.coluna_da_batida(self.b + qtd_batidas)
        self.bota_piso(self.coluna_da_batida(self.b), c1 + 40)
        self.b += qtd_batidas
        f.x_do_fim = c1 * QUADRADO
        f.duracao = self.b * f.tempo_da_batida
        f.batidas_de_pular.sort()
        f.chao = MapaDaFase([PedacoDeChao(f, tx, n) for tx, n in f.chao_por_coluna.items()])
        f.pontezinhas = MapaDaFase([Pontezinha(f, tx, ty) for tx, ty in f.pontes])
        f.torres = MapaDaFase([BlocoDuro(f, tx, ty) for tx, ty in f.blocos])
        for tile in f.chao.get_solidos() + f.torres.get_solidos():
            for casa in tile.casas():
                f.solidos[casa] = tile
        f.molas.ordena(lambda m: m.x)
        for p in f.coisas_que_machucam:
            f.perigos_por_coluna.add(p, (int(p.x // QUADRADO),))
        f.voadores.ordena(lambda v: (v.x, v.y, v.width, v.height, v.tipo))
        for v in f.voadores:
            if v.tipo == "enxame":
                f.bandos.add(v)
            else:
                f.penduradas.add(v)
            f.voadores_por_coluna.add(v, range(int(v.x // QUADRADO), int((v.x + v.width) // QUADRADO) + 1))
        f.enfeites.add(PortalDoFim(c1 * QUADRADO, (self.nivel - 4) * QUADRADO, QUADRADO * 2, QUADRADO * 4))
        self.bota_bolinhas()
        self.enfeita()
        return f

    def bota_bolinhas(self):
        f = self.f
        desenho = ("alto", "baixo", "alto", None, "baixo")
        for batida_n, x, y in f.saltos:
            tipo = desenho[(int(batida_n // 8) + f.semente) % len(desenho)]
            if tipo is None:
                continue
            alto = tipo == "alto" or f.sem_segurar
            meio = f.velocidade_em(x + 1.0) * f.tempo_do_pulo * 0.5
            sobe = f.altura_do_pulo
            if not alto:
                sobe *= PULINHO
            f.bolinhas.add(Bolinha(x + meio, y - sobe, alto))
        f.bolinhas.add(*f.bolinhas_extras)
        f.bolinhas.ordena(lambda eco: eco.ordem_dela())
        for i, eco in enumerate(f.bolinhas):
            eco.numero = i

    def enfeita(self):
        f = self.f
        ja_tem_coisa = set()
        for p in f.coisas_que_machucam:
            ja_tem_coisa.add(int(p.x // QUADRADO))
            if not p.mata_na_hora:
                afasta(ja_tem_coisa, int(p.x // QUADRADO), 2)
        for m in f.toques_certos:
            ja_tem_coisa.add(int(m.x // QUADRADO))
        for d in f.enfeites:
            ja_tem_coisa.update(colunas_do_enfeite(d))
        for tx, _ in f.blocos:
            afasta(ja_tem_coisa, tx, 2)
        for m in f.molas:
            for k in range(int((m.fim - m.x) // QUADRADO) + 2):
                afasta(ja_tem_coisa, int(m.x // QUADRADO) + k, 2)
        for tx, _ in f.pontes:
            ja_tem_coisa.add(tx)
        for tx in f.voadores_por_coluna:
            afasta(ja_tem_coisa, tx, 1)
        lugares_vazios = []
        for tx, n in f.chao_por_coluna.items():
            ta_plano = f.chao_por_coluna.get(tx - 1) == n == f.chao_por_coluna.get(tx + 1)
            if ta_plano and tx not in ja_tem_coisa:
                lugares_vazios.append((tx, n))
        if f.nome_da_musica == "bosque":
            for tx, n in lugares_vazios:
                numero_sorteado = (tx * 2654435761 >> 7) % 100
                if tx % 5 == 2 and numero_sorteado < 80:
                    f.enfeites.add(Arvorezona((tx - 1) * QUADRADO, (n - 4) * QUADRADO, 3 * QUADRADO, 4 * QUADRADO,
                                              numero_sorteado % 7))
        ja_tem_enfeite = set()
        for d in f.enfeites:
            ja_tem_enfeite.update(colunas_do_enfeite(d))
        for tx, n in lugares_vazios:
            numero_sorteado = (tx * 2246822519 >> 9) % 100
            if tx % 4 == 1 and tx not in ja_tem_enfeite and numero_sorteado < 70:
                enfeite = Enfeite(tx * QUADRADO, (n - 2) * QUADRADO, QUADRADO, 2 * QUADRADO, (tx * 40503 >> 4) % 97)
                enfeite.ato = f.ato(tx * QUADRADO)
                f.enfeites.add(enfeite)


def afasta(ja_tem_coisa, tx, quanto):
    for k in range(-quanto, quanto + 1):
        ja_tem_coisa.add(tx + k)


def colunas_do_enfeite(d):
    tx = int(d.x // QUADRADO)
    return range(tx, tx + int(d.width // QUADRADO))


def fase_do_bosque():
    c = MontaFase(Fasezinha(0, "BOSQUE DOS ECOS", "FACIL", "bosque"))
    c.comeca_parte("introducao")
    c.bota(("pausa", 2), ("caco", 2))
    c.comeca_parte("A")
    c.bota(("caco", 2), ("torre", 2))
    c.bota_morro(2, ("caco", 2), ("caco", 2))
    c.bota(("mola", 4), ("pausa", 2))
    c.dupla(("caco", 2), ("torre", 2), ("caco", 2, 2), ("pausa", 2))
    c.bota(("vao", 2), ("caco", 2), ("vao", 2), ("vao", 2))
    c.bota_morro(1, ("torre", 2), ("caco", 1.5), ("caco", 1.5), ("caco", 1.5), ("caco", 1.5))
    c.descanso(1)
    c.comeca_parte("B")
    c.bota(("pausa", 2), ("vao", 4), ("mola", 4, -3))
    c.bota(("caco", 2), ("caco", 2), ("ilha", 4, -1), ("torre", 2), ("torre", 2))
    c.bota(("ilha", 4, 1), ("vao", 2), ("desce", 1, 3), ("pausa", 3))
    c.comeca_parte("A'")
    c.zigzag(2)
    c.cacos(6, a_cada=1)
    c.descanso(1)
    c.velocidade(8)
    c.descanso(1)
    c.bota(("caco", 2), ("vao", 2), ("caco", 2, 2), ("vao", 2))
    c.bota(("mola", 4, "vao"), ("caco", 2), ("caco", 2))
    return c.fim(6)


def fase_das_dunas():
    c = MontaFase(Fasezinha(3, "DUNAS DO CHOCALHO", "MODERADO", "dunas"))
    c.comeca_parte("introducao")
    c.bota(("pausa", 2), ("caco", 2), ("caco", 2))
    c.bota(("enxame", 4))
    c.bota(("torre", 2), ("caco", 1), ("caco", 1), ("pausa", 2))
    c.comeca_parte("A")
    c.bota(("caco", 2), ("caco", 2, 2), ("vao", 2), ("enxame", 2))
    c.bota(("sobe", 2), ("sobe", 2), ("caco", 1), ("caco", 1), ("pausa", 2))
    c.bota(("torre", 2), ("enxame", 2), ("desce", 1), ("desce", 1), ("vao", 2))
    c.bota(("mola", 4), ("caco", 2), ("caco", 2, 2))
    c.bota(("ilha", 2, 0), ("ilha", 2, -1), ("ilha", 2, 1), ("enxame", 2))
    c.bota(("vao", 2), ("vao", 2), ("caco", 1), ("caco", 1), ("caco", 1), ("pausa", 1))
    c.comeca_parte("B")
    c.bota(("pausa", 2), ("mola", 4, -3), ("pausa", 2))
    c.bota(("ilha", 4, 0), ("ilha", 4, -1))
    c.bota(("enxame", 2), ("caco", 2), ("enxame", 2), ("caco", 2))
    c.bota(("ilha", 2, 1), ("torre", 2), ("ilha", 2, 1), ("pausa", 2))
    c.bota(("sobe", 2), ("caco", 2), ("sobe", 2), ("caco", 2))
    c.bota(("caco", 1), ("caco", 1), ("caco", 1), ("caco", 1), ("enxame", 2), ("mola", 2, "vao"))
    c.comeca_parte("A'")
    c.bota(("caco", 1), ("caco", 1, 2), ("desce", 1), ("caco", 1), ("caco", 1), ("caco", 1, 2),
           ("desce", 1), ("caco", 1))
    c.bota(("caco", 1), ("caco", 1), ("enxame", 2), ("caco", 1), ("caco", 1, 2), ("enxame", 2))
    c.dupla(("caco", 2), ("caco", 2, 2), ("caco", 2), ("pausa", 2))
    c.bota(("caco", 1.5), ("caco", 1.5), ("caco", 1), ("caco", 1.5), ("caco", 1.5), ("caco", 1))
    c.bota(("ilha", 1, 1), ("ilha", 1, 0), ("ilha", 2, 1), ("torre", 1), ("torre", 1), ("pausa", 2))
    c.bota(("caco", 1), ("caco", 1), ("caco", 1, 2), ("caco", 1), ("caco", 1, 3), ("pausa", 1),
           ("mola", 2, "vao"))
    return c.fim(6)


def linhas_de_salto(*niveis_das_ilhas):
    return [("ilha", 1, d) for d in niveis_das_ilhas]


def fase_das_ilhas():
    c = MontaFase(Fasezinha(1, "ILHAS SUSPENSAS", "NORMAL", "ilhas"))
    c.comeca_parte("introducao")
    c.descanso(2)
    c.ilhas((0, -1, 1))
    c.bota(("enxame", 2), ("mola", 4, "vao"))
    c.descanso(1)
    c.velocidade(8)
    c.descanso(1)
    c.comeca_parte("A")
    c.bota(("ilha", 1, 0), ("ilha", 1, -1), ("ilha", 2, 1), ("ilha", 1, 0), ("ilha", 1, -1),
           ("ilha", 2, 1))
    c.bota(("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1),
           ("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1))
    c.bota(("caco", 2), ("enxame", 2), ("caco", 1), ("ilha", 1, -1), ("ilha", 2, 1))
    c.bota(*linhas_de_salto(0, -1, 0, 1), ("ilha", 1, -1), ("ilha", 1, 0), ("ilha", 2, 1))
    c.bota(("pingente", 2), ("ilha", 1, -1), ("ilha", 1, 1), ("pingente", 2), ("ilha", 2, 0))
    c.dupla(("caco", 2), ("caco", 1, 2), ("pausa", 1))
    c.bota(("caco", 2), ("enxame", 2))
    c.bota(("ilha", 1.5, -1), ("ilha", 1.5, 1), ("ilha", 1, 0), ("caco", 1), ("caco", 1, 2),
           ("ilha", 2, 0))
    c.bota(*linhas_de_salto(0, -1, 1), ("mola", 4, "vao"))
    c.velocidade(6)
    c.descanso(1)
    c.comeca_parte("B")
    c.bota(("ilha", 2, -1), ("ilha", 2, 0), ("ilha", 2, 1), ("enxame", 2))
    c.bota(("mola", 3, "orbe"), ("desce", 1, 3), ("pausa", 1), ("desce", 1, 3), ("ilha", 2, 0))
    c.bota(*linhas_de_salto(1, 0), ("caco", 1, 2), ("ilha", 1, 0), ("ilha", 1.5, -1), ("ilha", 1.5, 1),
           ("ilha", 1, 0))
    c.bota(("caco", 2), ("enxame", 2), ("ilha", 1, -1), ("ilha", 1, 1))
    c.descanso(1)
    c.velocidade(8)
    c.descanso(1)
    c.comeca_parte("A'")
    c.bota(*linhas_de_salto(0, -1, 0, 1), ("caco", 2), ("enxame", 2))
    c.bota(("ilha", 1, -1), ("ilha", 1, 0), ("ilha", 1.5, 1), ("ilha", 1.5, -1), ("ilha", 1, 1),
           ("caco", 1, 3), ("caco", 1))
    c.bota(("caco", 1), ("caco", 1, 2), ("ilha", 1, -1), ("pingente", 2), ("ilha", 1, 1),
           ("ilha", 2, 0))
    c.bota(("ilha", 1.5, -1), ("ilha", 1.5, -1), ("ilha", 1, 1),
           ("ilha", 1.5, 0), ("ilha", 1.5, 1), ("ilha", 1, 0))
    c.bota(("caco", 2), ("enxame", 2), ("pingente", 2), ("enxame", 2))
    c.bota(*linhas_de_salto(0, 0, -1, 0, 1, 0), ("ilha", 2, 0))
    c.bota(("caco", 1), ("ilha", 1, -1), ("caco", 1), ("ilha", 1, 0),
           ("caco", 1, 2), ("ilha", 1, 1), ("ilha", 2, 0))
    c.dupla(("caco", 1, 3), ("caco", 1), ("pausa", 2))
    c.bota(("mola", 4, "vao"))
    return c.fim(6)


def fase_da_geleira():
    c = MontaFase(Fasezinha(4, "GELEIRA DA AURORA", "AVANCADO", "geleira"))
    c.comeca_parte("introducao")
    c.descanso(2)
    c.bota(("caco", 2), ("caco", 2), ("torre", 2), ("caco", 2))
    c.bota(("pingente", 4))
    c.bota(("caco", 2), ("pingente", 2), ("caco", 2), ("pingente", 2))
    c.bota(("ilha", 2, 0), ("ilha", 2, -1), ("ilha", 2, 1), ("caco", 1), ("caco", 1))
    c.descanso(2)
    c.comeca_parte("A")
    c.bota(*linhas_de_salto(0, -1, 0, 1))
    c.bota(("caco", 1), ("pingente", 1), ("caco", 1), ("pingente", 1))
    c.bota(("sobe", 1), ("caco", 1), ("sobe", 1), ("caco", 1, 2))
    c.desce_escada(2)
    c.descanso(2)
    c.torres(4, a_cada=1)
    c.bota(("caco", 2), ("enxame", 2))
    c.zigzag(2, a_cada=1)
    c.bota(("vao", 1), ("vao", 1), ("caco", 1), ("pingente", 1))
    c.descanso(1)
    c.velocidade(7)
    c.descanso(1)
    c.bota(*linhas_de_salto(0, -1, 0, 1), ("ilha", 1, 0), ("ilha", 1, -1), ("ilha", 2, 1))
    c.bota(("caco", 1), ("caco", 1, 2), ("pingente", 1), ("ilha", 1, -1), ("caco", 1),
           ("pingente", 1, 2), ("ilha", 1, 1), ("caco", 1))
    c.bota(("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1),
           ("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1))
    c.dupla(("caco", 2), ("caco", 1, 2), ("caco", 1, 3), ("pausa", 1))
    c.velocidade(6)
    c.descanso(1)
    c.comeca_parte("B")
    c.bota(("ilha", 2, -1), ("ilha", 2, 0), ("ilha", 2, 1), ("pingente", 2))
    c.bota(("mola", 3, "orbe"), ("desce", 1, 3), ("pausa", 1), ("desce", 1, 3), ("ilha", 2, 0))
    c.bota(("caco", 2), ("pingente", 2), ("caco", 2, 2), ("pingente", 2))
    c.bota(("ilha", 2, -1), ("torre", 2), ("ilha", 2, 1), ("pingente", 2))
    c.bota(("caco", 1), ("caco", 1), ("pingente", 1), ("caco", 1), ("caco", 1), ("caco", 2, 2),
           ("pingente", 1))
    c.bota(("caco", 1), ("caco", 1), ("caco", 1), ("pingente", 1), ("caco", 1), ("caco", 1, 2))
    c.descanso(1)
    c.velocidade(7)
    c.descanso(1)
    c.comeca_parte("A'")
    c.bota(("caco", 2), ("pingente", 1), ("caco", 1))
    c.bota(("caco", 2), ("caco", 2))
    c.bota(("caco", 1), ("caco", 1), ("pingente", 1), ("pingente", 1))
    c.bota(("pingente", 2), ("pingente", 1), ("pingente", 1))
    c.bota(("caco", 2), ("pingente", 1), ("caco", 1))
    c.bota(("sobe", 1), ("sobe", 1), ("caco", 2))
    c.bota(("caco", 1), ("caco", 1), ("caco", 1), ("caco", 1))
    c.bota(("pingente", 2), ("pingente", 1), ("desce", 1, 2))
    c.dupla(("caco", 2, 2), ("caco", 2, 2), ("caco", 2, 2), ("pausa", 2))
    c.bota(("mola", 2, -3))
    c.bota(("caco", 1), ("pingente", 1), ("caco", 1, 2), ("pausa", 1))
    c.desce_escada(3)
    c.descanso(1)
    c.bota(*linhas_de_salto(0, -1, 0, 1))
    c.bota(("caco", 1), ("pingente", 1), ("caco", 1, 2), ("pingente", 1))
    c.bota(("ilha", 1, -1), ("ilha", 1, 0), ("ilha", 2, 1))
    c.bota(("mola", 2, "vao"))
    return c.fim(6)


def fase_do_eclipse():
    c = MontaFase(Fasezinha(2, "CIDADELA DO ECLIPSE", "DIFICIL", "eclipse"))
    c.comeca_parte("introducao")
    c.descanso(2)
    c.bota(("torre", 2), ("torre", 2), ("mola", 4))
    c.sobe_escada(2)
    c.bota(("caco", 2), ("torre", 2), ("caco", 2, 2), ("pausa", 2))
    c.desce_escada(2)
    c.bota(("vao", 2), ("caco", 2), ("caco", 1), ("caco", 1), ("pausa", 2))
    c.comeca_parte("A")
    c.torres(6, a_cada=1)
    c.bota(("torre", 2))
    c.bota(("sobe", 1), ("caco", 1), ("sobe", 1), ("caco", 1, 2), ("vao", 1), ("vao", 1),
           ("sobe", 1), ("sobe", 1))
    c.desce_escada(4)
    c.descanso(1)
    c.bota(("caco", 1), ("caco", 2, 2), ("caco", 1), ("caco", 2, 2), ("caco", 1), ("caco", 1),
           ("caco", 2, 3), ("caco", 1), ("caco", 1))
    c.bota(("vao", 1), ("vao", 1), ("caco", 1, 2), ("vao", 1), ("vao", 1), ("caco", 1, 3),
           ("vao", 1), ("vao", 1))
    c.bota(("mola", 2, -4), ("pausa", 2))
    c.zigzag(2, a_cada=1)
    c.desce_escada(4)
    c.descanso(1)
    c.bota(("vao", 1), ("vao", 1), ("vao", 1), ("vao", 1), ("mola", 4, "vao"))
    c.descanso(1)
    c.velocidade(5)
    c.descanso(1)
    c.comeca_parte("B")
    c.bota(("vao", 2), ("vao", 2), ("caco", 2, 2), ("pausa", 2))
    c.dupla(("caco", 2), ("caco", 2, 2), ("pausa", 2))
    c.bota(("sobe", 2), ("caco", 2), ("sobe", 2), ("enxame", 2))
    c.bota(("caco", 2), ("torre", 2), ("desce", 1), ("desce", 1), ("vao", 2))
    c.bota(("caco", 1), ("caco", 1), ("pausa", 2), ("caco", 1), ("caco", 2, 2), ("caco", 1))
    c.bota(("vao", 2), ("caco", 2, 3), ("enxame", 2))
    c.bota(("sobe", 2), ("caco", 2, 2), ("mola", 3, "orbe"), ("pausa", 2))
    c.bota(("desce", 1, 4), ("desce", 1, 3), ("pausa", 1))
    c.bota(("caco", 2), ("caco", 2), ("caco", 1), ("caco", 1))
    c.descanso(1)
    c.velocidade(7)
    c.descanso(1)
    c.comeca_parte("A'")
    c.dupla(("caco", 2, 2), ("caco", 2, 2), ("caco", 2, 2), ("pausa", 2))
    c.bota(("caco", 1), ("caco", 1), ("enxame", 2))
    c.bota(("ilha", 1, 0), ("ilha", 1, -1), ("ilha", 2, 1))
    c.bota(("caco", 1), ("pingente", 1), ("caco", 1), ("pingente", 1))
    c.bota(("mola", 4, "vao"))
    c.bota(("caco", 1), ("pingente", 1), ("enxame", 2), ("ilha", 1, -1), ("ilha", 1, 0),
           ("ilha", 2, 1))
    c.bota(("sobe", 1), ("sobe", 1), ("sobe", 1), ("caco", 1), ("sobe", 1), ("caco", 1, 2),
           ("pausa", 2))
    c.torres(6, a_cada=1)
    c.descanso(2)
    c.desce_escada(4)
    c.bota(("vao", 1), ("caco", 1), ("vao", 1), ("caco", 1, 2), ("vao", 1), ("caco", 1, 3),
           ("vao", 1), ("vao", 1))
    c.bota(("caco", 2), ("enxame", 1))
    c.velocidade(8)
    c.descanso(1)
    c.cacos_quebrados(12, quantidade=2)
    c.cacos(8, a_cada=1, quantidade=2)
    c.descanso(1)
    c.zigzag(2, a_cada=1)
    c.bota(("pingente", 1), ("caco", 1))
    c.bota(("vao", 1), ("caco", 1), ("mola", 3, "vao"))
    return c.fim(8)


FAZEDORES_DE_FASE = (fase_do_bosque, fase_das_dunas, fase_das_ilhas, fase_da_geleira, fase_do_eclipse)
fases_prontas = {}


def carrega_fase(indice):
    if indice not in fases_prontas:
        fases_prontas[indice] = FAZEDORES_DE_FASE[indice]()
        fases_prontas[indice].qual_fase = indice
    return fases_prontas[indice]


def fase_do_mundo(nome_da_musica):
    for f in todas():
        if f.nome_da_musica == nome_da_musica:
            return f


def todas():
    return [carrega_fase(i) for i in range(len(FAZEDORES_DE_FASE))]
