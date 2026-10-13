"""SQLite schema + helpers."""
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import DB_URL

Base = declarative_base()
engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, index=True)
    league = Column(String, index=True)
    home_team = Column(String)
    away_team = Column(String)
    kickoff = Column(DateTime)
    status = Column(String, default="SCHEDULED")
    home_goals = Column(Integer, nullable=True)
    away_goals = Column(Integer, nullable=True)
    home_xg = Column(Float, nullable=True)
    away_xg = Column(Float, nullable=True)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    market = Column(String, index=True)
    probability = Column(Float)
    fair_odds = Column(Float)
    best_odds = Column(Float, nullable=True)
    bookmaker = Column(String, nullable=True)
    ev = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    details_json = Column(Text, nullable=True)


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"
    id = Column(Integer, primary_key=True)
    match_external_id = Column(String, index=True)
    bookmaker = Column(String)
    market = Column(String)
    selection = Column(String)
    price = Column(Float)
    captured_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print("Database initialised at", DB_URL)