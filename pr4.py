"""ПР4: тестування та адаптація бази правил.

  python3 pr4.py                – тестові сценарії на базі до адаптації (v1) і після (v2)
  python3 pr4.py -t T6          – один тест детально: що очікувалось і що вийшло
  python3 pr4.py --random 2000  – випадкові ситуації: шукає суперечливі стани
"""
import argparse
import json
import logging
import random
import sys

from analysis import CHECKS, violations, random_facts
from analysis.suite import DATA, VERSIONS, check, load, tests
from engine import WorkingMemory, load_rules, run
from ics_logging import setup_logging


def table(loaded):
    print(f"{'Тест':5} {'Тип':8} {'Ситуація':55} {'v1':6} v2")
    print("─" * 82)
    passed = {"v1": 0, "v2": 0}
    notes = []
    for t in tests():
        marks = []
        for v in ("v1", "v2"):
            ok, diff, _ = check(t, v, loaded[v])
            passed[v] += ok
            marks.append("✓" if ok else "✗")
            notes += [f"  {t['id']} {v}: {d}" for d in diff]
        print(f"{t['id']:5} {t['kind']:8} {t['name'][:55]:55} {marks[0]:6} {marks[1]}")
    n = len(tests())
    print("─" * 82)
    print(f"Пройдено: v1 – {passed['v1']} з {n}, v2 – {passed['v2']} з {n}")
    if notes:
        print("\nРозбіжності:")
        print("\n".join(notes))


def one(test_id, loaded):
    logging.getLogger("ics").info("=== ПР4, тест %s", test_id)
    found = [t for t in tests() if t["id"].upper() == test_id.upper()]
    if not found:
        sys.exit(f"немає тесту {test_id}")
    t = found[0]
    print(f"{t['id']}. {t['name']} ({t['kind']} система)")
    print("Змінені факти: " + (", ".join(f"{f['object']}.{f['attribute']} = {f['value']}"
                                        + (f" (CF {f['cf']})" if "cf" in f else "")
                                        for f in t["facts"]) or "– (база фактів з ПР2)"))
    print("Очікується:    " + ", ".join(f"{k} = {v}" for k, v in t["expect"].items()))
    for v in ("v1", "v2"):
        ok, diff, fired = check(t, v, loaded[v])
        print(f"\n{v}: спрацювали {', '.join(fired) or '—'}")
        print("  ✓ усе як очікувалось" if ok else "\n".join("  ✗ " + d for d in diff))


def random_check(n, seed=7):
    init = json.loads((DATA / "initial_state.json").read_text(encoding="utf-8"))
    print(f"Випадкових ситуацій: {n} (seed {seed})\n")
    print(f"{'Код':4} {'Суперечність':55} {'v1':>5} {'v2':>5}")
    print("─" * 72)
    counts, bad = {}, {}
    engine_log = logging.getLogger("ics.engine")
    engine_log.setLevel(logging.WARNING)        # тисячі запусків не пишемо в журнал
    for v in ("v1", "v2"):
        rules = load_rules(VERSIONS[v] / "rules.json")
        rng = random.Random(seed)
        counts[v] = {c.code: 0 for c in CHECKS}
        bad[v] = 0
        for _ in range(n):
            wm = WorkingMemory()
            wm.load(init)
            wm.load(random_facts(rng))
            before = wm.snapshot()
            run(rules, wm)
            found = violations(before, wm.snapshot())
            bad[v] += bool(found)
            for c in found:
                counts[v][c.code] += 1
    for c in CHECKS:
        print(f"{c.code:4} {c.text:55} {counts['v1'][c.code]:>5} {counts['v2'][c.code]:>5}")
    print("─" * 72)
    print(f"Ситуацій з хоча б однією суперечністю: v1 – {bad['v1']}, v2 – {bad['v2']}")
    engine_log.setLevel(logging.NOTSET)
    logging.getLogger("ics").info("ПР4: %d випадкових ситуацій, суперечностей v1 – %d, v2 – %d",
                                  n, bad["v1"], bad["v2"])


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Тестування та адаптація бази правил (ПР4)")
    p.add_argument("-t", "--test", help="показати один тест детально, наприклад T6")
    p.add_argument("--random", type=int, metavar="N", help="перевірити N випадкових ситуацій")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING"],
                   help="докладність журналу logs/ics.log")
    args = p.parse_args()
    setup_logging(args.log_level)

    if args.random:
        random_check(args.random)
        return
    loaded = {v: load(v) for v in ("v1", "v2")}
    if args.test:
        one(args.test, loaded)
    else:
        table(loaded)


if __name__ == "__main__":
    main()
