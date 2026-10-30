"""Запуск тестових сценаріїв з очікуваними результатами (ПР4).

Тест – це ситуація (факти) і очікуваний стан після виведення.
Для чіткої системи очікування – значення факту, для нечіткої – значення
і що з ним робить система: «виконати» (CF ≥ 0.5), «запропонувати» або «без змін».
"""
import json
from pathlib import Path

from engine import WorkingMemory, load_rules, run as run_crisp
from fuzzy import FuzzyMemory, load_variables, run as run_fuzzy, ACT_THRESHOLD

DATA = Path(__file__).resolve().parent.parent / "data"
VERSIONS = {"v1": DATA / "v1", "v2": DATA}      # v1 – база до адаптації, v2 – після


def read(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def all_facts(test):
    return read("initial_state.json") + read("facts.json") + test["facts"]


def crisp_result(test, rules):
    wm = WorkingMemory()
    wm.load(all_facts(test))
    before = wm.snapshot()
    trace = run_crisp(rules, wm)
    return before, wm.snapshot(), [s.rule.id for s in trace]


def fuzzy_result(test, rules, variables):
    mem = FuzzyMemory()
    mem.load(all_facts(test))
    trace, _, concluded = run_fuzzy(rules, mem, variables)
    shown = {}
    for key in test["expect"]:
        if key in concluded:
            value, cf = concluded[key]
            shown[key] = f"{value}, {'виконати' if cf >= ACT_THRESHOLD else 'запропонувати'}"
            shown[key + " CF"] = cf
        else:
            shown[key] = "без змін"
    return shown, [s.rule.id for s in trace]


def load(version):
    folder = VERSIONS[version]
    return (load_rules(folder / "rules.json"), load_rules(folder / "rules_fuzzy.json"),
            load_variables(DATA / "fuzzy_vars.json"))


def check(test, version="v2", loaded=None):
    """Повертає (пройдено?, список розбіжностей, правила, що спрацювали)."""
    crisp_rules, fuzzy_rules, variables = loaded or load(version)
    if test["kind"] == "чітка":
        _, after, fired = crisp_result(test, crisp_rules)
        got = {k: after.get(k) for k in test["expect"]}
    else:
        got, fired = fuzzy_result(test, fuzzy_rules, variables)
    diff = []
    for key, want in test["expect"].items():
        if got.get(key) != want:
            cf = got.get(key + " CF")
            tail = f" (CF {cf:.2f})" if cf is not None else ""
            diff.append(f"{key}: очікувано «{want}», отримано «{got.get(key)}»{tail}")
    return not diff, diff, fired


def tests():
    return read("test_scenarios.json")
