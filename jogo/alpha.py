"""
A VERSAO ALPHA de uma fase (temporario: para gravar o video do alpha).

E a fase de verdade, com os mesmos sprites, cenario e interface, so que
simplificada, como num alpha: o Leo anima normalmente, mas o fundo e PARADO
(so o ceu, o astro e os morros), o chao e uma reta lisa (sem degraus nem
buracos), a camera nao sobe nem treme, o Leo nao tem sombra, os cacos nao
falham, nao ha particulas, animacao de morte, efeitos sonoros (so a musica)
nem a apresentacao da musica, e na tela ficam so os coracoes.

Quais mundos saem assim: config.ALPHA. Para voltar a versao final, deixe
ALPHA vazio -- este arquivo pode ate ser apagado depois.
"""

from . import arte, mundo
from .config import VIDAS, VERMELHO


def desenhar(tela, partida, cam_x, cam_y, espera):
    """O quadro da partida na versao alpha (a pausa e os letreiros vem por cima)."""
    fase, est = partida.fase, partida.est
    partida.cenario.desenhar(tela, cam_x, cam_y, 0.0, 0.0, simples=True)
    mundo.desenhar(tela, fase, est, cam_x, cam_y, 0.0, espera, partida.y_desenho, simples=True)
    _hud(tela, partida)


def _hud(tela, partida):
    """Na tela, so os coracoes."""
    for i in range(VIDAS):
        img = arte.coracao(36, VERMELHO, i < partida.est.vidas, False)
        tela.blit(img, img.get_rect(center=(28 + i * 46 + 18, 46)))
