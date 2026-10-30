"""Клієнт ML-сервісу. Справжній сервіс не потрібен: піднімаємо маленький
тестовий HTTP-сервер у фоновому потоці."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from fuzzy import FuzzyMemory
from hybrid import features_from, predict_overheat, prediction_fact


class FakeService(BaseHTTPRequestHandler):
    answer = (200, {"overheat_probability": 0.7})

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        code, body = self.answer
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    srv = HTTPServer(("127.0.0.1", 0), FakeService)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv, f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


FEATURES = {"hour": 11, "temp_now": 25.5, "temp_trend": 0.4, "temp_outdoor": 31}


def test_prediction_from_service(server):
    srv, url = server
    FakeService.answer = (200, {"overheat_probability": 0.7})
    assert predict_overheat(FEATURES, url) == (0.7, None)


def test_service_error_400(server):
    srv, url = server
    FakeService.answer = (400, {"error": "немає поля hour"})
    p, err = predict_overheat(FEATURES, url)
    assert p is None and "400" in err


def test_strange_answer(server):
    srv, url = server
    FakeService.answer = (200, {"something": 1})
    p, err = predict_overheat(FEATURES, url)
    assert p is None and "незрозуміла" in err


def test_service_is_down():
    p, err = predict_overheat(FEATURES, "http://127.0.0.1:9", timeout=0.5)
    assert p is None and "недоступний" in err


def test_prediction_becomes_fact():
    assert prediction_fact(0.7) == {"object": "Прогноз", "attribute": "перегрів", "value": "так", "cf": 0.7}
    assert prediction_fact(0.1)["value"] == "ні"
    assert prediction_fact(0.1)["cf"] == pytest.approx(0.9)


def test_features_are_taken_from_memory():
    m = FuzzyMemory()
    m.load([{"object": "Час", "attribute": "година", "value": 11},
            {"object": "Кімната", "attribute": "температура", "value": 25.5},
            {"object": "Кімната", "attribute": "зміна_температури", "value": 0.4}])
    assert features_from(m) is None            # немає температури надворі
    m.load([{"object": "Середовище", "attribute": "температура_надворі", "value": 31}])
    assert features_from(m) == FEATURES
