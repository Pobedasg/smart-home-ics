"""Випадкові ситуації: адаптована база не повинна давати суперечливих станів."""
import json
import random

from analysis import CHECKS, random_facts, violations
from engine import WorkingMemory, load_rules, run
from conftest import DATA


def count(rules_path, n=500, seed=1):
    rules = load_rules(rules_path)
    init = json.loads((DATA / "initial_state.json").read_text(encoding="utf-8"))
    rng = random.Random(seed)
    found = {c.code: 0 for c in CHECKS}
    for _ in range(n):
        wm = WorkingMemory()
        wm.load(init)
        wm.load(random_facts(rng))
        before = wm.snapshot()
        run(rules, wm)
        for c in violations(before, wm.snapshot()):
            found[c.code] += 1
    return found


def test_adapted_base_has_no_contradictions():
    found = count(DATA / "rules.json")
    assert sum(found.values()) == 0, found


def test_old_base_had_contradictions():
    found = count(DATA / "v1" / "rules.json")
    assert found["К1"] > 0 and found["К4"] > 0 and found["К5"] > 0


def test_check_counts_only_what_system_caused():
    k1 = next(c for c in CHECKS if c.code == "К1")
    state = {"Вікна.стан": "відкрито", "Кондиціонер.режим": "помірне_охолодження"}
    assert k1 in violations({"Вікна.стан": "відкрито", "Кондиціонер.режим": "вимкнено"}, state)
    assert k1 not in violations(state, state)      # так було ще до виведення
