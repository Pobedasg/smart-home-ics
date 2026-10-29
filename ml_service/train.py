"""Навчає модель прогнозу перегріву (ЛР3) і зберігає її в ml_service/models/.

Модель – випадковий ліс (RandomForestClassifier): багато дерев рішень, кожне
голосує «буде перегрів / не буде», а частка голосів «за» – це ймовірність.
Для порівняння рахується простий базовий прогноз «через 30 хв буде так само,
як зараз», щоб було видно, що модель справді щось додає.
"""
import csv
import json
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

HERE = Path(__file__).parent
FEATURES = ["hour", "temp_now", "temp_trend", "temp_outdoor"]


def main():
    with open(HERE / "data" / "overheat.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    X = [[float(r[k]) for k in FEATURES] for r in rows]
    y = [int(r["overheat_30"]) for r in rows]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=1, stratify=y)

    model = RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_leaf=20,
                                   random_state=1, n_jobs=-1)
    model.fit(Xtr, ytr)
    proba = model.predict_proba(Xte)[:, 1]
    pred = [int(p >= 0.5) for p in proba]
    baseline = [int(x[1] > 26) for x in Xte]          # «буде як зараз»

    # перевірка там, де прогноз справді потрібен: зараз ще не спекотно
    idx = [i for i, x in enumerate(Xte) if x[1] <= 26]
    near = lambda v: [v[i] for i in idx]

    metrics = {
        "model": "RandomForestClassifier (100 дерев, глибина до 8)",
        "features": FEATURES,
        "train_size": len(Xtr), "test_size": len(Xte),
        "accuracy": round(accuracy_score(yte, pred), 3),
        "f1": round(f1_score(yte, pred), 3),
        "roc_auc": round(roc_auc_score(yte, proba), 3),
        "baseline_accuracy": round(accuracy_score(yte, baseline), 3),
        "baseline_f1": round(f1_score(yte, baseline), 3),
        "not_hot_yet_f1": round(f1_score(near(yte), near(pred)), 3),
        "not_hot_yet_baseline_f1": round(f1_score(near(yte), near(baseline), zero_division=0), 3),
        "feature_importance": {k: round(v, 3) for k, v in zip(FEATURES, model.feature_importances_)},
    }
    (HERE / "models").mkdir(exist_ok=True)
    joblib.dump(model, HERE / "models" / "overheat_model.joblib", compress=3)
    (HERE / "models" / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Навчено на {len(Xtr)} прикладах, перевірено на {len(Xte)}.")
    print(f"  модель:          accuracy {metrics['accuracy']}, F1 {metrics['f1']}, "
          f"ROC AUC {metrics['roc_auc']}")
    print(f"  «буде як зараз»: accuracy {metrics['baseline_accuracy']}, F1 {metrics['baseline_f1']}")
    print(f"  коли ще ≤ 26 °C: F1 моделі {metrics['not_hot_yet_f1']}, "
          f"базового {metrics['not_hot_yet_baseline_f1']}")
    print("  важливість ознак:", ", ".join(f"{k} {v}" for k, v in metrics["feature_importance"].items()))
    print("Модель збережено в models/overheat_model.joblib")


if __name__ == "__main__":
    main()
