"""Запуск програм з консолі (main.py, lr2.py, lr3.py, pr4.py) – перевіряємо,
що вони відпрацьовують без помилок і друкують головне."""
import sys

import pytest

import lr2
import lr3
import main
import pr4


@pytest.fixture(autouse=True)
def no_log_file(monkeypatch):
    for module in (main, lr2, lr3, pr4):
        monkeypatch.setattr(module, "setup_logging", lambda *a, **k: None)


def start(module, monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", [module.__name__ + ".py", *args])
    module.main()


def test_lr1_all_scenarios(monkeypatch, capsys):
    start(main, monkeypatch)
    out = capsys.readouterr().out
    assert "Сценарій 7" in out and "тривога" in out


def test_lr1_explain(monkeypatch, capsys):
    start(main, monkeypatch, "-s", "3", "--explain", "R18,R21")
    assert "потрібно Режим.криза = ні, а є так" in capsys.readouterr().out


def test_lr1_wrong_scenario(monkeypatch):
    with pytest.raises(SystemExit):
        start(main, monkeypatch, "-s", "99")


def test_lr2_compare(monkeypatch, capsys):
    start(lr2, monkeypatch, "-s", "2", "--compare")
    out = capsys.readouterr().out
    assert "CF 0.58" in out and "чітка система ЛР1" in out


def test_lr3_without_service(monkeypatch, capsys):
    start(lr3, monkeypatch, "-s", "1", "--url", "http://127.0.0.1:9")
    assert "сервіс недоступний" in capsys.readouterr().out


def test_pr4_table(monkeypatch, capsys):
    start(pr4, monkeypatch)
    assert "v2 – 17 з 17" in capsys.readouterr().out


def test_pr4_one_test(monkeypatch, capsys):
    start(pr4, monkeypatch, "-t", "T6")
    assert "усе як очікувалось" in capsys.readouterr().out


def test_pr4_random(monkeypatch, capsys):
    start(pr4, monkeypatch, "--random", "100")
    assert "v2 – 0" in capsys.readouterr().out
