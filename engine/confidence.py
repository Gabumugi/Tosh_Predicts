"""Confidence score for each signal. Weighted blend of:
- probability strength (already filtered)
- EV magnitude (bigger edge = more confidence, but capped)
- data completeness (do we have all inputs?)
- market liquidity (line depth / book coverage)
"""


def compute_confidence(prob: float, ev: float, has_odds: bool = True) -> float:
    """
    Returns a 0–100 confidence score.
    """
    # Probability component: 0.5 -> 0, 1.0 -> 100
    p_score = max(0.0, min(1.0, (prob - 0.5) * 2.0)) * 100

    # EV component: 0% EV -> 0, 30% EV -> 100 (capped)
    ev_score = max(0.0, min(1.0, ev / 0.30)) * 100

    # Liquidity
    liq = 100.0 if has_odds else 30.0

    # Weighted blend
    score = 0.45 * p_score + 0.35 * ev_score + 0.20 * liq
    return round(score, 1)


def label(score: float) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 55:
        return "MEDIUM"
    return "LOW"