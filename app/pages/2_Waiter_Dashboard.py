from __future__ import annotations

import streamlit as st
import pandas as pd

from utils import load_waiters, load_tips
from app import waiter_summary


st.set_page_config(page_title="TipTrack · Waiter", page_icon="🍽️", layout="wide")
st.title("Waiter Dashboard")

waiters_df = load_waiters()
tips_df = load_tips()

waiter_map = {row.waiter_id: row.name for row in waiters_df.itertuples()}
selected = st.selectbox("Choose waiter", list(waiter_map.keys()))
summary = waiter_summary(tips_df, selected)
col1, col2, col3 = st.columns(3)
col1.metric("Total Tips", f"{summary['total_tips']:.2f}")
col2.metric("Average Rating", f"{summary['avg_rating']:.2f}")
col3.metric("Number of Tips", f"{summary['num_tips']}")

st.markdown("### Recent Feedback")
rf = summary["recent_feedback"]
if isinstance(rf, pd.DataFrame) and not rf.empty:
    st.dataframe(rf, use_container_width=True, hide_index=True)
else:
    st.info("No feedback yet.")


