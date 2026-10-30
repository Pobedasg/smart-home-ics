import logging

from conftest import make_rule
from engine import WorkingMemory, run
from ics_logging import setup_logging


def test_inference_is_logged(tmp_path):
    log_file = tmp_path / "ics.log"
    setup_logging("INFO", path=log_file)
    wm = WorkingMemory()
    wm.set("Кімната.температура", 28)
    rule = make_rule("R21", {"fact": "Кімната.температура", "op": ">", "value": 26},
                     [{"set": "Кондиціонер.режим", "value": "помірне_охолодження"}])
    run([rule], wm)
    for h in logging.getLogger("ics").handlers:
        h.flush()
    text = log_file.read_text(encoding="utf-8")
    assert "спрацьовує R21" in text
    assert "Кондиціонер.режим: — → помірне_охолодження" in text
    assert "Кінець виведення" in text


def test_warning_when_service_is_down(tmp_path):
    from hybrid import predict_overheat
    log_file = tmp_path / "ics.log"
    setup_logging("INFO", path=log_file)
    predict_overheat({"hour": 1, "temp_now": 20, "temp_trend": 0, "temp_outdoor": 20},
                     "http://127.0.0.1:9", timeout=0.5)
    for h in logging.getLogger("ics").handlers:
        h.flush()
    assert "WARNING" in log_file.read_text(encoding="utf-8")
