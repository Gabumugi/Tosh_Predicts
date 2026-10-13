"""Central configuration for Tosh_Predicts engine."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tosh_predicts.db"
DB_URL = f"sqlite:///{DB_PATH}"

# API keys (put real values in .env)
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Leagues we track — code -> (name, football-data competition id, odds-api sport key)
LEAGUES = {
    "EPL":        {"name": "Premier League",   "fd_code": "PL",  "odds_key": "soccer_epl"},
    "BUNDESLIGA": {"name": "Bundesliga",       "fd_code": "BL1", "odds_key": "soccer_germany_bundesliga"},
    "LALIGA":     {"name": "La Liga",          "fd_code": "PD",  "odds_key": "soccer_spain_la_liga"},
    "SERIEA":     {"name": "Serie A",          "fd_code": "SA",  "odds_key": "soccer_italy_serie_a"},
    "LIGUE1":     {"name": "Ligue 1",          "fd_code": "FL1", "odds_key": "soccer_france_ligue_one"},
    "BRASILEIRAO":{"name": "Brasileirão Série A", "fd_code": "BSA", "odds_key": "soccer_brazil_campeonato"},
}

# Value-gate thresholds
MIN_PROBABILITY = 0.55   # ignore longshots
MIN_EV = 0.03            # require at least 3% expected value
TOP_N = 10               # return top 10 signals
BOOKMAKER_MARGIN_ESTIMATE = 0.05  # fallback margin for de-vig when only 1 book is available