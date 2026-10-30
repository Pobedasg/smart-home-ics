import pytest

from conftest import make_rule
from engine import WorkingMemory
from engine.rules import check, describe


@pytest.fixture
def wm():
    m = WorkingMemory()
    m.load([{"object": "Кімната", "attribute": "температура", "value": 28},
            {"object": "Середовище", "attribute": "опади", "value": "дощ"},
            {"object": "Мешканці", "attribute": "є_люди", "value": "так"}])
    return m


@pytest.mark.parametrize("op, value, expected", [
    (">", 26, True), (">", 30, False), ("<", 30, True), (">=", 28, True),
    ("<=", 27, False), ("==", 28, True), ("!=", 28, False),
])
def test_comparison_operators(wm, op, value, expected):
    assert check({"fact": "Кімната.температура", "op": op, "value": value}, wm) is expected


def test_in_operator(wm):
    assert check({"fact": "Середовище.опади", "op": "in", "value": ["дощ", "сніг"]}, wm)
    assert not check({"fact": "Середовище.опади", "op": "in", "value": ["сніг"]}, wm)


def test_all_and_any(wm):
    hot = {"fact": "Кімната.температура", "op": ">", "value": 26}
    snow = {"fact": "Середовище.опади", "op": "==", "value": "сніг"}
    assert not check({"all": [hot, snow]}, wm)
    assert check({"any": [hot, snow]}, wm)
    assert check({"all": [hot, {"any": [snow, {"fact": "Мешканці.є_люди", "op": "==", "value": "так"}]}]}, wm)


def test_unknown_fact_is_false(wm):
    assert not check({"fact": "Кімната.рівень_CO2", "op": ">", "value": 1000}, wm)


def test_type_mismatch_does_not_crash(wm):
    assert not check({"fact": "Середовище.опади", "op": ">", "value": 5}, wm)


def test_fire_changes_facts_and_reports_changes(wm):
    rule = make_rule("X", {"fact": "Кімната.температура", "op": ">", "value": 26},
                     [{"set": "Кондиціонер.режим", "value": "охолодження"}])
    assert rule.matches(wm)
    assert rule.fire(wm) == [("Кондиціонер.режим", None, "охолодження")]
    assert rule.fire(wm) == []          # значення вже таке, змін немає


def test_explanation_of_failed_rule(wm):
    rule = make_rule("X", {"fact": "Кімната.температура", "op": "<", "value": 18},
                     [{"set": "Обігрівач.стан", "value": "увімкнено"}])
    assert rule.failed(wm) == ["потрібно Кімната.температура < 18, а є 28"]
    assert describe({"fact": "A.b", "op": "in", "value": ["x", "y"]}) == "A.b ∈ x / y"
