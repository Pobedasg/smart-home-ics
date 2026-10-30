from engine import WorkingMemory


def test_load_and_get():
    wm = WorkingMemory()
    wm.load([{"object": "Кімната", "attribute": "температура", "value": 28}])
    assert wm.has("Кімната.температура")
    assert wm.get("Кімната.температура") == 28
    assert wm.get("Кімната.вологість", "немає") == "немає"


def test_set_returns_old_value_and_change_flag():
    wm = WorkingMemory()
    assert wm.set("Вікна.стан", "закрито") == (None, True)
    assert wm.set("Вікна.стан", "відкрито") == ("закрито", True)
    assert wm.set("Вікна.стан", "відкрито") == ("відкрито", False)


def test_snapshot_is_a_copy():
    wm = WorkingMemory()
    wm.set("Режим.назва", "комфортний")
    snap = wm.snapshot()
    wm.set("Режим.назва", "сон")
    assert snap["Режим.назва"] == "комфортний"
