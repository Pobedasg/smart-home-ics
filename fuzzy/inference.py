"""Виведення з невизначеністю.

Відмінності від чіткого механізму з ЛР1:
  * умова «температура is спекотно» дає не так/ні, а ступінь від 0 до 1;
  * факт може бути невпевненим (наприклад, тривога з CF 0.6);
  * І = мінімум, АБО = максимум; CF висновку = ступінь умови × вага правила;
  * правило спрацьовує, лише якщо CF висновку не менший за поріг 0.2;
  * висновок з CF від 0.5 виконується автоматично, слабший – пропонується користувачу;
  * однакові висновки від різних правил підсилюють один одного (combine),
    а суперечливі (вікна відкрити / закрити) – перемагає більший CF.
"""
from dataclasses import dataclass, field

from engine.rules import OPERATORS
from .certainty import AND, OR, NOT, conclusion_cf, combine

THRESHOLD = 0.2         # нижче – правило не спрацьовує
ACT_THRESHOLD = 0.5     # від цього CF система діє сама, нижче – лише пропонує
BOOL = ("так", "ні")


def degree(cond, mem, variables):
    """Ступінь виконання умови від 0 до 1."""
    if "all" in cond:
        return AND(*(degree(c, mem, variables) for c in cond["all"]))
    if "any" in cond:
        return OR(*(degree(c, mem, variables) for c in cond["any"]))
    key = cond["fact"]
    if not mem.has(key):
        return 0.0
    value, cf = mem.value(key), mem.cf(key)
    if "is" in cond:                                   # нечітка умова
        return variables[key].mu(cond["is"], value) * cf
    target = cond["value"]
    if cond["op"] == "==" and value in BOOL and target in BOOL:
        # «так» з CF 0.6 означає «ні» з впевненістю 0.4
        return cf if value == target else NOT(cf)
    try:
        return cf if OPERATORS[cond["op"]](value, target) else 0.0
    except TypeError:
        return 0.0


@dataclass
class Step:
    cycle: int
    rule: object
    premise: float
    cf: float
    changes: list = field(default_factory=list)   # (ключ, старе, нове, cf, статус)


def run(rules, mem, variables, threshold=THRESHOLD, max_cycles=50):
    fired, trace = set(), []
    concluded = {}            # ключ -> (значення, cf), висновки цього запуску
    for cycle in range(1, max_cycles + 1):
        agenda = []
        for r in rules:
            if r.id in fired:
                continue
            p = degree(r.condition, mem, variables)
            if conclusion_cf(p, r.weight) >= threshold:
                agenda.append((r, p))
        if not agenda:
            break
        agenda.sort(key=lambda x: (-x[0].salience, x[0].order))
        rule, p = agenda[0]
        cf = round(conclusion_cf(p, rule.weight), 2)
        step = Step(cycle, rule, round(p, 2), cf)
        for act in rule.actions:
            if "if" in act and degree(act["if"], mem, variables) < 0.5:
                continue
            key, new = act["set"], act["value"]
            old = mem.value(key)
            if key in concluded:
                prev_val, prev_cf = concluded[key]
                if prev_val == new:
                    total = round(combine(prev_cf, cf), 2)
                    concluded[key] = (new, total)
                    mem.set(key, new, total)
                    step.changes.append((key, old, new, total, f"підсилено {prev_cf} → {total}"))
                elif cf > prev_cf:
                    concluded[key] = (new, cf)
                    mem.set(key, new, cf)
                    step.changes.append((key, old, new, cf, f"переважило {prev_val} (CF {prev_cf})"))
                else:
                    step.changes.append((key, old, new, cf, f"відкинуто: вже є {prev_val} (CF {prev_cf})"))
            else:
                concluded[key] = (new, cf)
                mem.set(key, new, cf)
                step.changes.append((key, old, new, cf, ""))
        fired.add(rule.id)
        trace.append(step)

    weak = []                 # правила, які «майже» спрацювали
    for r in rules:
        if r.id not in fired:
            p = degree(r.condition, mem, variables)
            if p > 0:
                weak.append((r, round(p, 2), round(conclusion_cf(p, r.weight), 2)))
    return trace, weak, concluded
