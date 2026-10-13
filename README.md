# Tosh_Predicts

Value-betting signal engine for 6 leagues (EPL, Bundesliga, La Liga,
Serie A, Ligue 1, Brasileirão). Ranks the Top 10 highest expected-value
bets each day across all major markets.

## Architecture

- **Python engine** (FastAPI) — data ingest, Dixon-Coles model, market
  derivation, value gate, REST API.
- **PHP frontend** — dashboard that consumes the API.

## Quick start

### 1. Python engine

```bash
cd python_engine
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# optional: create a .env with real keys
cat > .env <<EOF
FOOTBALL_DATA_API_KEY=
ODDS_API_KEY=
EOF

uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload