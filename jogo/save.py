"""Recordes das fases, num JSON simples ao lado do jogo."""

import json
import os

from .config import ARQUIVO_SAVE

VERSAO = 2   # sobe quando o formato muda
# Ate a versao 1 o recorde era guardado pela POSICAO da fase na lista (0, 1, 2).
# Com fases novas entrando no meio da ordem, a chave passou a ser o nome do
# mundo: um save antigo e convertido ao abrir, e nenhum recorde muda de dono.
MUNDOS_V1 = {"0": "bosque", "1": "ilhas", "2": "eclipse"}

VAZIO = {"melhor": 0.0, "completou": False, "pontos": 0, "nota": "-",
         "precisao": 0.0, "ecos": 0}
OPCOES = {"musica": 10, "sfx": 10, "atraso": 0}     # so "musica" (0 a 10) ainda e usada
ORDEM_NOTAS = {"-": 0, "C": 1, "B": 2, "A": 3, "S": 4}


class Save:
    def __init__(self):
        self.recordes = {}
        self.opcoes = dict(OPCOES)
        self.final_visto = False      # o final (jogo/final.py) ja tocou uma vez?
        self.carregar()

    def carregar(self):
        try:
            with open(ARQUIVO_SAVE, "r", encoding="utf-8") as f:
                dados = json.load(f)
        except (OSError, ValueError):
            return
        if dados.get("versao") in (1, VERSAO) and isinstance(dados.get("recordes"), dict):
            self.recordes = dados["recordes"]
            if dados["versao"] == 1:
                self.recordes = {MUNDOS_V1[k]: v for k, v in self.recordes.items()
                                 if k in MUNDOS_V1}
            if isinstance(dados.get("opcoes"), dict):
                for k in OPCOES:
                    if isinstance(dados["opcoes"].get(k), int):
                        self.opcoes[k] = dados["opcoes"][k]
            self.final_visto = dados.get("final_visto") is True

    def salvar(self):
        try:
            tmp = ARQUIVO_SAVE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"versao": VERSAO, "recordes": self.recordes,
                           "opcoes": self.opcoes,
                           "final_visto": self.final_visto}, f, indent=1)
            os.replace(tmp, ARQUIVO_SAVE)
        except OSError as erro:
            print(f"[save] nao foi possivel gravar: {erro}")

    def recorde(self, mundo):
        """O recorde da fase do mundo `mundo` (fase.cancao)."""
        r = self.recordes.setdefault(str(mundo), dict(VAZIO))
        for k, v in VAZIO.items():
            r.setdefault(k, v)
        return r

    def registrar(self, mundo, pct, completou, pontos, nota, precisao, ecos=0):
        """Guarda o melhor de cada campo (nunca piora um recorde)."""
        r = self.recorde(mundo)
        r["melhor"] = max(r["melhor"], round(pct, 2))
        if pontos > r["pontos"]:
            r["pontos"] = int(pontos)
            r["precisao"] = round(precisao, 4)
        if ORDEM_NOTAS.get(nota, 0) > ORDEM_NOTAS.get(r["nota"], 0):
            r["nota"] = nota
        r["completou"] = r["completou"] or completou
        r["ecos"] = max(r["ecos"], int(ecos))
        self.salvar()
        return r

    def progresso(self, mundos):
        """(fases completas, soma dos pontos) das fases dos `mundos`."""
        completas = pontos = 0
        for mundo in mundos:
            r = self.recordes.get(mundo)
            if r:
                completas += bool(r.get("completou"))
                pontos += int(r.get("pontos", 0))
        return completas, pontos


save = Save()
