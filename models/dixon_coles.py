"""Dixon-Coles bivariate Poisson model for football score prediction.

Fit on historical match results per league using maximum likelihood
with an exponential time-decay weighting.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson
from typing import List, Dict, Tuple


class DixonColesModel:
    def __init__(self, xi: float = 0.0018, max_goals: int = 10):
        """
        xi: time-decay parameter (higher = faster decay, more weight on recent)
        max_goals: score grid dimension
        """
        self.xi = xi
        self.max_goals = max_goals
        self.teams: List[str] = []
        self.attack: Dict[str, float] = {}
        self.defence: Dict[str, float] = {}
        self.home_adv: float = 0.25
        self.rho: float = -0.05  # low-score correlation

    # ---------- static helpers ----------
    @staticmethod
    def _tau(x, y, lh, la, rho):
        if x == 0 and y == 0:
            return 1 - lh * la * rho
        if x == 0 and y == 1:
            return 1 + lh * rho
        if x == 1 and y == 0:
            return 1 + la * rho
        if x == 1 and y == 1:
            return 1 - rho
        return 1.0

    def _neg_log_likelihood(self, params, matches, weights):
        n = len(self.teams)
        attack = params[:n]
        defence = params[n:2 * n]
        home_adv = params[2 * n]
        rho = params[2 * n + 1]

        # identifiability: mean attack = 0
        attack = attack - attack.mean()

        ll = 0.0
        for (h_idx, a_idx, hg, ag), w in zip(matches, weights):
            lh = np.exp(attack[h_idx] + defence[a_idx] + home_adv)
            la = np.exp(attack[a_idx] + defence[h_idx])
            if hg > self.max_goals or ag > self.max_goals:
                continue
            p_h = poisson.pmf(hg, lh)
            p_a = poisson.pmf(ag, la)
            tau = self._tau(hg, ag, lh, la, rho)
            p = max(p_h * p_a * tau, 1e-10)
            ll += w * np.log(p)
        return -ll

    # ---------- fit ----------
    def fit(self, history: List[dict]):
        """
        history: list of dicts with keys
            home_team, away_team, home_goals, away_goals, days_ago
        """
        self.teams = sorted({m["home_team"] for m in history} | {m["away_team"] for m in history})
        idx = {t: i for i, t in enumerate(self.teams)}
        n = len(self.teams)

        matches = []
        weights = []
        for m in history:
            matches.append((idx[m["home_team"]], idx[m["away_team"]],
                            int(m["home_goals"]), int(m["away_goals"])))
            weights.append(np.exp(-self.xi * m.get("days_ago", 0)))
        weights = np.array(weights)

        x0 = np.concatenate([
            np.zeros(n),                    # attack
            np.zeros(n),                    # defence
            [0.25],                         # home advantage
            [-0.05],                        # rho
        ])
        bounds = [(-3, 3)] * (2 * n) + [(0.0, 1.0), (-0.2, 0.2)]

        res = minimize(
            self._neg_log_likelihood, x0, args=(matches, weights),
            method="L-BFGS-B", bounds=bounds,
            options={"maxiter": 500, "disp": False},
        )
        p = res.x
        attack = p[:n] - p[:n].mean()
        defence = p[n:2 * n]
        self.attack = {t: attack[i] for i, t in enumerate(self.teams)}
        self.defence = {t: defence[i] for i, t in enumerate(self.teams)}
        self.home_adv = float(p[2 * n])
        self.rho = float(p[2 * n + 1])
        return self

    # ---------- predict ----------
    def expected_goals(self, home: str, away: str) -> Tuple[float, float]:
        a_h = self.attack.get(home, 0.0)
        d_h = self.defence.get(home, 0.0)
        a_a = self.attack.get(away, 0.0)
        d_a = self.defence.get(away, 0.0)
        lh = np.exp(a_h + d_a + self.home_adv)
        la = np.exp(a_a + d_h)
        return float(lh), float(la)

    def score_grid(self, home: str, away: str) -> np.ndarray:
        lh, la = self.expected_goals(home, away)
        g = np.outer(
            poisson.pmf(np.arange(self.max_goals + 1), lh),
            poisson.pmf(np.arange(self.max_goals + 1), la),
        )
        for i in range(2):
            for j in range(2):
                g[i, j] *= self._tau(i, j, lh, la, self.rho)
        return g / g.sum()