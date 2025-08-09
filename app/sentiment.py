from __future__ import annotations

from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=1)
def _load_transformers_pipeline():
    try:
        from transformers import pipeline  # type: ignore

        return pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
        )
    except Exception:
        return None


def rule_based_sentiment(text: str) -> str:
    """Very small fallback sentiment function.

    Positive if contains words like: great, good, awesome, love, excellent
    Negative if: bad, rude, slow, terrible, awful
    Neutral otherwise.
    """
    if not text:
        return "neutral"
    t = text.lower()
    positive_keywords = ["great", "good", "awesome", "love", "excellent", "amazing", "friendly", "fast"]
    negative_keywords = ["bad", "rude", "slow", "terrible", "awful", "cold", "overcooked", "late"]
    if any(w in t for w in positive_keywords) and not any(w in t for w in negative_keywords):
        return "POSITIVE"
    if any(w in t for w in negative_keywords) and not any(w in t for w in positive_keywords):
        return "NEGATIVE"
    return "neutral"


def analyze_sentiment(text: str) -> str:
    """Try transformers; fallback to rule-based."""
    classifier = _load_transformers_pipeline()
    if classifier is None:
        return rule_based_sentiment(text)
    try:
        result = classifier(text)
        if isinstance(result, list) and result:
            label = result[0].get("label", "neutral")
            return label
        return "neutral"
    except Exception:
        return rule_based_sentiment(text)


__all__ = ["analyze_sentiment", "rule_based_sentiment"]


