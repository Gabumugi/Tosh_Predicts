"""Rank markets by expected value and return the Top N signals."""
from typing import List, Dict


def no_vig_probabilities(prices: List[float]) -> List[float]:
    """Given a list of decimal odds for mutually exclusive outcomes,
    strip the bookmaker margin."""
    implied = [1.0 / p for p in prices if p and p > 1.0]
    s = sum(implied)
    if s <= 0:
        return []
    return [p / s for p in implied]


def expected_value(prob: float, odds: float) -> float:
    return prob * odds - 1.0


def find_value_signals(
    predictions: List[dict],
    odds: Dict[str, dict],
    min_prob: float,
    min_ev: float,
) -> List[dict]:
    """
    predictions: [{'match_external_id', 'market', 'probability', 'fair_odds'}]
    odds: {external_id: {'1X2': {'1':..}, 'OU25': {...}, 'BTTS': {...}, 'AH': {...}}}
    Returns sorted list of signal dicts.
    """
    signals = []
    for pred in predictions:
        ext = pred["match_external_id"]
        market = pred["market"]
        prob = pred["probability"]
        if prob < min_prob:
            continue

        best_price, best_book = _best_price_for(market, odds.get(ext, {}))
        if best_price is None:
            continue

        ev = expected_value(prob, best_price)
        if ev < min_ev:
            continue

        signals.append({
            "match_external_id": ext,
            "market": market,
            "probability": round(prob, 4),
            "fair_odds": pred["fair_odds"],
            "best_odds": best_price,
            "bookmaker": best_book or "consensus",
            "ev": round(ev, 4),
        })

    signals.sort(key=lambda s: s["ev"], reverse=True)
    return signals


def _best_price_for(market: str, odds: dict):
    """Map our internal market key onto the odds dict shape."""
    if ":" not in market:
        return None, None
    family, selection = market.split(":", 1)
    if family == "1X2":
        bucket = odds.get("1X2", {})
        return bucket.get(selection), None
    if family == "OU":
        line, side = selection.split(":", 1)
        bucket = odds.get("OU25" if line == "2.5" else f"OU{line}", {})
        return bucket.get(side), None
    if family == "BTTS":
        bucket = odds.get("BTTS", {})
        return bucket.get(selection), None
    if family == "AH":
        bucket = odds.get("AH", {})
        key = selection.replace("+", "+").replace("-", "_")
        # Support both 'home_-1.5' and 'home_-1.5' formats
        for k, v in bucket.items():
            if k.lower().replace(" ", "") == selection.lower().replace(" ", ""):
                return v, None
        # Also match 'home_-1.5' against 'home_-1.5'
        alt = selection
        return bucket.get(alt), None
    return None, None