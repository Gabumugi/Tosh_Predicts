"""Fetch bookmaker odds. Uses The Odds API if a key is present, else mock."""
import httpx
from typing import Dict, List
from config import ODDS_API_BASE, ODDS_API_KEY, LEAGUES


MOCK_ODDS = {
    "EPL_M1":     {"1X2": {"1": 1.35, "X": 5.20, "2": 8.50}, "OU25": {"Over": 1.90, "Under": 1.90}, "BTTS": {"Yes": 2.10, "No": 1.72}, "AH": {"home_-1.5": 2.05, "away_+1.5": 1.75}},
    "EPL_M2":     {"1X2": {"1": 1.28, "X": 6.00, "2": 9.00}, "OU25": {"Over": 1.55, "Under": 2.40}, "BTTS": {"Yes": 1.80, "No": 2.00}, "AH": {"home_-1.5": 1.85, "away_+1.5": 1.95}},
    "BUND_M1":    {"1X2": {"1": 1.15, "X": 8.00, "2": 15.0}, "OU25": {"Over": 1.42, "Under": 2.80}, "BTTS": {"Yes": 1.75, "No": 2.05}, "AH": {"home_-2.5": 1.90, "away_+2.5": 1.90}},
    "LALIGA_M1":  {"1X2": {"1": 1.30, "X": 5.50, "2": 9.00}, "OU25": {"Over": 1.95, "Under": 1.85}, "BTTS": {"Yes": 2.20, "No": 1.65}, "AH": {"home_-1.5": 1.95, "away_+1.5": 1.85}},
    "SERIEA_M1":  {"1X2": {"1": 1.45, "X": 4.20, "2": 7.00}, "OU25": {"Over": 2.05, "Under": 1.75}, "BTTS": {"Yes": 2.05, "No": 1.75}, "AH": {"home_-1": 1.85, "away_+1": 1.95}},
    "LIGUE1_M1":  {"1X2": {"1": 1.20, "X": 6.50, "2": 12.0}, "OU25": {"Over": 1.60, "Under": 2.30}, "BTTS": {"Yes": 1.95, "No": 1.85}, "AH": {"home_-1.5": 1.70, "away_+1.5": 2.10}},
    "BRASIL_M1":  {"1X2": {"1": 1.80, "X": 3.40, "2": 4.20}, "OU25": {"Over": 2.10, "Under": 1.72}, "BTTS": {"Yes": 1.85, "No": 1.95}, "AH": {"home_-0.5": 1.85, "away_+0.5": 1.95}},
    "EPL_M3":     {"1X2": {"1": 1.55, "X": 4.20, "2": 5.50}, "OU25": {"Over": 1.65, "Under": 2.20}, "BTTS": {"Yes": 1.70, "No": 2.10}, "AH": {"home_-1": 2.05, "away_+1": 1.75}},
    "BUND_M2":    {"1X2": {"1": 1.75, "X": 3.80, "2": 4.30}, "OU25": {"Over": 1.55, "Under": 2.40}, "BTTS": {"Yes": 1.62, "No": 2.25}, "AH": {"home_-0.5": 1.95, "away_+0.5": 1.85}},
    "LALIGA_M2":  {"1X2": {"1": 1.40, "X": 4.50, "2": 7.00}, "OU25": {"Over": 1.70, "Under": 2.10}, "BTTS": {"Yes": 1.90, "No": 1.90}, "AH": {"home_-1.5": 2.15, "away_+1.5": 1.68}},
    "SERIEA_M2":  {"1X2": {"1": 2.05, "X": 3.30, "2": 3.60}, "OU25": {"Over": 2.30, "Under": 1.60}, "BTTS": {"Yes": 2.05, "No": 1.75}, "AH": {"home_-0.25": 1.90, "away_+0.25": 1.90}},
    "LIGUE1_M2":  {"1X2": {"1": 2.10, "X": 3.50, "2": 3.30}, "OU25": {"Over": 1.75, "Under": 2.05}, "BTTS": {"Yes": 1.80, "No": 2.00}, "AH": {"home_-0.25": 1.95, "away_+0.25": 1.85}},
}


class OddsClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or ODDS_API_KEY

    def fetch(self, league_key: str) -> List[dict]:
        if not self.api_key:
            return []
        league = LEAGUES[league_key]
        params = {
            "apiKey": self.api_key,
            "regions": "eu",
            "markets": "h2h,totals",
            "oddsFormat": "decimal",
        }
        url = f"{ODDS_API_BASE}/sports/{league['odds_key']}/odds"
        with httpx.Client(timeout=20.0) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            return r.json()


def load_odds(fixtures: List[dict], api_key: str | None = None) -> Dict[str, dict]:
    """Return dict: external_id -> {market -> {selection -> price}}.

    Real implementation should call The Odds API and match on team names.
    For the MVP we return MOCK_ODDS so the whole pipeline runs end-to-end.
    """
    if api_key:
        # TODO: implement real odds matching. Fall back to mock if matching fails.
        pass
    return {f["external_id"]: MOCK_ODDS.get(f["external_id"], {}) for f in fixtures}