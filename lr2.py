"""ЛР2: експертна система з обробкою невизначеності.

Запуск:
  python lr2.py                    – усі сценарії з data/scenarios_fuzzy.json
  python lr2.py -s 3               – один сценарій
  python lr2.py -s 3 --compare     – плюс результат чіткої системи з ЛР1
  python lr2.py -f my.json         – власний файл фактів
"""
import argparse
import json
import sys
from pathlib import Path

from engine import WorkingMemory, load_rules
from engine import run as run_crisp
from fuzzy import FuzzyMemory, load_variables, run, THRESHOLD, ACT_THRESHOLD

DATA = Path(__file__).parent / "data"
OUTPUTS = ["Режим.назва", "Режим.криза", "Вікна.стан", "Кондиціонер.режим",
           "Обігрівач.стан", "Очищувач.режим", "Тепла_підлога.потужність", "Поїлка.стан"]


def read_json(name):
    path = Path(name) if Path(name).exists() else DATA / name
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def scenario_facts(sc):
    return (read_json("initial_state.json")
            + read_json(sc.get("facts_file") or sc.get("base", "facts.json"))
            + sc.get("facts", []))


def crisp_result(facts):
    """Що вирішила б чітка система з ЛР1 на тих самих даних (без CF)."""
    wm = WorkingMemory()
    wm.load(facts)
    trace = run_crisp(load_rules(DATA / "rules.json"), wm)
    return wm, [s.rule.id for s in trace]


def show(title, facts, rules, variables, compare=False):
    line = "═" * 72
    print(f"\n{line}\n {title}\n{line}")
    mem = FuzzyMemory()
    mem.load(facts)

    print("Фазифікація вхідних даних:")
    for key, var in variables.items():
        if mem.has(key):
            x = mem.value(key)
            terms = " | ".join(f"{t} {d:.2f}" for t, d in var.fuzzify(x).items())
            print(f"  {key} = {x} {var.unit}\n      → {terms}")
    uncertain = [(k, v, c) for k, (v, c) in mem.snapshot().items() if c < 1]
    if uncertain:
        print("Невпевнені факти:")
        for k, v, c in uncertain:
            print(f"  {k} = {v} (CF {c})")

    trace, weak, concluded = run(rules, mem, variables)

    print(f"\nХід виведення (поріг спрацювання CF ≥ {THRESHOLD}):")
    if not trace:
        print("  жодне правило не пройшло поріг")
    for st in trace:
        print(f"  Цикл {st.cycle}. {st.rule.id} «{st.rule.name}»: "
              f"ступінь умови {st.premise:.2f} × вага {st.rule.weight} = CF {st.cf:.2f}")
        for key, old, new, cf, note in st.changes:
            tail = f"  [{note}]" if note else ""
            print(f"      {key}: {old} → {new} (CF {cf:.2f}){tail}")
    if weak:
        print("Не пройшли поріг: " + ", ".join(f"{r.id} (CF {cf:.2f})" for r, p, cf in weak))

    print(f"\nВисновок (CF ≥ {ACT_THRESHOLD} – система діє сама):")
    for k in OUTPUTS:
        if k in concluded:
            v, cf = concluded[k]
            how = "виконати" if cf >= ACT_THRESHOLD else "запропонувати користувачу"
            print(f"  {k:26} {v:20} CF {cf:.2f}  → {how}")
    if not concluded:
        print("  змін немає, пристрої лишаються в поточному стані")

    if compare:
        wm, fired = crisp_result(facts)
        print(f"\nДля порівняння, чітка система ЛР1 (правила {', '.join(fired) or '—'}):")
        start = {f"{t['object']}.{t['attribute']}": t["value"] for t in facts}
        changed = [k for k in OUTPUTS if wm.get(k) != start.get(k)]
        for k in changed:
            print(f"  {k:26} {wm.get(k)}")
        if not changed:
            print("  змін немає")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Експертна система з невизначеністю (ЛР2)")
    p.add_argument("-s", "--scenario", type=int, help="номер сценарію (з 1)")
    p.add_argument("-f", "--facts", help="власний JSON-файл фактів")
    p.add_argument("--compare", action="store_true", help="порівняти з чіткою системою ЛР1")
    args = p.parse_args()

    rules = load_rules(DATA / "rules_fuzzy.json")
    variables = load_variables(DATA / "fuzzy_vars.json")
    print(f"Завантажено правил: {len(rules)}, лінгвістичних змінних: {len(variables)}")

    if args.facts:
        items = [(f"Факти з файлу {args.facts}", {"facts_file": args.facts})]
    else:
        scenarios = read_json("scenarios_fuzzy.json")
        if args.scenario is not None and not 1 <= args.scenario <= len(scenarios):
            p.error(f"немає сценарію {args.scenario}, доступні 1–{len(scenarios)}")
        idx = [args.scenario] if args.scenario is not None else range(1, len(scenarios) + 1)
        items = [(f"Сценарій {i}: {scenarios[i - 1]['name']}", scenarios[i - 1]) for i in idx]
    for title, sc in items:
        show(title, scenario_facts(sc), rules, variables, args.compare)


if __name__ == "__main__":
    main()
