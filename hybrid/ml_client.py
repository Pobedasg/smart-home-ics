"""Клієнт ML-сервісу: ІКС звертається до REST API і перетворює відповідь на факт.

Використовує лише стандартну бібліотеку (urllib), тож ядру системи
не потрібні сторонні пакети. Якщо сервіс не відповідає, повертається None,
і система працює на самих правилах, як у ЛР2.
"""
import json
import logging
from urllib import error, request

DEFAULT_URL = "http://127.0.0.1:8000"
log = logging.getLogger("ics.ml")

# які факти робочої пам'яті передаються моделі як ознаки
FEATURE_FACTS = {
    "hour": "Час.година",
    "temp_now": "Кімната.температура",
    "temp_trend": "Кімната.зміна_температури",
    "temp_outdoor": "Середовище.температура_надворі",
}


def features_from(mem):
    """Збирає з пам'яті ознаки для запиту. None, якщо якогось факту бракує."""
    if not all(mem.has(fact) for fact in FEATURE_FACTS.values()):
        return None
    return {name: mem.value(fact) for name, fact in FEATURE_FACTS.items()}


def predict_overheat(features, url=DEFAULT_URL, timeout=2.0):
    """POST /predict. Повертає (ймовірність, None) або (None, текст помилки)."""
    body = json.dumps(features).encode("utf-8")
    req = request.Request(f"{url}/predict", data=body, method="POST",
                          headers={"Content-Type": "application/json"})
    log.info("Запит POST %s/predict %s", url, features)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            answer = json.loads(resp.read().decode("utf-8"))
        p = float(answer["overheat_probability"])
        log.info("Відповідь сервісу: ймовірність перегріву %.2f", p)
        return p, None
    except error.HTTPError as e:
        msg = f"сервіс відповів помилкою {e.code}: {e.read().decode('utf-8', 'replace')}"
    except (error.URLError, TimeoutError, OSError) as e:
        msg = f"сервіс недоступний ({getattr(e, 'reason', e)})"
    except (KeyError, ValueError) as e:
        msg = f"незрозуміла відповідь сервісу ({e})"
    log.warning("ML-сервіс: %s, рішення лише за правилами", msg)
    return None, msg


def prediction_fact(p):
    """Ймовірність від моделі стає фактом з коефіцієнтом впевненості.

    p ≥ 0.5 – «перегрів = так» з CF p; інакше «перегрів = ні» з CF 1 − p.
    Для рушія ЛР2 це одне й те саме: «ні» з CF 0.9 означає «так» зі ступенем 0.1.
    """
    p = round(p, 2)
    if p >= 0.5:
        return {"object": "Прогноз", "attribute": "перегрів", "value": "так", "cf": p}
    return {"object": "Прогноз", "attribute": "перегрів", "value": "ні", "cf": round(1 - p, 2)}
