import json
import os

from .config import ONDE_SALVA

VERSAO = 2
VAZIO = {"melhor": 0.0, "completou": False, "pontos": 0, "nota": "-",
         "precisao": 0.0, "ecos": 0}
ORDEM_DAS_NOTAS = ["-", "C", "B", "A", "S"]


def valor_presta(nome, valor):
    if nome not in VAZIO:
        return False
    if nome == "nota":
        return valor in ORDEM_DAS_NOTAS
    if nome == "completou":
        return type(valor) is bool
    return type(valor) in (int, float)


class Salvo:
    def __init__(self):
        self.recordes = {}
        self.opcoes = {"musica": 10, "sfx": 10, "atraso": 0}
        self.final_visto = False
        self.carrega_save()

    def carrega_save(self):
        try:
            with open(ONDE_SALVA, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if dados["versao"] == VERSAO:
                self.pega_opcoes(dados["opcoes"])
                self.pega_recordes(dados["recordes"])
                self.final_visto = bool(dados["final_visto"])
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            pass

    def pega_opcoes(self, opcoes):
        for nome, valor in opcoes.items():
            if nome in self.opcoes and type(valor) is int:
                self.opcoes[nome] = max(0, min(10, valor))

    def pega_recordes(self, recordes):
        for mundo, r in recordes.items():
            if type(r) is dict:
                self.recordes[mundo] = {k: v for k, v in r.items() if valor_presta(k, v)}

    def salva(self):
        dados = {"versao": VERSAO, "recordes": self.recordes,
                 "opcoes": self.opcoes, "final_visto": self.final_visto}
        try:
            with open(ONDE_SALVA + ".tmp", "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=1)
            os.replace(ONDE_SALVA + ".tmp", ONDE_SALVA)
        except OSError as erro:
            print(f"[save] nao foi possivel gravar: {erro}")

    def recorde(self, mundo):
        if mundo not in self.recordes:
            self.recordes[mundo] = dict(VAZIO)
        r = self.recordes[mundo]
        for k in VAZIO:
            if k not in r:
                r[k] = VAZIO[k]
        return r

    def anota(self, mundo, porcento, completou, pontos, nota, precisao, ecos):
        r = self.recorde(mundo)
        r["melhor"] = max(r["melhor"], round(porcento, 2))
        if pontos > r["pontos"]:
            r["pontos"] = pontos
            r["precisao"] = round(precisao, 4)
        if ORDEM_DAS_NOTAS.index(nota) > ORDEM_DAS_NOTAS.index(r["nota"]):
            r["nota"] = nota
        if completou:
            r["completou"] = True
        r["ecos"] = max(r["ecos"], ecos)
        self.salva()

    def progresso(self, os_mundos):
        quantas_completas = 0
        pontos = 0
        for mundo in os_mundos:
            if mundo in self.recordes:
                r = self.recorde(mundo)
                if r["completou"]:
                    quantas_completas += 1
                pontos += r["pontos"]
        return quantas_completas, pontos


save = Salvo()
