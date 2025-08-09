from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


# Paths
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WAITERS_CSV = DATA_DIR / "waiters.csv"
TIPS_CSV = DATA_DIR / "tips.csv"
QRCODES_DIR = DATA_DIR / "qrcodes"
QRCODES_DIR.mkdir(parents=True, exist_ok=True)


def _empty_waiters_df() -> pd.DataFrame:
    return pd.DataFrame(columns=["waiter_id", "name", "phone"])


def _empty_tips_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "timestamp",
            "waiter_id",
            "amount",
            "rating",
            "feedback",
            "sentiment",
        ]
    )


def load_waiters() -> pd.DataFrame:
    """Load waiters from CSV. Returns empty DataFrame if missing."""
    if not WAITERS_CSV.exists():
        return _empty_waiters_df()
    try:
        df = pd.read_csv(WAITERS_CSV, dtype=str)
        # Normalize columns
        expected = ["waiter_id", "name", "phone"]
        for col in expected:
            if col not in df.columns:
                df[col] = ""
        return df[expected]
    except Exception:
        return _empty_waiters_df()


def load_tips() -> pd.DataFrame:
    """Load tips from CSV. Returns empty DataFrame if missing."""
    if not TIPS_CSV.exists():
        return _empty_tips_df()
    try:
        df = pd.read_csv(TIPS_CSV)
        # Coerce dtypes
        if "amount" in df.columns:
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
        if "rating" in df.columns:
            df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0).astype(int)
        for col in ["timestamp", "waiter_id", "feedback", "sentiment"]:
            if col not in df.columns:
                df[col] = ""
        return df[["timestamp", "waiter_id", "amount", "rating", "feedback", "sentiment"]]
    except Exception:
        return _empty_tips_df()


def append_tip(waiter_id: str, amount: float, rating: int, feedback: str, sentiment: str) -> None:
    """Append a tip entry to CSV, creating file with headers if needed."""
    TIPS_CSV.parent.mkdir(parents=True, exist_ok=True)
    exists = TIPS_CSV.exists()
    with TIPS_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "waiter_id",
                "amount",
                "rating",
                "feedback",
                "sentiment",
            ],
        )
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "waiter_id": waiter_id,
                "amount": float(amount),
                "rating": int(rating),
                "feedback": (feedback or "").strip(),
                "sentiment": sentiment or "",
            }
        )


def waiter_summary(df_tips: pd.DataFrame, waiter_id: str, recent_n: int = 10) -> Dict[str, object]:
    """Compute summary stats and recent feedback for one waiter."""
    if df_tips.empty:
        return {
            "total_tips": 0.0,
            "avg_rating": 0.0,
            "num_tips": 0,
            "recent_feedback": _empty_tips_df(),
        }
    sub = df_tips[df_tips["waiter_id"] == waiter_id].copy()
    if sub.empty:
        return {
            "total_tips": 0.0,
            "avg_rating": 0.0,
            "num_tips": 0,
            "recent_feedback": _empty_tips_df(),
        }
    total_tips = round(float(sub["amount"].sum()), 2)
    avg_rating = float(sub["rating"].mean()) if not sub["rating"].empty else 0.0
    num_tips = int(sub.shape[0])
    sub = sub.sort_values("timestamp", ascending=False).head(recent_n)
    return {
        "total_tips": total_tips,
        "avg_rating": avg_rating,
        "num_tips": num_tips,
        "recent_feedback": sub[["timestamp", "feedback", "sentiment", "amount", "rating"]],
    }


__all__ = [
    "DATA_DIR",
    "WAITERS_CSV",
    "TIPS_CSV",
    "QRCODES_DIR",
    "load_waiters",
    "load_tips",
    "append_tip",
    "waiter_summary",
]


