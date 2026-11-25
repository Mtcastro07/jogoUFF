from PPlay.object_group import ObjectGroup


class Monte(ObjectGroup):
    def __init__(self, *objetos):
        super().__init__()
        self.add(*objetos)

    def __iter__(self):
        return iter(self.get_all())

    def __getitem__(self, i):
        return self.get_all()[i]

    def ordena(self, chave):
        self.get_all().sort(key=chave)


class PorColuna:
    VAZIA = Monte()

    def __init__(self):
        self.monte_por_coluna = {}

    def add(self, obj, n_colunas):
        for tx in n_colunas:
            self.monte_por_coluna.setdefault(tx, Monte()).add(obj)

    def remove(self, obj):
        for grupo in self.monte_por_coluna.values():
            grupo.remove(obj)

    def em(self, tx):
        return self.monte_por_coluna.get(tx, self.VAZIA)

    def __iter__(self):
        return iter(self.monte_por_coluna)
