import pytest

from fuzzy.certainty import AND, OR, NOT, combine, conclusion_cf


def test_logic():
    assert AND(0.3, 0.8, 1.0) == 0.3
    assert OR(0.3, 0.8) == 0.8
    assert NOT(0.6) == pytest.approx(0.4)


def test_conclusion_cf():
    assert conclusion_cf(0.83, 0.7) == pytest.approx(0.58, abs=0.01)


def test_combine_example_from_lr3():
    # R21 дає 0,23, прогноз через R25 – 0,49, разом 0,61
    assert combine(0.23, 0.49) == pytest.approx(0.61, abs=0.01)


@pytest.mark.parametrize("a, b", [(0.0, 0.5), (0.5, 0.5), (0.9, 0.9), (1.0, 0.3)])
def test_combine_grows_but_never_above_one(a, b):
    c = combine(a, b)
    assert max(a, b) <= c <= 1.0
    assert combine(a, b) == pytest.approx(combine(b, a))
