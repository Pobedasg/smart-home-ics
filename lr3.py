"""ЛР3: гібридна ІКС – правила з невизначеністю (ЛР2) + ML-сервіс через REST API.

Спершу запустіть сервіс в окремому терміналі:
  python3 ml_service/app.py

Потім:
  python3 lr3.py              – усі сценарії з data/scenarios_ml.json
  python3 lr3.py -s 1         – один сценарій
  python3 lr3.py --url http://127.0.0.1:8000   – інша адреса сервісу
Якщо сервіс не запущено, система попередить і працюватиме лише на правилах.
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from engine import load_rules
from fuzzy import FuzzyMemory, load_variables, run, ACT_THRESHOLD
from hybrid import DEFAULT_URL, features_from, predict_overheat, prediction_fact
from lr2 import OUTPUTS, read_json, scenario_facts
from ics_logging import setup_logging

DATA = Path(__file__).parent / "data"


def load_all_rules():
    rules = load_rules(DATA / "rules_fuzzy.json")        # R1–R24 з ЛР2
    extra = load_rules(DATA / "rules_ml.json")           # R25, що використовує прогноз
    for r in extra:
        r.order += len(rules)
    return rules + extra


def decide(facts, rules, variables):
    mem = FuzzyMemory()
    mem.load(facts)
    trace, weak, concluded = run(rules, mem, variables)
    return trace, weak, concluded


def verdict(concluded, key):
    if key not in concluded:
        return "без змін"
    value, cf = concluded[key]
    how = "виконати" if cf >= ACT_THRESHOLD else "запропонувати"
    return f"{value}, CF {cf:.2f} → {how}"


def show(title, facts, rules, variables, url):
    line = "═" * 72
    print(f"\n{line}\n {title}\n{line}")
    logging.getLogger("ics").info("=== %s", title)

    mem = FuzzyMemory()
    mem.load(facts)
    features = features_from(mem)
    print("1) Запит до ML-сервісу:")
    if features is None:
        p, err = None, "у фактах немає ознак для моделі"
    else:
        print(f"   POST {url}/predict {json.dumps(features, ensure_ascii=False)}")
        p, err = predict_overheat(features, url)
    if p is None:
        print(f"   ⚠ {err}. Рішення приймається лише за правилами.")
        hybrid_facts = facts
    else:
        print(f"   відповідь: ймовірність перегріву за 30 хв = {p:.2f}")
        fact = prediction_fact(p)
        print(f"   → новий факт {fact['object']}.{fact['attribute']} = {fact['value']} (CF {fact['cf']:.2f})")
        hybrid_facts = facts + [fact]

    trace, weak, concluded = decide(hybrid_facts, rules, variables)
    print("\n2) Хід виведення (правила + прогноз):")
    for st in trace:
        print(f"   Цикл {st.cycle}. {st.rule.id} «{st.rule.name}»: "
              f"ступінь {st.premise:.2f} × вага {st.rule.weight} = CF {st.cf:.2f}")
        for key, old, new, cf, note in st.changes:
            tail = f"  [{note}]" if note else ""
            print(f"       {key}: {'—' if old is None else old} → {new} (CF {cf:.2f}){tail}")
    if weak:
        print("   Не пройшли поріг: " + ", ".join(f"{r.id} (CF {cf:.2f})" for r, _, cf in weak))

    _, _, rules_only = decide(facts, [r for r in rules if r.id != "R25"], variables)
    print("\n3) Єдиний висновок:")
    print(f"   {'':26} {'лише правила':38} правила + ML")
    for k in OUTPUTS:
        if k in concluded or k in rules_only:
            print(f"   {k:26} {verdict(rules_only, k):38} {verdict(concluded, k)}")
    return concluded, rules_only


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Гібридна ІКС: правила + ML через REST API (ЛР3)")
    p.add_argument("-s", "--scenario", type=int, help="номер сценарію (з 1)")
    p.add_argument("--url", default=DEFAULT_URL, help=f"адреса ML-сервісу (за замовчуванням {DEFAULT_URL})")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING"],
                   help="докладність журналу logs/ics.log")
    args = p.parse_args()
    setup_logging(args.log_level)

    rules = load_all_rules()
    variables = load_variables(DATA / "fuzzy_vars.json")
    print(f"Завантажено правил: {len(rules)} (R1–R24, R26–R28 з ПР4 + R25 для прогнозу), ML-сервіс: {args.url}")

    scenarios = read_json("scenarios_ml.json")
    if args.scenario is not None and not 1 <= args.scenario <= len(scenarios):
        p.error(f"немає сценарію {args.scenario}, доступні 1–{len(scenarios)}")
    idx = [args.scenario] if args.scenario is not None else range(1, len(scenarios) + 1)
    for i in idx:
        sc = scenarios[i - 1]
        show(f"Сценарій {i}: {sc['name']}", scenario_facts(sc), rules, variables, args.url)


if __name__ == "__main__":
    main()
