from __future__ import annotations

import streamlit as st
import pandas as pd

from utils import load_waiters, append_tip
from sentiment import analyze_sentiment
from app import read_query_params  # reuse helper


st.set_page_config(page_title="TipTrack · Customer", page_icon="💸", layout="wide")
st.title("Customer")

waiters_df = load_waiters()

qp = read_query_params()
default_waiter_id = qp.get("waiter_id")
if isinstance(default_waiter_id, list):
    default_waiter_id = default_waiter_id[0]

with st.container():
    waiter_names = {row.waiter_id: f"{row.name} ({row.waiter_id})" for row in waiters_df.itertuples()}
    waiter_choices = ["-- Select waiter --"] + list(waiter_names.keys())
    idx_default = 0
    if default_waiter_id in waiter_names:
        idx_default = waiter_choices.index(default_waiter_id)
    selected_waiter = st.selectbox("Waiter", waiter_choices, index=idx_default)
    if selected_waiter != "-- Select waiter --":
        amount = st.number_input("Tip amount", min_value=0.0, step=0.5, format="%.2f")
        rating = st.slider("Rating", min_value=1, max_value=5, value=5)
        feedback = st.text_area("Optional feedback")
        if st.button("Submit Tip"):
            sentiment = analyze_sentiment(feedback)
            append_tip(selected_waiter, amount, rating, feedback, sentiment)
            st.success("Thank you! Your tip and feedback were recorded.")
    else:
        st.info("Pick the waiter (or use QR).")



