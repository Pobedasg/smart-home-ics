"""REST API сервісу. Тести пропускаються, якщо модель ще не навчена
(спершу python3 ml_service/generate_data.py і python3 ml_service/train.py)."""
import pytest

from conftest import ROOT

pytest.importorskip("flask")
pytest.importorskip("sklearn")
if not (ROOT / "ml_service" / "models" / "overheat_model.joblib").exists():
    pytest.skip("модель не навчена", allow_module_level=True)

from ml_service.app import app   # noqa: E402

GOOD = {"hour": 11, "temp_now": 25.5, "temp_trend": 0.4, "temp_outdoor": 31}


@pytest.fixture
def client():
    return app.test_client()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_predict_returns_probability(client):
    r = client.post("/predict", json=GOOD)
    assert r.status_code == 200
    assert 0 <= r.get_json()["overheat_probability"] <= 1


def test_morning_heat_is_more_likely_than_evening(client):
    morning = client.post("/predict", json=GOOD).get_json()["overheat_probability"]
    evening = client.post("/predict", json={"hour": 21, "temp_now": 25.5, "temp_trend": -0.3,
                                            "temp_outdoor": 22}).get_json()["overheat_probability"]
    assert morning > 0.5 > evening


@pytest.mark.parametrize("body, text", [
    ({"hour": 11}, "немає поля"),
    ({**GOOD, "temp_now": 80}, "має бути від"),
    ({**GOOD, "hour": "одинадцята"}, "числом"),
    ({**GOOD, "hour": True}, "числом"),
    ([1, 2, 3], "JSON-об'єкт"),
])
def test_bad_requests(client, body, text):
    r = client.post("/predict", json=body)
    assert r.status_code == 400
    assert text in r.get_json()["error"]
