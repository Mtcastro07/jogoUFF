"""
Julgamento ritmico: compara cada toque do jogador com a partitura.

Cada acao exigida pela fase tem um instante certo (uma "marca"). Quando o
jogador age, medimos a distancia entre o toque e a marca mais proxima:

    |dt| <= JANELA_PERFEITO * batida  ->  PERFEITO   50 pontos
    |dt| <= JANELA_BOM * batida       ->  BOM        25 pontos
    janela passou sem toque           ->  ERROU       0 pontos

Uma marca so e julgada uma vez. Tocar fora da partitura nao pune, e errar o
tempo tambem nao tira coracao: coracao so se perde batendo em alguma coisa.
"""

from .config import (JANELA_PERFEITO, JANELA_BOM, PONTOS_PERFEITO, PONTOS_BOM,
                     NOTAS)


class Julgamento:
    def __init__(self, tipo, tempo, pontos):
        self.tipo = tipo          # "perfeito", "bom" ou "erro"
        self.tempo = tempo
        self.pontos = pontos


class Ritmo:
    def __init__(self, fase):
        batida = fase.dur_batida
        self.jan_perfeito = JANELA_PERFEITO * batida
        self.jan_bom = JANELA_BOM * batida
        self.marcas = [b * batida for b in fase.acoes]
        self.julgados = [None] * len(self.marcas)
        self.cursor = 0           # primeira marca que ainda pode ser julgada
        self.pontos = 0
        self.perfeitos = self.bons = self.erros = 0
        self.combo = self.melhor_combo = 0
        self.ultimo = None        # ultimo Julgamento mostrado no HUD

    # ------------------------------------------------------------ consultas
    def maximo(self):
        return max(1, len(self.marcas) * PONTOS_PERFEITO)

    def precisao(self):
        return min(1.0, self.pontos / self.maximo())

    def nota(self):
        for limite, letra in NOTAS:
            if self.precisao() >= limite:
                return letra
        return "C"

    # ----------------------------------------------------------- julgamento
    def _pendente(self, tempo):
        """Indice da marca ainda nao julgada mais proxima de `tempo`."""
        melhor, melhor_d = None, None
        i = self.cursor
        while i < len(self.marcas) and self.marcas[i] <= tempo + self.jan_bom:
            d = abs(self.marcas[i] - tempo)
            if self.julgados[i] is None and (melhor_d is None or d < melhor_d):
                melhor, melhor_d = i, d
            i += 1
        return melhor

    def _registrar(self, i, tipo, tempo, mostrar=True):
        self.julgados[i] = tipo
        pontos = 0
        if tipo == "perfeito":
            self.perfeitos += 1
            pontos = PONTOS_PERFEITO
        elif tipo == "bom":
            self.bons += 1
            pontos = PONTOS_BOM
        else:
            self.erros += 1
        if pontos:
            self.pontos += pontos
            self.combo += 1
            self.melhor_combo = max(self.melhor_combo, self.combo)
        else:
            self.combo = 0
        if mostrar:
            self.ultimo = Julgamento(tipo, tempo, pontos)

    def tocar(self, tempo):
        """O jogador agiu. Devolve "perfeito", "bom" ou None (fora de qualquer marca)."""
        i = self._pendente(tempo)
        if i is None:
            return None
        desvio = abs(tempo - self.marcas[i])
        if desvio <= self.jan_perfeito:
            tipo = "perfeito"
        elif desvio <= self.jan_bom:
            tipo = "bom"
        else:
            return None
        self._registrar(i, tipo, tempo)
        return tipo

    def falhar(self, tempo):
        """O jogador bateu em algo: a marca aberta dessa batida (se houver) vira erro."""
        i = self._pendente(tempo)
        if i is not None:
            self._registrar(i, "erro", tempo)

    def expirar(self, tempo, mostrar=True):
        """Fecha as marcas cuja janela ja passou. Devolve quantas viraram erro."""
        novos = 0
        while (self.cursor < len(self.marcas) and
               self.marcas[self.cursor] < tempo - self.jan_bom):
            if self.julgados[self.cursor] is None:
                self._registrar(self.cursor, "erro", tempo, mostrar)
                novos += 1
            self.cursor += 1
        return novos

    def fechar(self):
        """No fim da fase, tudo que sobrou em aberto vira erro (sem mostrar)."""
        for i in range(len(self.marcas)):
            if self.julgados[i] is None:
                self._registrar(i, "erro", 0.0, mostrar=False)
        self.cursor = len(self.marcas)
