"""Робоча пам'ять: поточні факти у вигляді «об'єкт.атрибут -> значення»."""


class WorkingMemory:
    def __init__(self):
        self.facts = {}

    @staticmethod
    def key(obj, attr):
        return f"{obj}.{attr}"

    def load(self, triples):
        """Завантажує список фактів формату {"object", "attribute", "value"}."""
        for t in triples:
            self.facts[self.key(t["object"], t["attribute"])] = t["value"]

    def get(self, key, default=None):
        return self.facts.get(key, default)

    def has(self, key):
        return key in self.facts

    def set(self, key, value):
        """Записує факт. Повертає (старе значення, змінилось чи ні)."""
        old = self.facts.get(key)
        self.facts[key] = value
        return old, old != value

    def snapshot(self):
        return dict(self.facts)
