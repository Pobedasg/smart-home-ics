"""ML-сервіс прогнозу перегріву (ЛР3): REST API на Flask.

Запуск (з кореня проєкту):
  python3 ml_service/generate_data.py   – один раз, згенерувати навчальні дані
  python3 ml_service/train.py           – один раз, навчити модель
  python3 ml_service/app.py             – запустити сервіс на http://127.0.0.1:8000

Ендпоінти:
  GET  /health   – чи живий сервіс, яка модель і її якість
  POST /predict  – прогноз; тіло запиту JSON:
       {"hour": 11, "temp_now": 25.5, "temp_trend": 0.4, "temp_outdoor": 31}
       відповідь:
       {"overheat_probability": 0.7, "horizon_min": 30, "threshold_c": 26}
"""
import json
import logging
from pathlib import Path

import joblib
from flask import Flask, jsonify, request

HERE = Path(__file__).parent
PORT = 8000            # 5000 на macOS зайнятий AirPlay, тому 8000

app = Flask(__name__)
log = logging.getLogger("ics.service")
app.json.ensure_ascii = False

model = joblib.load(HERE / "models" / "overheat_model.joblib")
metrics = json.loads((HERE / "models" / "metrics.json").read_text(encoding="utf-8"))

# поле: (мінімум, максимум) – усе, що поза межами, вважаємо помилкою датчика
FIELDS = {"hour": (0, 24), "temp_now": (-10, 50), "temp_trend": (-5, 5), "temp_outdoor": (-40, 50)}


def validate(data):
    """Перевіряє тіло запиту. Повертає текст помилки або None."""
    if not isinstance(data, dict):
        return "очікується JSON-об'єкт"
    for key, (lo, hi) in FIELDS.items():
        if key not in data:
            return f"немає поля {key}"
        value = data[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"поле {key} має бути числом"
        if not lo <= value <= hi:
            return f"поле {key} має бути від {lo} до {hi}"
    return None


@app.get("/health")
def health():
    return jsonify(status="ok", model=metrics["model"], features=metrics["features"],
                   accuracy=metrics["accuracy"], roc_auc=metrics["roc_auc"])


@app.post("/predict")
def predict():
    data = request.get_json(silent=True)
    error = validate(data)
    if error:
        log.warning("Відхилено запит %s: %s", data, error)
        return jsonify(error=error), 400
    x = [[float(data[k]) for k in metrics["features"]]]
    p = float(model.predict_proba(x)[0][1])
    log.info("Прогноз для %s: %.2f", data, p)
    return jsonify(overheat_probability=round(p, 2), horizon_min=30, threshold_c=26)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE.parent))
    from ics_logging import setup_logging
    setup_logging(path=HERE.parent / "logs" / "ml_service.log")
    app.run(host="127.0.0.1", port=PORT)
