from . import aparencia, arte, terreno
from .config import QUADRADO, LARG_TELA, FOLGA_DO_CACO
from .mapa import o_que_aparece
from .objetos import Coisa, OQueTaVendo

FOSSO = {"bosque": terreno.fosso, "dunas": terreno.buraco_das_dunas, "geleira": terreno.buraco_da_geleira}
CACOS_DO_ATO = {
    "bosque": ((0,), (0, 1, 2), (3, 4, 1), (0, 3, 4, 2)),
    "dunas": ((0,), (0, 1), (2, 3), (0, 1, 2, 3)),
    "ilhas": ((0, 1), (0, 1, 2), (3, 4), (0, 1, 2, 3, 4)),
    "geleira": ((0,), (0, 1), (2, 3), (0, 1, 2, 3)),
    "eclipse": ((0, 2), (0, 1, 2), (4, 3), (0, 1, 2, 3, 4)),
}
leitos_feitos = {}


def prepara(fase):
    cores_da_fase = fase.cores_da_fase
    terreno.prepara(fase)
    pega_leitos(fase)
    sorteia_cacos(fase)
    figurinhas = []
    for p in fase.coisas_que_machucam:
        figurinhas.append(arte.caco(p.quantidade, cores_da_fase.nome, p.qual_desenho))
        p.perfil = arte.contorno_do_caco(p.quantidade, cores_da_fase.nome, FOLGA_DO_CACO, p.qual_desenho)
    for v in fase.voadores:
        figurinhas.append(arte.peca(v.tipo, cores_da_fase.nome))
    cor_do_brilho = arte.clareia(cores_da_fase.perigo, 0.3)
    for figurinha in figurinhas:
        for img in figurinha.quadros:
            arte.aura(img, cor_do_brilho, aparencia.RAIO_AURA)
    for d in fase.enfeites:
        if d.tipo == "arvore":
            aparencia.arvore(d, cores_da_fase)
        elif d.tipo == "enfeite":
            aparencia.enfeite(d, cores_da_fase)


def sorteia_cacos(fase):
    nome = fase.cores_da_fase.nome
    atos = CACOS_DO_ATO[nome]
    grupo = 0
    o_de_antes = None
    for p in sorted(fase.coisas_que_machucam, key=lambda p: (p.y, p.x)):
        if o_de_antes is None or p.y != o_de_antes.y or p.x - o_de_antes.x > QUADRADO:
            grupo = (int(p.x // QUADRADO) * 2654435761 >> 9) & 0xFFFF
        o_de_antes = p
        n = arte.quantos_cacos(p.quantidade, nome)
        quais = []
        for v in atos[min(fase.ato(p.x), len(atos) - 1)]:
            if v < n:
                quais.append(v)
        p.qual_desenho = quais[grupo % len(quais)]


def mostra_na_tela(tela, fase, leozinho, cam, pulso, espera=None, y_do_boneco=None,
                   com_heroi=True, rastro_do_leo=()):
    cores_da_fase = fase.cores_da_fase
    c0, c1 = o_que_aparece(cam)
    Coisa.o_que_ta_vendo = OQueTaVendo(tela, cores_da_fase, cam, leozinho.tempo, pulso, leozinho)
    fase.enfeites.draw()
    terreno.desenha_atras(tela, fase, cam, c0, c1, leozinho.tempo)
    fase.chao.draw()
    terreno.pula_pro_fim(fase, c1)
    fase.portais.draw()
    fase.pontezinhas.draw()
    fase.molas.draw()
    fase.torres.draw()

    for a, b, y in pega_leitos(fase):
        if a * QUADRADO < cam.x + LARG_TELA and b * QUADRADO > cam.x:
            if cores_da_fase.nome in FOSSO:
                FOSSO[cores_da_fase.nome](tela, a, b, y, cam)
            else:
                desenha_leito(tela, a, b, y, cam, aparencia.CORES_DO_LUGAR[cores_da_fase.nome][2])
    for tx in range(c0, c1):
        fase.perigos_por_coluna.em(tx).draw()
    fase.penduradas.draw()
    fase.bandos.draw()
    if fase.setinhas:
        fase.toques_certos.draw()
    fase.orbes.draw()

    for i, (img, x, y) in enumerate(rastro_do_leo):
        tela.blit(arte.fantasma(img, 40 + 30 * i), (cam.transform_x(x), cam.transform_y(y)))
    if com_heroi:
        if y_do_boneco is None:
            y_do_boneco = leozinho.y
        leozinho.draw(tela, cam, espera, y_do_boneco)


def desenha_bolinhas(tela, fase, cam, ecos, tempo):
    Coisa.o_que_ta_vendo = OQueTaVendo(tela, fase.cores_da_fase, cam, tempo)
    ecos.draw()


def icone_da_bolinha(cor):
    return aparencia.brilho(cor, False, 0)


def pega_leitos(fase):
    if fase.qual_fase not in leitos_feitos:
        os_soltos = set()
        for p in fase.coisas_que_machucam:
            casa = (int(p.x // QUADRADO), int((p.y + p.height) // QUADRADO))
            if casa not in fase.solidos:
                os_soltos.add(casa)
        faixas = []
        for tx, ty in sorted(os_soltos, key=lambda c: (c[1], c[0])):
            if faixas and faixas[-1][2] == ty * QUADRADO and faixas[-1][1] == tx:
                faixas[-1][1] = tx + 1
            else:
                faixas.append([tx, tx + 1, ty * QUADRADO])
        leitos_feitos[fase.qual_fase] = faixas
    return leitos_feitos[fase.qual_fase]


def desenha_leito(tela, a, b, y, cam, cores):
    cor_escura, cor_media, cor_clara = cores
    x0, x1 = a * QUADRADO - 6, b * QUADRADO + 6
    sy = cam.transform_y(y)
    for x in range(x0, x1, 4):
        fundo = 10 + ((x * 7919) >> 3) % 3 * 4
        tela.fill(cor_media, (cam.transform_x(x), sy, 4, fundo))
        tela.fill(cor_escura, (cam.transform_x(x), sy + fundo - 4, 4, 4))
    tela.fill(cor_clara, (cam.transform_x(x0), sy, x1 - x0, 2))
