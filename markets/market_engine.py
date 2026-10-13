"""Derive all market probabilities from a Dixon-Coles score grid."""
import numpy as np
from typing import Dict


def _grid_sum(grid: np.ndarray, predicate) -> float:
    n = grid.shape[0]
    return float(sum(grid[i, j] for i in range(n) for j in range(n) if predicate(i, j)))


def compute_all_markets(grid: np.ndarray) -> Dict[str, float]:
    n = grid.shape[0]
    markets: Dict[str, float] = {}

    home = _grid_sum(grid, lambda i, j: i > j)
    draw = _grid_sum(grid, lambda i, j: i == j)
    away = _grid_sum(grid, lambda i, j: i < j)
    markets["1X2:1"] = home
    markets["1X2:X"] = draw
    markets["1X2:2"] = away

    markets["DC:1X"] = home + draw
    markets["DC:X2"] = draw + away
    markets["DC:12"] = home + away

    if home + away > 0:
        markets["DNB:1"] = home / (home + away)
        markets["DNB:2"] = away / (home + away)

    for line in (0.5, 1.5, 2.5, 3.5, 4.5):
        over = _grid_sum(grid, lambda i, j, L=line: i + j > L)
        markets[f"OU:{line}:Over"] = over
        markets[f"OU:{line}:Under"] = 1.0 - over

    p_h0 = float(grid[0, :].sum())
    p_a0 = float(grid[:, 0].sum())
    p_00 = float(grid[0, 0])
    btts_yes = 1.0 - p_h0 - p_a0 + p_00
    markets["BTTS:Yes"] = btts_yes
    markets["BTTS:No"] = 1.0 - btts_yes

    # Asian Handicap: home line in {-2.5, -1.5, -1.0, -0.5, 0, +0.5, +1.5}
    for line in (-2.5, -1.5, -1.0, -0.5, 0.0, 0.5, 1.5):
        win = 0.0
        push = 0.0
        for i in range(n):
            for j in range(n):
                diff = (i - j) + line
                if abs(diff + 0.0) < 1e-9:
                    push += grid[i, j]
                elif diff > 0:
                    win += grid[i, j]
        # Simplified: ignore quarter lines for MVP
        p = win / (1.0 - push) if (1.0 - push) > 0 else 0.0
        markets[f"AH:home_{line:+g}"] = p
        markets[f"AH:away_{-line:+g}"] = 1.0 - p

    # Correct score top grid cells
    flat = [(f"{i}-{j}", float(grid[i, j]))
            for i in range(n) for j in range(n)]
    flat.sort(key=lambda x: x[1], reverse=True)
    for rank, (score, p) in enumerate(flat[:8], start=1):
        markets[f"CS:{score}"] = p

    return markets


def fair_odds(p: float) -> float:
    return round(1.0 / p, 3) if p > 0 else 0.0