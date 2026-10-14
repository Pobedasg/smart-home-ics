"""Продукційні правила «ЯКЩО – ТО»: завантаження з JSON і перевірка умов."""
import json

OPERATORS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "in": lambda a, b: a in b,
}


def check(cond, wm):
    """Перевіряє умову. Умова – це атом {"fact", "op", "value"}
    або група {"all": [...]} (І) чи {"any": [...]} (АБО)."""
    if "all" in cond:
        return all(check(c, wm) for c in cond["all"])
    if "any" in cond:
        return any(check(c, wm) for c in cond["any"])
    if not wm.has(cond["fact"]):
        return False          # невідомий факт – умова не виконується
    try:
        return OPERATORS[cond["op"]](wm.get(cond["fact"]), cond["value"])
    except TypeError:         # наприклад, порівняння числа з рядком
        return False


def atoms(cond):
    """Усі атомарні умови всередині складної умови."""
    if "all" in cond:
        return [a for c in cond["all"] for a in atoms(c)]
    if "any" in cond:
        return [a for c in cond["any"] for a in atoms(c)]
    return [cond]


def describe(cond):
    value = cond["value"]
    if isinstance(value, list):
        value = " / ".join(map(str, value))
    op = "∈" if cond["op"] == "in" else cond["op"].replace("==", "=")
    return f"{cond['fact']} {op} {value}"


class Rule:
    def __init__(self, data, order):
        self.id = data["id"]
        self.name = data["name"]
        self.salience = data.get("salience", 0)
        self.weight = data.get("weight", 1.0)
        self.condition = data["if"]
        self.actions = data["then"]
        self.order = order    # порядок у файлі, якщо пріоритети однакові

    def matches(self, wm):
        return check(self.condition, wm)

    def reasons(self, wm):
        """Факти, через які правило спрацювало (виконані атомарні умови)."""
        return [f"{a['fact']} = {wm.get(a['fact'])}"
                for a in atoms(self.condition) if check(a, wm)]

    def failed(self, wm):
        """Умови, які не виконались (для пояснення, чому правило мовчить)."""
        out = []
        for a in atoms(self.condition):
            if not check(a, wm):
                out.append(f"потрібно {describe(a)}, а є {wm.get(a['fact'], 'невідомо')}")
        return out

    def fire(self, wm):
        """Виконує праву частину правила. Повертає список змін."""
        changes = []
        for act in self.actions:
            if "if" in act and not check(act["if"], wm):
                continue
            old, changed = wm.set(act["set"], act["value"])
            if changed:
                changes.append((act["set"], old, act["value"]))
        return changes

    def __repr__(self):
        return f"{self.id}({self.salience})"


def load_rules(path):
    with open(path, encoding="utf-8") as f:
        return [Rule(d, i) for i, d in enumerate(json.load(f))]
