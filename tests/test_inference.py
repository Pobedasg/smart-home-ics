from conftest import make_rule
from engine import WorkingMemory, run


def facts(**kw):
    wm = WorkingMemory()
    for k, v in kw.items():
        wm.set(k.replace("__", "."), v)
    return wm


def test_higher_salience_fires_first():
    always = {"fact": "A.x", "op": "==", "value": 1}
    low = make_rule("LOW", always, [{"set": "B.y", "value": "low"}], salience=10, order=0)
    high = make_rule("HIGH", always, [{"set": "B.y", "value": "high"}], salience=90, order=1)
    trace = run([low, high], facts(A__x=1))
    assert [s.rule.id for s in trace] == ["HIGH", "LOW"]


def test_same_salience_keeps_file_order():
    always = {"fact": "A.x", "op": "==", "value": 1}
    r1 = make_rule("R1", always, [{"set": "B.y", "value": 1}], salience=50, order=0)
    r2 = make_rule("R2", always, [{"set": "B.z", "value": 2}], salience=50, order=1)
    assert [s.rule.id for s in run([r2, r1], facts(A__x=1))] == ["R1", "R2"]


def test_refraction_prevents_endless_loop():
    # правило перемикає стан туди-сюди; без рефракції система б зациклилась
    toggle = make_rule("T", {"fact": "A.x", "op": "in", "value": [0, 1]},
                       [{"set": "A.x", "value": 1}])
    trace = run([toggle], facts(A__x=0))
    assert len(trace) == 1


def test_chain_of_rules():
    first = make_rule("R8", {"fact": "Середовище.обстріл", "op": "==", "value": "так"},
                      [{"set": "Режим.криза", "value": "так"}], salience=100, order=0)
    second = make_rule("R9", {"fact": "Режим.криза", "op": "==", "value": "так"},
                       [{"set": "Режим.назва", "value": "ізольований"}], salience=100, order=1)
    wm = facts(Середовище__обстріл="так", Режим__криза="ні")
    trace = run([second, first], wm)
    assert [s.rule.id for s in trace] == ["R8", "R9"]
    assert wm.get("Режим.назва") == "ізольований"


def test_stops_when_nothing_matches():
    rule = make_rule("R", {"fact": "A.x", "op": "==", "value": 5}, [{"set": "B.y", "value": 1}])
    assert run([rule], facts(A__x=1)) == []


def test_real_base_shelling(rules):
    wm = WorkingMemory()
    wm.load([{"object": "Середовище", "attribute": "обстріл", "value": "так"},
             {"object": "Середовище", "attribute": "індекс_забруднення", "value": 40},
             {"object": "Живлення", "attribute": "джерело", "value": "мережа"},
             {"object": "Режим", "attribute": "криза", "value": "ні"},
             {"object": "Картка", "attribute": "вставлена", "value": "так"},
             {"object": "Кімната", "attribute": "рівень_CO2", "value": 1300}])
    fired = [s.rule.id for s in run(rules, wm)]
    assert fired[:1] == ["R1"]
    assert {"R6", "R7", "R8", "R9"} <= set(fired)
    assert "R18" not in fired          # під час кризи вікна не відкриваються
    assert wm.get("Вікна.стан") == "закрито_ізоляція"
