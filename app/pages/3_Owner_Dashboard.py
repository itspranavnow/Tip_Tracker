from __future__ import annotations

import streamlit as st
import pandas as pd

from utils import load_waiters, load_tips
from auth import require_role


st.set_page_config(page_title="TipTrack · Owner", page_icon="📊", layout="wide")
st.title("Owner Dashboard")

# Auth: owner only
require_role({"owner"})

waiters_df = load_waiters()
tips_df = load_tips()

if tips_df.empty:
    st.info("No tips yet.")
else:
    agg = tips_df.groupby("waiter_id").agg(
        total_tips=("amount", "sum"),
        avg_rating=("rating", "mean"),
        num_tips=("rating", "count"),
    ).reset_index()
    agg["waiter_name"] = agg["waiter_id"].map({w.waiter_id: w.name for w in waiters_df.itertuples()})
    agg = agg.sort_values("total_tips", ascending=False)

    st.markdown("#### Tips by Waiter")
    st.bar_chart(agg.set_index("waiter_name")["total_tips"])

    st.markdown("#### Average Rating by Waiter")
    st.bar_chart(agg.set_index("waiter_name")["avg_rating"])

    st.markdown("### Recent Feedback Stream")
    feed_cols = ["timestamp", "waiter_id", "amount", "rating", "feedback", "sentiment"]
    feed = tips_df[feed_cols].copy().sort_values("timestamp", ascending=False).head(25)
    feed["waiter_name"] = feed["waiter_id"].map({w.waiter_id: w.name for w in waiters_df.itertuples()})
    st.dataframe(feed, use_container_width=True, hide_index=True)


