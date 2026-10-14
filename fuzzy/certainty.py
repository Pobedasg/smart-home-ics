"""Обчислення коефіцієнтів впевненості (CF) у стилі MYCIN.

CF – число від 0 до 1: 1 – повна впевненість, 0 – факт не підтверджено.
"""


def AND(*degrees):
    return min(degrees)


def OR(*degrees):
    return max(degrees)


def NOT(degree):
    return 1 - degree


def conclusion_cf(premise, weight):
    """Впевненість у висновку = ступінь виконання умови × вага правила."""
    return premise * weight


def combine(cf1, cf2):
    """Два правила підтверджують однаковий висновок: впевненість зростає,
    але ніколи не перевищує 1."""
    return cf1 + cf2 * (1 - cf1)
