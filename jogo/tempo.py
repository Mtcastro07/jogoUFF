from PPlay.timer import Timer
from PPlay.tween import Tween

from .janela import Janelona


class Agenda(Timer):
    _tasks = []

    @classmethod
    def nova(cls):
        return type("Agenda", (cls,), {"_tasks": []})

    @classmethod
    def after(cls, segundos, funcao, *args):
        super().after(segundos, funcao, *args)
        return cls._tasks[-1]

    @classmethod
    def limpar(cls):
        cls._tasks.clear()

    @classmethod
    def update(cls, dt):
        if cls._tasks:
            with Janelona.com_esse_tempo(dt):
                super().update()

    @classmethod
    def vai_ate(cls, agora):
        for tarefa in cls._tasks:
            tarefa.tempo_restante = tarefa.delay - agora
        cls.update(0.0)


class Curvas(Tween):
    _ativos = []

    @classmethod
    def nova(cls):
        return type("Curvas", (cls,), {"_ativos": []})

    @classmethod
    def to(cls, objeto, atributo, valor_final, duracao, tipo="linear", inicio=0.0, progresso=0.0):
        super().to(objeto, atributo, valor_final, duracao, tipo)
        cls._ativos[-1].update(inicio=inicio, progresso=progresso)

    @classmethod
    def limpar(cls):
        cls._ativos.clear()

    @classmethod
    def update(cls, dt):
        if cls._ativos:
            with Janelona.com_esse_tempo(dt):
                super().update()

    @classmethod
    def vai_ate(cls, agora):
        for curva in cls._ativos:
            curva["progresso"] = (agora - curva["inicio"]) / curva["dur"]
        cls.update(0.0)
