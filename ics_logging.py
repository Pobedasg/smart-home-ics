"""Логування ІКС (ЛР4).

Усі модулі пишуть у логери з іменами «ics.*» (ics.engine, ics.fuzzy, ics.ml, ...).
setup_logging() один раз налаштовує запис у файл logs/ics.log.
Рівні: INFO – рішення системи, DEBUG – подробиці (чому спрацювало правило),
WARNING – проблеми (сервіс недоступний, досягнуто ліміт циклів).
"""
import logging
from pathlib import Path

LOG_FILE = Path(__file__).parent / "logs" / "ics.log"
FORMAT = "%(asctime)s %(levelname)-7s %(name)-10s %(message)s"


def setup_logging(level="INFO", path=LOG_FILE, console=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("ics")
    logger.setLevel(level)
    logger.handlers.clear()
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter(FORMAT, "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    if console:
        stream = logging.StreamHandler()
        stream.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(stream)
    logger.propagate = False
    return logger
