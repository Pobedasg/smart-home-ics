"""Робоча пам'ять з невизначеністю: кожен факт має значення і впевненість CF."""


class FuzzyMemory:
    def __init__(self):
        self.facts = {}           # "Об'єкт.атрибут" -> (значення, cf)

    def load(self, triples):
        for t in triples:
            key = f"{t['object']}.{t['attribute']}"
            self.facts[key] = (t["value"], t.get("cf", 1.0))

    def has(self, key):
        return key in self.facts

    def value(self, key, default=None):
        return self.facts.get(key, (default, 0))[0]

    def cf(self, key):
        return self.facts.get(key, (None, 0))[1]

    def set(self, key, value, cf):
        self.facts[key] = (value, cf)

    def snapshot(self):
        return dict(self.facts)
