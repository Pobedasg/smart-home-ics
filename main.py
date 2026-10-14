"""Rule-based система керування мікрокліматом розумного будинку (ЛР1).

Запуск:
  python main.py                 – усі сценарії з data/scenarios.json
  python main.py -s 3            – лише сценарій 3
  python main.py -s 3 --explain  – плюс пояснення, чому інші правила не спрацювали
  python main.py -s 3 --explain R18,R21 – пояснення лише для вказаних правил
  python main.py -f my.json      – власний файл фактів
"""
import argparse
import json
import sys
import textwrap
from pathlib import Path

from engine import WorkingMemory, load_rules, run

DATA = Path(__file__).parent / "data"
DEVICES = ["Мешканці.є_люди", "Охорона.джерело_руху", "Сигналізація.стан",
           "Режим.назва", "Режим.криза", "Вікна.стан", "Кондиціонер.режим",
           "Обігрівач.стан", "Очищувач.режим", "Тепла_підлога.потужність", "Поїлка.стан"]
SHOWN_INPUT = ("Режим.назва", "Вікна.стан")   # стани, які можуть бути вхідними даними


def read_json(name):
    path = Path(name) if Path(name).exists() else DATA / name
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_memory(scenario):
    wm = WorkingMemory()
    wm.load(read_json("initial_state.json"))
    wm.load(read_json(scenario.get("facts_file") or scenario.get("base", "facts.json")))
    wm.load(scenario.get("facts", []))
    return wm


def show(name, rules, wm, explain=False):
    line = "═" * 70
    print(f"\n{line}\n {name}\n{line}")
    print("Вхідні факти:")
    for k, v in wm.snapshot().items():
        if k not in DEVICES or k in SHOWN_INPUT:
            print(f"  {k} = {v}")

    before = wm.snapshot()
    trace = run(rules, wm)

    print("\nХід виведення:")
    if not trace:
        print("  жодне правило не спрацювало")
    for st in trace:
        agenda = ", ".join(repr(r) for r in st.agenda)
        print(f"  Цикл {st.cycle}. Конфліктний набір: {agenda}")
        print(f"    → спрацьовує {st.rule.id} «{st.rule.name}» "
              f"(salience {st.rule.salience}, вага {st.rule.weight})")
        print(textwrap.fill("; ".join(st.reasons), width=78,
                            initial_indent="      бо: ", subsequent_indent="          "))
        for key, old, new in st.changes:
            print(f"      {key}: {'—' if old is None else old} → {new}")
        if not st.changes:
            print("      (факти вже мали ці значення)")

    fired = {st.rule.id for st in trace}
    silent = [r for r in rules if r.id not in fired]
    print()
    print(textwrap.fill("Не спрацювали: " + ", ".join(r.id for r in silent), width=78,
                        subsequent_indent="  "))
    if explain:
        wanted = None if explain == "all" else set(explain.upper().split(","))
        for r in [r for r in silent if wanted is None or r.id in wanted]:
            print(textwrap.fill("; ".join(r.failed(wm)), width=78,
                                initial_indent=f"  {r.id} «{r.name}»: ", subsequent_indent="      "))

    print("\nРезультат (стан системи і пристроїв):")
    for k in DEVICES:
        mark = "  ← змінено" if before.get(k) != wm.get(k) else ""
        if wm.get(k) is not None:
            print(f"  {k:26} {wm.get(k)}{mark}")
    return trace


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # кирилиця в консолі Windows

    p = argparse.ArgumentParser(description="Rule-based система розумного будинку")
    p.add_argument("-s", "--scenario", type=int, help="номер сценарію (з 1)")
    p.add_argument("-f", "--facts", help="власний JSON-файл фактів")
    p.add_argument("--explain", nargs="?", const="all", metavar="R18,R21",
                   help="пояснити, чому правила не спрацювали (усі або вказані)")
    args = p.parse_args()

    rules = load_rules(DATA / "rules.json")
    print(f"Завантажено правил: {len(rules)} (R1–R{len(rules)})")

    if args.facts:
        scenarios = [{"name": f"Факти з файлу {args.facts}", "facts_file": args.facts}]
    else:
        scenarios = read_json("scenarios.json")
        if args.scenario is not None and not 1 <= args.scenario <= len(scenarios):
            p.error(f"немає сценарію {args.scenario}, доступні 1–{len(scenarios)}")
        if args.scenario:
            scenarios = [scenarios[args.scenario - 1]]

    for i, sc in enumerate(scenarios, 1):
        num = args.scenario or i
        title = sc["name"] if args.facts else f"Сценарій {num}: {sc['name']}"
        show(title, rules, build_memory(sc), args.explain)


if __name__ == "__main__":
    main()
