import pytest

from conftest import make_rule
from fuzzy import FuzzyMemory, run, degree


def mem(*facts):
    m = FuzzyMemory()
    m.load([{"object": o, "attribute": a, "value": v, "cf": cf} for o, a, v, cf in facts])
    return m


def test_boolean_fact_with_low_cf_means_no(variables):
    m = mem(("Середовище", "обстріл", "так", 0.6))
    assert degree({"fact": "Середовище.обстріл", "op": "==", "value": "так"}, m, variables) == 0.6
    assert degree({"fact": "Середовище.обстріл", "op": "==", "value": "ні"}, m, variables) == pytest.approx(0.4)


def test_fuzzy_condition_uses_membership_and_cf(variables):
    m = mem(("Кімната", "температура", 25.5, 1.0))
    assert degree({"fact": "Кімната.температура", "is": "тепло"}, m, variables) == pytest.approx(0.83, abs=0.01)
    m = mem(("Кімната", "температура", 25.5, 0.5))
    assert degree({"fact": "Кімната.температура", "is": "тепло"}, m, variables) == pytest.approx(0.42, abs=0.01)


def test_rule_below_threshold_does_not_fire(variables):
    weak = make_rule("W", {"fact": "A.x", "op": "==", "value": "так"},
                     [{"set": "B.y", "value": 1}], weight=0.5)
    trace, _, concluded = run([weak], mem(("A", "x", "так", 0.3)), variables)   # 0,3 × 0,5 = 0,15
    assert trace == [] and concluded == {}


def test_same_conclusion_is_strengthened(variables):
    r1 = make_rule("R1", {"fact": "A.x", "op": "==", "value": "так"}, [{"set": "K.m", "value": "on"}], weight=0.5, order=0)
    r2 = make_rule("R2", {"fact": "A.x", "op": "==", "value": "так"}, [{"set": "K.m", "value": "on"}], weight=0.5, order=1)
    _, _, concluded = run([r1, r2], mem(("A", "x", "так", 1.0)), variables)
    assert concluded["K.m"] == ("on", 0.75)


def test_conflict_keeps_stronger_conclusion(variables):
    weak = make_rule("A", {"fact": "A.x", "op": "==", "value": "так"}, [{"set": "W.s", "value": "відкрито"}],
                     weight=0.6, salience=10, order=0)
    strong = make_rule("B", {"fact": "A.x", "op": "==", "value": "так"}, [{"set": "W.s", "value": "закрито"}],
                       weight=0.9, salience=90, order=1)
    _, _, concluded = run([weak, strong], mem(("A", "x", "так", 1.0)), variables)
    assert concluded["W.s"] == ("закрито", 0.9)
