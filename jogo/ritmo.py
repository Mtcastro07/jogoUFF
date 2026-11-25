from .config import (TEMPO_PERFEITO, TEMPO_BOM, PONTOS_DO_PERFEITO, PONTOS_DO_BOM,
                     NOTAS)


class SeAcertou:
    def __init__(self, tipo, tempo, pontos):
        self.tipo = tipo
        self.tempo = tempo
        self.pontos = pontos


class ContaRitmo:
    def __init__(self, fase):
        batida_n = fase.tempo_da_batida
        self.tempo_do_perfeito = TEMPO_PERFEITO * batida_n
        self.tempo_do_bom = TEMPO_BOM * batida_n
        self.toques_certos = [b * batida_n for b in fase.batidas_de_pular]
        self.ja_julgados = [None] * len(self.toques_certos)
        self.cursor = 0
        self.pontos = 0
        self.bonus = 0
        self.perfeitos = self.bons = self.erros = 0
        self.combo = self.maior_combo = 0
        self.ultimo = None

    def precisao(self):
        return min(1.0, self.pontos / (len(self.toques_certos) * PONTOS_DO_PERFEITO))

    def nota(self):
        for limite, letra in NOTAS:
            if self.precisao() >= limite:
                return letra

    def qual_falta(self, tempo):
        melhor = None
        menor = 999
        i = self.cursor
        while i < len(self.toques_certos) and self.toques_certos[i] <= tempo + self.tempo_do_bom:
            d = abs(self.toques_certos[i] - tempo)
            if self.ja_julgados[i] is None and d < menor:
                melhor = i
                menor = d
            i += 1
        return melhor

    def marca_ponto(self, i, tipo, tempo, vai_mostrar=True):
        self.ja_julgados[i] = tipo
        pontos = 0
        if tipo == "perfeito":
            self.perfeitos += 1
            pontos = PONTOS_DO_PERFEITO
        elif tipo == "bom":
            self.bons += 1
            pontos = PONTOS_DO_BOM
        if tipo == "erro":
            self.erros += 1
            self.combo = 0
        else:
            self.pontos += pontos
            self.combo += 1
            self.maior_combo = max(self.maior_combo, self.combo)
        if vai_mostrar:
            self.ultimo = SeAcertou(tipo, tempo, pontos)

    def toca(self, tempo):
        i = self.qual_falta(tempo)
        if i is None:
            return None
        desvio = abs(tempo - self.toques_certos[i])
        if desvio > self.tempo_do_bom:
            return None
        tipo = "bom"
        if desvio <= self.tempo_do_perfeito:
            tipo = "perfeito"
        self.marca_ponto(i, tipo, tempo)
        return tipo

    def deu_erro(self, tempo):
        i = self.qual_falta(tempo)
        if i is not None:
            self.marca_ponto(i, "erro", tempo)

    def passou_da_hora(self, tempo):
        perdeu_agora = False
        while (self.cursor < len(self.toques_certos) and
               self.toques_certos[self.cursor] < tempo - self.tempo_do_bom):
            if self.ja_julgados[self.cursor] is None:
                self.marca_ponto(self.cursor, "erro", tempo)
                perdeu_agora = True
            self.cursor += 1
        return perdeu_agora

    def fecha_conta(self):
        for i in range(len(self.toques_certos)):
            if self.ja_julgados[i] is None:
                self.marca_ponto(i, "erro", 0.0, vai_mostrar=False)
        self.cursor = len(self.toques_certos)
