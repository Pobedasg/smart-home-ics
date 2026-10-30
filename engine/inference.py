"""Механізм логічного виведення: прямий ланцюжок (forward chaining).

Кожен цикл має три кроки:
  1) зіставлення – знайти всі правила, умови яких виконуються (конфліктний набір);
  2) вибір – узяти правило з найбільшим salience (при рівності – перше у файлі);
  3) виконання – змінити факти в робочій пам'яті.
Кожне правило спрацьовує не більше одного разу (рефракція), тому система
не зациклюється. Виведення зупиняється, коли конфліктний набір порожній.
"""
import logging
from dataclasses import dataclass, field

log = logging.getLogger("ics.engine")


@dataclass
class Step:
    cycle: int
    agenda: list          # конфліктний набір цього циклу
    rule: object          # правило, яке спрацювало
    reasons: list         # факти, через які воно спрацювало
    changes: list = field(default_factory=list)


def run(rules, wm, max_cycles=50):
    fired = set()
    trace = []
    log.info("Старт виведення: правил %d, фактів %d", len(rules), len(wm.facts))
    for cycle in range(1, max_cycles + 1):
        agenda = [r for r in rules if r.id not in fired and r.matches(wm)]
        if not agenda:
            break
        agenda.sort(key=lambda r: (-r.salience, r.order))
        rule = agenda[0]
        reasons = rule.reasons(wm)
        changes = rule.fire(wm)
        fired.add(rule.id)
        trace.append(Step(cycle, agenda, rule, reasons, changes))
        log.info("Цикл %d: конфліктний набір %s, спрацьовує %s «%s»",
                 cycle, agenda, rule.id, rule.name)
        log.debug("  %s: умови %s", rule.id, "; ".join(reasons))
        for key, old, new in changes:
            log.info("  %s: %s → %s", key, "—" if old is None else old, new)
    else:
        log.warning("Досягнуто ліміт у %d циклів, виведення зупинено", max_cycles)
    log.info("Кінець виведення: спрацювало правил %d (%s)",
             len(trace), ", ".join(s.rule.id for s in trace) or "—")
    return trace
