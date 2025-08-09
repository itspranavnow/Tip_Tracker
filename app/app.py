from __future__ import annotations

import html
import urllib.parse
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from utils import (
    DATA_DIR,
    WAITERS_CSV,
    TIPS_CSV,
    QRCODES_DIR,
    load_waiters,
    load_tips,
    append_tip,
    waiter_summary,
)
from sentiment import analyze_sentiment
from components import ensure_waiter_qr


st.set_page_config(page_title="TipTrack", page_icon="💸", layout="wide")


def inject_styles():
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def read_query_params() -> dict:
    try:
        return st.query_params.to_dict()
    except Exception:
        # streamlit < 1.32 fallback
        return st.experimental_get_query_params()


def app_header():
    st.title("TipTrack 💸")
    st.caption("Digitize tips and feedback for restaurant waiters. Local CSV storage.")


def ensure_data_ready():
    # If CSVs missing, guide the user to run generate script
    if not WAITERS_CSV.exists() or not TIPS_CSV.exists():
        st.warning(
            "Data files not found. Click the button below to generate synthetic data (6 waiters)."
        )
        if st.button("Generate data now"):
            # Import lazily to avoid circular; use absolute import so script runs outside a package
            from generate_data import main as generate_main

            generate_main()
            # Safely rerun only when under Streamlit runtime
            try:
                # Newer API
                if callable(getattr(st, "rerun", None)):
                    st.rerun()  # type: ignore[attr-defined]
                else:
                    # Older API
                    st.experimental_rerun()  # type: ignore[attr-defined]
            except Exception:
                # If not in a Streamlit session (e.g., python app/app.py), just continue
                pass


def tab_customer(waiters_df: pd.DataFrame, tips_df: pd.DataFrame):
    st.subheader("Customer")
    qp = read_query_params()
    default_waiter_id = qp.get("waiter_id")
    if isinstance(default_waiter_id, list):
        default_waiter_id = default_waiter_id[0]

    col1, col2 = st.columns([2, 1])
    with col1:
        waiter_names = {row.waiter_id: f"{row.name} ({row.waiter_id})" for row in waiters_df.itertuples()}
        waiter_choices = ["-- Select waiter --"] + list(waiter_names.keys())
        idx_default = 0
        if default_waiter_id in waiter_names:
            idx_default = waiter_choices.index(default_waiter_id)
        selected_waiter = st.selectbox("Waiter", waiter_choices, index=idx_default)
        if selected_waiter == "-- Select waiter --":
            st.info("Pick the waiter (or scan QR that encodes this selection).")
            return

        amount = st.number_input("Tip amount (in your currency)", min_value=0.0, step=0.5, format="%.2f")
        rating = st.slider("Rating", min_value=1, max_value=5, value=5)
        feedback = st.text_area("Optional feedback")

        if st.button("Submit Tip"):
            sentiment = analyze_sentiment(feedback)
            append_tip(selected_waiter, amount, rating, feedback, sentiment)
            st.success("Thank you! Your tip and feedback were recorded.")

    with col2:
        # Quick stats for selected waiter
        if selected_waiter != "-- Select waiter --":
            summary = waiter_summary(load_tips(), selected_waiter)
            st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
            st.metric("Total Tips", f"{summary['total_tips']:.2f}")
            st.metric("Average Rating", f"{summary['avg_rating']:.2f}")
            st.metric("Number of Tips", f"{summary['num_tips']}")
            st.markdown("</div>", unsafe_allow_html=True)


def tab_waiter_dashboard(waiters_df: pd.DataFrame, tips_df: pd.DataFrame):
    st.subheader("Waiter Dashboard")
    waiter_map = {row.waiter_id: row.name for row in waiters_df.itertuples()}
    selected = st.selectbox("Choose waiter", list(waiter_map.keys()))
    summary = waiter_summary(tips_df, selected)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Tips", f"{summary['total_tips']:.2f}")
    c2.metric("Average Rating", f"{summary['avg_rating']:.2f}")
    c3.metric("Number of Tips", f"{summary['num_tips']}")

    st.markdown("### Recent Feedback")
    if isinstance(summary["recent_feedback"], pd.DataFrame) and not summary["recent_feedback"].empty:
        for row in summary["recent_feedback"].itertuples():
            sent = str(row.sentiment).upper()
            css = "sent-neu"
            if sent.startswith("POS"):
                css = "sent-pos"
            elif sent.startswith("NEG"):
                css = "sent-neg"
            st.markdown(
                f"<div class='feedback-card'><b>{row.timestamp}</b> — "
                f"<span class='{css}'>{row.sentiment}</span><br>"
                f"{html.escape(str(row.feedback))}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No feedback yet.")


def tab_owner_dashboard(waiters_df: pd.DataFrame, tips_df: pd.DataFrame):
    st.subheader("Owner Dashboard")
    if tips_df.empty:
        st.info("No tips yet.")
        return

    # Aggregate by waiter
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


def tab_admin_qr(waiters_df: pd.DataFrame):
    st.subheader("Admin · Waiter QR Codes")
    base_url = st.text_input("App base URL", value="http://localhost:8501/")
    st.caption("Each QR links to the app with the waiter preselected (via query param).")

    cols = st.columns(3)
    for idx, row in enumerate(waiters_df.itertuples(), start=0):
        waiter_id = row.waiter_id
        with cols[idx % 3]:
            img_path = ensure_waiter_qr(base_url, waiter_id)
            st.image(str(img_path), caption=f"{row.name} ({waiter_id})", use_column_width=True)
            with open(img_path, "rb") as f:
                st.download_button(
                    "Download PNG",
                    data=f.read(),
                    file_name=img_path.name,
                    mime="image/png",
                )


def main():
    inject_styles()
    app_header()
    ensure_data_ready()

    waiters_df = load_waiters()
    tips_df = load_tips()

    st.info("Use the page sidebar to navigate: Customer, Waiter Dashboard, Owner Dashboard, Admin QR.")
    st.markdown("- Customer: submit tips and feedback")
    st.markdown("- Waiter Dashboard: personal stats and feedback")
    st.markdown("- Owner Dashboard: aggregate metrics (login required)")
    st.markdown("- Admin QR: generate QR codes (login required)")


if __name__ == "__main__":
    main()


