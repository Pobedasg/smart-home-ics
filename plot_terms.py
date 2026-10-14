"""Графіки функцій належності для звіту ЛР2 (потрібен matplotlib).

  pip install matplotlib
  python plot_terms.py          – збереже reports/terms.png
"""
from pathlib import Path

import matplotlib.pyplot as plt

from fuzzy import load_variables

ROOT = Path(__file__).parent
COLORS = ["#2563EB", "#16A34A", "#F59E0B", "#DC2626"]

variables = load_variables(ROOT / "data" / "fuzzy_vars.json")
fig, axes = plt.subplots(2, 2, figsize=(11, 7))
for ax, (name, var) in zip(axes.flat, variables.items()):
    lo, hi = var.range
    xs = [lo + (hi - lo) * i / 500 for i in range(501)]
    for color, term in zip(COLORS, var.terms):
        ax.plot(xs, [var.mu(term, x) for x in xs], color=color, linewidth=2, label=term)
    ax.set_title(name, fontsize=12)
    ax.set_xlabel(var.unit)
    ax.set_ylabel("μ")
    ax.set_ylim(-0.05, 1.08)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9, loc="center right")
fig.tight_layout()
out = ROOT / "reports" / "terms.png"
out.parent.mkdir(exist_ok=True)
fig.savefig(out, dpi=160)
print("Збережено", out)
