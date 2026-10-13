"""FastAPI service that exposes the Tosh_Predicts engine."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

from config import MIN_PROBABILITY, MIN_EV, TOP_N, LEAGUES
from database import (
    SessionLocal, Match, Prediction, OddsSnapshot, init_db
)
from data_ingest.football_data import load_fixtures
from data_ingest.odds_fetcher import load_odds
from models.dixon_coles import DixonColesModel
from models.features import synthesise_history
from markets.market_engine import compute_all_markets, fair_odds
from engine.value_gate import find_value_signals
from engine.confidence import compute_confidence, label

app = FastAPI(title="Tosh_Predicts API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SignalOut(BaseModel):
    rank: int
    league: str
    league_name: str
    home_team: str
    away_team: str
    kickoff: str
    market: str
    probability: float
    fair_odds: float
    best_odds: Optional[float]
    bookmaker: Optional[str]
    ev: float
    confidence: float
    confidence_label: str


class MatchDetailOut(BaseModel):
    external_id: str
    league: str
    home_team: str
    away_team: str
    kickoff: str
    expected_goals: dict
    markets: dict


# ----------------------------------------------------------------
# In-memory cache (rebuilds on /refresh)
# ----------------------------------------------------------------
_CACHE = {"signals": [], "details": {}, "built_at": None}


def _build_model(fixtures):
    teams = sorted({f["home_team"] for f in fixtures} | {f["away_team"] for f in fixtures})
    history = synthesise_history(teams, matches_per_team=25)
    model = DixonColesModel(xi=0.0018, max_goals=8).fit(history)
    return model


def _build_predictions(model, fixtures):
    preds = []
    details = {}
    for f in fixtures:
        grid = model.score_grid(f["home_team"], f["away_team"])
        mkt = compute_all_markets(grid)
        details[f["external_id"]] = {
            "external_id": f["external_id"],
            "league": f["league"],
            "home_team": f["home_team"],
            "away_team": f["away_team"],
            "kickoff": f["kickoff"].isoformat() if hasattr(f["kickoff"], "isoformat") else str(f["kickoff"]),
            "expected_goals": dict(zip(
                ["home", "away"],
                [round(x, 2) for x in model.expected_goals(f["home_team"], f["away_team"])],
            )),
            "markets": {k: round(v, 4) for k, v in mkt.items()},
        }
        for market, p in mkt.items():
            if p < 0.01:
                continue
            preds.append({
                "match_external_id": f["external_id"],
                "market": market,
                "probability": p,
                "fair_odds": fair_odds(p),
            })
    return preds, details


def run_pipeline(force: bool = False):
    fixtures = load_fixtures()
    if not fixtures:
        return
    odds = load_odds(fixtures)
    model = _build_model(fixtures)
    preds, details = _build_predictions(model, fixtures)

    signals = find_value_signals(preds, odds, MIN_PROBABILITY, MIN_EV)
    # Take the top N globally, but enforce max 2 per match for diversity
    per_match = {}
    selected = []
    for sig in signals:
        ext = sig["match_external_id"]
        if per_match.get(ext, 0) >= 2:
            continue
        per_match[ext] = per_match.get(ext, 0) + 1
        selected.append(sig)
        if len(selected) >= TOP_N:
            break

    _CACHE["signals"] = selected
    _CACHE["details"] = details
    _CACHE["built_at"] = datetime.utcnow().isoformat()


@app.on_event("startup")
def startup():
    init_db()
    try:
        run_pipeline()
    except Exception as e:
        print("Initial pipeline failed:", e)


@app.get("/health")
def health():
    return {"status": "ok", "built_at": _CACHE["built_at"]}


@app.post("/refresh")
def refresh():
    run_pipeline(force=True)
    return {"status": "rebuilt", "signals": len(_CACHE["signals"]), "built_at": _CACHE["built_at"]}


@app.get("/top10", response_model=List[SignalOut])
def top10():
    out = []
    for i, sig in enumerate(_CACHE["signals"], start=1):
        det = _CACHE["details"].get(sig["match_external_id"], {})
        conf = compute_confidence(sig["probability"], sig["ev"], has_odds=sig["best_odds"] is not None)
        out.append(SignalOut(
            rank=i,
            league=det.get("league", ""),
            league_name=LEAGUES.get(det.get("league", ""), {}).get("name", ""),
            home_team=det.get("home_team", ""),
            away_team=det.get("away_team", ""),
            kickoff=det.get("kickoff", ""),
            market=sig["market"],
            probability=sig["probability"],
            fair_odds=sig["fair_odds"],
            best_odds=sig["best_odds"],
            bookmaker=sig["bookmaker"],
            ev=sig["ev"],
            confidence=conf,
            confidence_label=label(conf),
        ))
    return out


@app.get("/match/{external_id}", response_model=MatchDetailOut)
def match_detail(external_id: str):
    det = _CACHE["details"].get(external_id)
    if not det:
        raise HTTPException(status_code=404, detail="Match not found")
    return MatchDetailOut(**det)


@app.get("/leagues")
def leagues():
    return LEAGUES