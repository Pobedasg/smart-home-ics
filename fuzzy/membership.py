"""Нечіткі (лінгвістичні) змінні та функції належності."""
import json


def trapezoid(x, a, b, c, d):
    """Трапецієподібна функція належності. Трикутна – це випадок b == c.
    Якщо a == b (або c == d), терм крайній: усе, що лежить за межею
    діапазону, теж належить йому повністю (36 °C – це теж «спекотно»)."""
    if b <= x <= c:
        return 1.0
    if x < b:
        if a == b:
            return 1.0
        return 0.0 if x <= a else (x - a) / (b - a)
    if c == d:
        return 1.0
    return 0.0 if x >= d else (d - x) / (d - c)


class LinguisticVariable:
    def __init__(self, name, unit, terms, value_range):
        self.name = name
        self.unit = unit
        self.terms = terms            # {"спекотно": [a, b, c, d], ...}
        self.range = value_range

    def mu(self, term, x):
        """Ступінь належності значення x до терму (від 0 до 1)."""
        return trapezoid(x, *self.terms[term])

    def fuzzify(self, x):
        """Ступені належності x до всіх термів змінної."""
        return {t: round(self.mu(t, x), 2) for t in self.terms}


def load_variables(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {name: LinguisticVariable(name, v["unit"], v["terms"], v["range"])
            for name, v in data.items()}
