"""Fetch fixtures, results, and team form from football-data.org."""
import httpx
from datetime import datetime, timedelta
from typing import List, Dict
from config import FOOTBALL_DATA_BASE, FOOTBALL_DATA_API_KEY, LEAGUES


class FootballDataClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or FOOTBALL_DATA_API_KEY
        self.headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{FOOTBALL_DATA_BASE}{path}"
        with httpx.Client(timeout=20.0) as client:
            r = client.get(url, headers=self.headers, params=params or {})
            r.raise_for_status()
            return r.json()

    def upcoming_fixtures(self, league_key: str, days_ahead: int = 3) -> List[Dict]:
        league = LEAGUES[league_key]
        date_from = datetime.utcnow().date().isoformat()
        date_to = (datetime.utcnow() + timedelta(days=days_ahead)).date().isoformat()
        data = self._get(
            f"/competitions/{league['fd_code']}/matches",
            {"dateFrom": date_from, "dateTo": date_to, "status": "SCHEDULED"},
        )
        return data.get("matches", [])

    def finished_matches(self, league_key: str, season: int | None = None) -> List[Dict]:
        league = LEAGUES[league_key]
        params = {"status": "FINISHED"}
        if season:
            params["season"] = season
        data = self._get(f"/competitions/{league['fd_code']}/matches", params)
        return data.get("matches", [])

    def normalise(self, raw: dict, league_key: str) -> dict:
        """Flatten a raw football-data match into our storage format."""
        score = raw.get("score", {}).get("fullTime", {}) or {}
        return {
            "external_id": f"{league_key}_{raw['id']}",
            "league": league_key,
            "home_team": raw["homeTeam"]["name"],
            "away_team": raw["awayTeam"]["name"],
            "kickoff": datetime.fromisoformat(raw["utcDate"].replace("Z", "+00:00")),
            "status": raw.get("status", "SCHEDULED"),
            "home_goals": score.get("home"),
            "away_goals": score.get("away"),
        }


# ---------- Mock fallback so the app runs without an API key ----------
MOCK_FIXTURES = [
    {"external_id": "EPL_M1", "league": "EPL", "home_team": "Arsenal", "away_team": "Everton",
     "kickoff": datetime.utcnow() + timedelta(hours=6), "status": "SCHEDULED"},
    {"external_id": "EPL_M2", "league": "EPL", "home_team": "Man City", "away_team": "Brighton",
     "kickoff": datetime.utcnow() + timedelta(hours=8), "status": "SCHEDULED"},
    {"external_id": "BUND_M1", "league": "BUNDESLIGA", "home_team": "Bayern Munich", "away_team": "Freiburg",
     "kickoff": datetime.utcnow() + timedelta(hours=5), "status": "SCHEDULED"},
    {"external_id": "LALIGA_M1", "league": "LALIGA", "home_team": "Real Madrid", "away_team": "Getafe",
     "kickoff": datetime.utcnow() + timedelta(hours=7), "status": "SCHEDULED"},
    {"external_id": "SERIEA_M1", "league": "SERIEA", "home_team": "Inter", "away_team": "Torino",
     "kickoff": datetime.utcnow() + timedelta(hours=9), "status": "SCHEDULED"},
    {"external_id": "LIGUE1_M1", "league": "LIGUE1", "home_team": "PSG", "away_team": "Nantes",
     "kickoff": datetime.utcnow() + timedelta(hours=10), "status": "SCHEDULED"},
    {"external_id": "BRASIL_M1", "league": "BRASILEIRAO", "home_team": "Flamengo", "away_team": "Palmeiras",
     "kickoff": datetime.utcnow() + timedelta(hours=11), "status": "SCHEDULED"},
    {"external_id": "EPL_M3", "league": "EPL", "home_team": "Liverpool", "away_team": "Newcastle",
     "kickoff": datetime.utcnow() + timedelta(hours=12), "status": "SCHEDULED"},
    {"external_id": "BUND_M2", "league": "BUNDESLIGA", "home_team": "Dortmund", "away_team": "Stuttgart",
     "kickoff": datetime.utcnow() + timedelta(hours=13), "status": "SCHEDULED"},
    {"external_id": "LALIGA_M2", "league": "LALIGA", "home_team": "Barcelona", "away_team": "Sevilla",
     "kickoff": datetime.utcnow() + timedelta(hours=14), "status": "SCHEDULED"},
    {"external_id": "SERIEA_M2", "league": "SERIEA", "home_team": "Juventus", "away_team": "Napoli",
     "kickoff": datetime.utcnow() + timedelta(hours=15), "status": "SCHEDULED"},
    {"external_id": "LIGUE1_M2", "league": "LIGUE1", "home_team": "Marseille", "away_team": "Lyon",
     "kickoff": datetime.utcnow() + timedelta(hours=16), "status": "SCHEDULED"},
]


def load_fixtures(api_key: str | None = None, use_mock: bool = True) -> List[dict]:
    """Return upcoming fixtures across all tracked leagues."""
    if not api_key:
        if use_mock:
            return MOCK_FIXTURES
        return []

    client = FootballDataClient(api_key)
    fixtures = []
    for league_key in LEAGUES:
        try:
            raw = client.upcoming_fixtures(league_key)
            fixtures.extend(client.normalise(m, league_key) for m in raw)
        except Exception as e:
            print(f"[football_data] {league_key} failed: {e}")
    return fixtures or (MOCK_FIXTURES if use_mock else [])