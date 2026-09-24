"""Recordes das fases, num JSON simples ao lado do jogo."""

import json
import os

from .config import ARQUIVO_SAVE

VERSAO = 1   # sobe quando o formato muda; um save de versao anterior e descartado

VAZIO = {"melhor": 0.0, "completou": False, "pontos": 0, "nota": "-",
         "precisao": 0.0}
ORDEM_NOTAS = {"-": 0, "C": 1, "B": 2, "A": 3, "S": 4}


class Save:
    def __init__(self):
        self.recordes = {}
        self.carregar()

    def carregar(self):
        try:
            with open(ARQUIVO_SAVE, "r", encoding="utf-8") as f:
                dados = json.load(f)
        except (OSError, ValueError):
            return
        if dados.get("versao") == VERSAO and isinstance(dados.get("recordes"), dict):
            self.recordes = dados["recordes"]

    def salvar(self):
        try:
            tmp = ARQUIVO_SAVE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"versao": VERSAO, "recordes": self.recordes}, f, indent=1)
            os.replace(tmp, ARQUIVO_SAVE)
        except OSError as erro:
            print(f"[save] nao foi possivel gravar: {erro}")

    def recorde(self, fase_id):
        r = self.recordes.setdefault(str(fase_id), dict(VAZIO))
        for k, v in VAZIO.items():
            r.setdefault(k, v)
        return r

    def registrar(self, fase_id, pct, completou, pontos, nota, precisao):
        """Guarda o melhor de cada campo (nunca piora um recorde)."""
        r = self.recorde(fase_id)
        r["melhor"] = max(r["melhor"], round(pct, 2))
        if pontos > r["pontos"]:
            r["pontos"] = int(pontos)
            r["precisao"] = round(precisao, 4)
        if ORDEM_NOTAS.get(nota, 0) > ORDEM_NOTAS.get(r["nota"], 0):
            r["nota"] = nota
        r["completou"] = r["completou"] or completou
        self.salvar()
        return r

    def progresso(self, total):
        """(fases completas, soma dos pontos) das `total` fases."""
        completas = pontos = 0
        for i in range(total):
            r = self.recordes.get(str(i))
            if r:
                completas += bool(r.get("completou"))
                pontos += int(r.get("pontos", 0))
        return completas, pontos


save = Save()
