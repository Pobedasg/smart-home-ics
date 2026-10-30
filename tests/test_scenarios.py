"""Тестові сценарії з ПР4: адаптована база (v2) має проходити всі,
а стара (v1) – падати саме на тих, де ми знайшли помилки."""
import pytest

from analysis.suite import check, load
from analysis.suite import tests as all_tests

TESTS = all_tests()
V1_FAILS = {"T4", "T5", "T6", "T7", "T8", "F2", "F5"}


@pytest.fixture(scope="module")
def loaded():
    return {"v1": load("v1"), "v2": load("v2")}


@pytest.mark.parametrize("test", TESTS, ids=[t["id"] for t in TESTS])
def test_adapted_base_passes(test, loaded):
    ok, diff, _ = check(test, "v2", loaded["v2"])
    assert ok, "\n".join(diff)


@pytest.mark.parametrize("test", TESTS, ids=[t["id"] for t in TESTS])
def test_old_base_fails_where_expected(test, loaded):
    ok, _, _ = check(test, "v1", loaded["v1"])
    assert ok == (test["id"] not in V1_FAILS)
