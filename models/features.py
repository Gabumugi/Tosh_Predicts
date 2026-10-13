"""Feature helpers: attach synthetic historical matches so the model can be
fit even when the user has no historical CSV yet. In production replace
this with real historic data from football-data.co.uk."""
import random
from datetime import datetime, timedelta
from typing import List


_STRENGTH = {
    # crude prior strength map — replace with real ratings from Understat/Elo
    "Arsenal": 1.35, "Man City": 1.55, "Liverpool": 1.40, "Newcastle": 1.10,
    "Brighton": 1.05, "Everton": 0.80,
    "Bayern Munich": 1.60, "Freiburg": 0.95, "Dortmund": 1.25, "Stuttgart": 1.15,
    "Real Madrid": 1.55, "Getafe": 0.80, "Barcelona": 1.45, "Sevilla": 1.00,
    "Inter": 1.45, "Torino": 0.90, "Juventus": 1.25, "Napoli": 1.20,
    "PSG": 1.60, "Nantes": 0.75, "Marseille": 1.15, "Lyon": 1.05,
    "Flamengo": 1.35, "Palmeiras": 1.30,
}


def synthesise_history(teams: List[str], matches_per_team: int = 20) -> List[dict]:
    """
    Create realistic-looking historical matches for the given teams based on
    their prior strengths. Used only when no real history is available.
    """
    random.seed(42)
    history = []
    now = datetime.utcnow()
    for _ in range(matches_per_team * len(teams) // 2):
        h, a = random.sample(teams, 2)
        sh = _STRENGTH.get(h, 1.0)
        sa = _STRENGTH.get(a, 1.0)
        lh = 1.35 * sh / sa
        la = 1.10 * sa / sh
        hg = _poisson_sample(lh)
        ag = _poisson_sample(la)
        days_ago = random.randint(1, 365)
        history.append({
            "home_team": h, "away_team": a,
            "home_goals": hg, "away_goals": ag,
            "days_ago": days_ago,
            "date": (now - timedelta(days=days_ago)).date().isoformat(),
        })
    return history


def _poisson_sample(lam: float, rng: random.Random | None = None) -> int:
    rng = rng or random
    L = pow(2.718281828, -lam)
    k, p = 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1