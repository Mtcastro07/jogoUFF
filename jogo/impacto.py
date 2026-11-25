from PPlay.effects import ScreenEffects


class Impacto(ScreenEffects):
    QUAO_RAPIDO_ACALMA = 40.0
    comeco_do_clarao = 0.0

    @classmethod
    def novo(cls):
        return type("Impacto", (cls,), {})

    @classmethod
    def shake(cls, intensidade):
        mais_forte = max(cls._shake_intensity, intensidade)
        super().shake(mais_forte, mais_forte / cls.QUAO_RAPIDO_ACALMA)

    @classmethod
    def update(cls, dt):
        cls._shake_intensity = max(0.0, cls._shake_intensity - dt * cls.QUAO_RAPIDO_ACALMA)
        cls._shake_time = cls._shake_intensity / cls.QUAO_RAPIDO_ACALMA

    @classmethod
    def flash(cls, cor, duracao, agora):
        super().flash(cor, duracao)
        cls.comeco_do_clarao = agora

    @classmethod
    def quanto_clarao(cls, agora):
        if cls._flash_time <= 0.0:
            return 0.0
        return max(0.0, 1.0 - (agora - cls.comeco_do_clarao) / cls._flash_time)

    @classmethod
    def draw_flash(cls, tela, veu, agora, alfa):
        forca = cls.quanto_clarao(agora)
        if forca > 0.0:
            veu.fill(cls._flash_color)
            veu.set_alpha(int(alfa * forca))
            tela.blit(veu, (0, 0))
