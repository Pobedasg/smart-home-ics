import pytest

from fuzzy.membership import trapezoid


@pytest.mark.parametrize("x, expected", [
    (10, 0.0), (20, 0.5), (25, 1.0), (30, 1.0), (35, 0.5), (40, 0.0), (50, 0.0),
])
def test_trapezoid(x, expected):
    assert trapezoid(x, 15, 25, 30, 40) == pytest.approx(expected)


def test_triangle_is_trapezoid_with_one_peak():
    assert trapezoid(25, 22, 25, 25, 28) == 1.0
    assert trapezoid(23.5, 22, 25, 25, 28) == pytest.approx(0.5)


def test_shoulders_cover_values_outside_range():
    # крайній терм: усе за межею належить йому повністю (36 °C – теж «спекотно»)
    assert trapezoid(36, 25, 27, 35, 35) == 1.0
    assert trapezoid(5, 10, 10, 16, 19) == 1.0


def test_temperature_terms_overlap(variables):
    t = variables["Кімната.температура"].fuzzify(25.5)
    assert t["тепло"] == pytest.approx(0.83)
    assert t["спекотно"] == pytest.approx(0.25)
    assert t["холодно"] == 0


def test_every_variable_has_terms(variables):
    assert set(variables) == {"Кімната.температура", "Кімната.вологість",
                              "Кімната.рівень_CO2", "Середовище.індекс_забруднення"}
    for var in variables.values():
        lo, hi = var.range
        for term, (a, b, c, d) in var.terms.items():
            assert a <= b <= c <= d, f"{var.name}: {term}"
            assert lo <= a and d <= hi
