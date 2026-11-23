"""
Folha de contato: varias imagens ampliadas lado a lado, sobre um fundo neutro.

    ./.venv/bin/python ferramentas/geradores/folha.py SAIDA ZOOM LARGURA arquivos...
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.init()
pygame.display.set_mode((1, 1))
saida, zoom, larg = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
imgs = [pygame.transform.scale_by(pygame.image.load(a).convert_alpha(), zoom) for a in sys.argv[4:]]
x = y = 6
linha = 0
pos = []
for im in imgs:
    if x + im.get_width() > larg and x > 6:
        x, y, linha = 6, y + linha + 6, 0
    pos.append((x, y))
    x += im.get_width() + 6
    linha = max(linha, im.get_height())
s = pygame.Surface((larg, y + linha + 6))
s.fill((90, 130, 150))
for im, p in zip(imgs, pos):
    s.blit(im, p)
pygame.image.save(s, saida)
