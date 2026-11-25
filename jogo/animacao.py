from PPlay.animation import Animation
from PPlay.camera import Camera
from PPlay.gameobject import GameObject

from .imagem import TemDesenho


class Animadinho(TemDesenho, Animation):
    def __init__(self, caminho, total_frames):
        super().__init__(caminho, total_frames)
        w = self.image.get_width() // total_frames
        self.quadros = []
        for i in range(total_frames):
            self.quadros.append(self.image.subsurface((i * w, 0, w, self.image.get_height())))
        self.width = w

    @classmethod
    def feito_de_quadros(cls, quadros):
        nova = cls.__new__(cls)
        GameObject.__init__(nova)
        nova.quadros = list(quadros)
        nova.image = nova.quadros[0]
        nova.width, nova.height = nova.image.get_size()
        nova.total_frames, nova.loop = len(nova.quadros), True
        nova.frame_atual, nova.rodando = 0, True
        nova.tempo_por_frame, nova.tempo_acumulado = 0.1, 0
        return nova

    def set_curr_frame(self, frame):
        super().set_curr_frame(int(frame) % self.total_frames)

    def cantinho(self):
        cam = Camera.get_instance()
        if cam is None:
            return self.x, self.y
        return cam.transform_x(self.x), cam.transform_y(self.y)

    def imagem_dele(self):
        return self.quadros[self.frame_atual]

    def pega_quadro(self, i):
        return self.quadros[int(i) % self.total_frames]
