from __future__ import annotations

import streamlit as st

from utils import load_waiters
from components import ensure_waiter_qr
from auth import require_role


st.set_page_config(page_title="TipTrack · Admin", page_icon="🔐", layout="wide")
st.title("Admin · Waiter QR Codes")

# Auth: admin only
require_role({"admin"})

base_url = st.text_input("App base URL", value="http://localhost:8501/")
st.caption("Each QR links to the app with the waiter preselected (via query param).")

waiters_df = load_waiters()
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


