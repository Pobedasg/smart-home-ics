"""Спільні налаштування тестів: шлях до проєкту і готові об'єкти."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import load_rules                    # noqa: E402
from fuzzy import load_variables                 # noqa: E402

DATA = ROOT / "data"


@pytest.fixture(scope="session")
def rules():
    return load_rules(DATA / "rules.json")


@pytest.fixture(scope="session")
def fuzzy_rules():
    return load_rules(DATA / "rules_fuzzy.json")


@pytest.fixture(scope="session")
def variables():
    return load_variables(DATA / "fuzzy_vars.json")


def make_rule(rid, cond, then, salience=0, weight=1.0, order=0):
    """Невелике правило для тестів."""
    from engine import Rule
    return Rule({"id": rid, "name": rid, "salience": salience, "weight": weight,
                 "if": cond, "then": then}, order)
