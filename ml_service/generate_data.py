"""Генерує навчальні дані для моделі прогнозу перегріву (ЛР3).

Справжньої історії з датчиків будинку немає, тому дані синтетичні, але
з фізично правдоподібною поведінкою. Моделюються 400 літніх днів із кроком
10 хвилин:
  * температура надворі: середня за день (від 16 до 30 °C) + добова хвиля
    з максимумом близько 15:00 + шум;
  * температура в кімнаті повільно тягнеться до вуличної (теплообмін через
    стіни), вдень її ще підігріває сонце у вікна, плюс невеликий шум.
Кондиціонер у даних не працює: модель вчиться, як кімната нагрівалася б сама.

Для кожного моменту записуються ознаки і мітка:
  hour          година доби (дробова, 14.5 = 14:30)
  temp_now      температура в кімнаті зараз, °C
  temp_trend    зміна температури в кімнаті за останні 30 хв, °C
  temp_outdoor  температура надворі, °C
  overheat_30   1, якщо через 30 хв у кімнаті буде понад 26 °C, інакше 0
"""
import csv
import math
import random
from pathlib import Path

random.seed(42)
OUT = Path(__file__).parent / "data"
STEP_MIN = 10
STEPS_PER_DAY = 24 * 60 // STEP_MIN
AHEAD = 30 // STEP_MIN          # горизонт прогнозу: 30 хв = 3 кроки
HOT = 26.0                      # той самий поріг «спеки», що й у правилах ЛР1


def outdoor(mean, amp, hour):
    return mean + amp * math.sin(2 * math.pi * (hour - 9) / 24)     # пік о 15:00


def sun(hour, strength):
    """Нагрів від сонця у вікна: є лише вдень, найсильніший о 13–14."""
    if 8 <= hour <= 19:
        return strength * math.sin(math.pi * (hour - 8) / 11)
    return 0.0


def simulate_day():
    mean = random.uniform(16, 30)
    amp = random.uniform(4, 8)
    strength = random.uniform(0.0, 0.12)      # наскільки сонячна сторона, штори
    clouds = random.random()                   # хмарність змінюється протягом дня
    t_in = mean - 2 + random.gauss(0, 1.5)
    true, measured, outs, hours = [], [], [], []
    for s in range(STEPS_PER_DAY + AHEAD):
        hour = (s * STEP_MIN / 60) % 24
        clouds = min(1, max(0, clouds + random.gauss(0, 0.08)))
        t_out = outdoor(mean, amp, hour) - 3 * clouds + random.gauss(0, 0.5)
        t_in += 0.03 * (t_out - t_in) + sun(hour, strength) * (1 - clouds) + random.gauss(0, 0.08)
        true.append(t_in)
        measured.append(t_in + random.gauss(0, 0.2))     # похибка датчика
        outs.append(t_out)
        hours.append(hour)
    return true, measured, outs, hours


def main():
    OUT.mkdir(exist_ok=True)
    rows = []
    for _ in range(400):
        true, measured, outs, hours = simulate_day()
        for s in range(3, STEPS_PER_DAY):
            # ознаки – те, що бачать датчики (з похибкою), мітка – справжня температура
            rows.append([round(hours[s], 2), round(measured[s], 1),
                         round(measured[s] - measured[s - 3], 1), round(outs[s], 1),
                         int(true[s + AHEAD] > HOT)])
    with open(OUT / "overheat.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["hour", "temp_now", "temp_trend", "temp_outdoor", "overheat_30"])
        w.writerows(rows)
    share = sum(r[-1] for r in rows) / len(rows)
    print(f"overheat.csv: {len(rows)} рядків, частка «перегріву» {share:.0%}")


if __name__ == "__main__":
    main()
