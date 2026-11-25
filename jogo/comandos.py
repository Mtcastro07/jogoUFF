import pygame
from PPlay.input_manager import InputManager
from PPlay.keyboard import Keyboard
from PPlay.mouse import Mouse
from PPlay.window import Window

TECLAS_DO_JOGO = {
    "pular": ["SPACE", "UP", "W"],
    "largada": ["SPACE"],
    "recomecar": ["R"],
    "cima": ["UP", "W"],
    "baixo": ["DOWN", "S"],
    "esquerda": ["LEFT", "A"],
    "direita": ["RIGHT", "D"],
    "confirmar": ["ENTER", "KP_ENTER", "SPACE"],
    "voltar": ["ESC"],
}
for nome, teclas in TECLAS_DO_JOGO.items():
    InputManager.define_action(nome, teclas)


class TecladoDoJogo(Keyboard):
    def __init__(self, os_controles):
        super().__init__()
        self.mapa["KP_ENTER"] = pygame.K_KP_ENTER
        self.mapa["F11"] = pygame.K_F11
        self.os_controles = os_controles

    def key_pressed(self, key):
        if self._get_code(key) == pygame.K_SPACE and self.os_controles.ta_segurado():
            return True
        return super().key_pressed(key)

    def qualquer_tecla(self):
        for ev in Window.get_instance().eventos:
            if ev.type == pygame.KEYDOWN and ev.key != pygame.K_F11:
                return True
        return False


class Mouzinho(Mouse):
    def mouse_mexeu(self):
        for ev in Window.get_instance().eventos:
            if ev.type == pygame.MOUSEMOTION:
                return True
        return False

    def is_over_object(self, obj):
        mx, my = self.get_position()
        if mx >= obj.x + obj.width or my >= obj.y + obj.height:
            return False
        return super().is_over_object(obj)


class Controlezinho:
    COMO_PULA = (0, 2, 3)
    VOLTA = (1, 6, 7, 9)

    def __init__(self):
        self.controles_ligados = {}

    def ta_segurado(self):
        try:
            for c in self.controles_ligados.values():
                for b in self.COMO_PULA:
                    if b < c.get_numbuttons() and c.get_button(b):
                        return True
        except pygame.error:
            pass
        return False

    def liga_controle(self, qual):
        try:
            c = pygame.joystick.Joystick(qual)
            self.controles_ligados[c.get_instance_id()] = c
        except pygame.error:
            pass

    def traduz(self, ev):
        tecla = None
        if ev.type == pygame.JOYDEVICEADDED:
            self.liga_controle(ev.device_index)
        elif ev.type == pygame.JOYDEVICEREMOVED:
            self.controles_ligados.pop(ev.instance_id, None)
        elif ev.type == pygame.JOYBUTTONDOWN:
            if ev.button in self.COMO_PULA:
                tecla = pygame.K_SPACE
            elif ev.button in self.VOLTA:
                tecla = pygame.K_ESCAPE
        elif ev.type == pygame.JOYHATMOTION:
            hx, hy = ev.value
            if hy > 0:
                tecla = pygame.K_UP
            elif hy < 0:
                tecla = pygame.K_DOWN
            elif hx > 0:
                tecla = pygame.K_RIGHT
            elif hx < 0:
                tecla = pygame.K_LEFT
        if tecla is None:
            return ev
        return pygame.event.Event(pygame.KEYDOWN, key=tecla, mod=0, unicode="")
