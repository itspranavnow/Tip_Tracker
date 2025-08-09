from __future__ import annotations

from typing import Tuple

import streamlit as st


def get_credentials() -> dict:
    """Demo credentials. In production load from env/secret file.

    Users:
      - owner / ownerpass (Owner)
      - admin / adminpass (Admin)
      - waiter1..waiter3 / waiterpass (Waiter)
    """
    # Minimal embedded credentials (plain text, for demo only)
    return {
        "usernames": {
            "owner": {"name": "Owner", "password": "ownerpass", "role": "owner"},
            "admin": {"name": "Admin", "password": "adminpass", "role": "admin"},
            "waiter1": {"name": "Waiter 1", "password": "waiterpass", "role": "waiter"},
            "waiter2": {"name": "Waiter 2", "password": "waiterpass", "role": "waiter"},
            "waiter3": {"name": "Waiter 3", "password": "waiterpass", "role": "waiter"},
        }
    }


def login_widget() -> Tuple[bool, str, str]:
    creds = get_credentials()["usernames"]
    # Case-insensitive username lookup
    creds_ci = {k.lower(): v for k, v in creds.items()}
    st.subheader("Login")
    st.caption("Demo users: owner/ownerpass, admin/adminpass, waiter1..3/waiterpass")
    with st.form("login_form", clear_on_submit=False):
        user = st.text_input("Username", key="auth_user_input")
        pwd = st.text_input("Password", type="password", key="auth_pwd_input")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        user_key = (user or "").strip().lower()
        if user_key in creds_ci and creds_ci[user_key]["password"] == pwd:
            st.session_state["auth_user"] = user_key
            st.session_state["auth_name"] = creds_ci[user_key]["name"]
            st.session_state["auth_role"] = creds_ci[user_key]["role"]
            st.success("Logged in")
            try:
                if callable(getattr(st, "rerun", None)):
                    st.rerun()  # type: ignore[attr-defined]
                else:
                    st.experimental_rerun()  # type: ignore[attr-defined]
            except Exception:
                pass
        else:
            st.error("Invalid credentials")
    auth_ok = "auth_user" in st.session_state
    return auth_ok, st.session_state.get("auth_name", ""), st.session_state.get("auth_user", "")


def logout():
    for k in ["auth_user", "auth_name", "auth_role"]:
        if k in st.session_state:
            del st.session_state[k]
    try:
        if callable(getattr(st, "rerun", None)):
            st.rerun()  # type: ignore[attr-defined]
        else:
            st.experimental_rerun()  # type: ignore[attr-defined]
    except Exception:
        pass


def require_role(allowed_roles: set[str]) -> Tuple[bool, str, str]:
    # If already logged in
    if "auth_user" in st.session_state:
        username = st.session_state.get("auth_user", "")
        role = st.session_state.get("auth_role", "")
        name = st.session_state.get("auth_name", "")
        # Show status and logout in sidebar
        with st.sidebar:
            st.caption(f"Signed in as {name} ({role})")
            if st.button("Logout", key="logout_btn"):
                logout()
        if role in allowed_roles:
            return True, name, username
        # Wrong role, allow switching account
        st.warning("You do not have access to this page with the current account.")
        if st.button("Switch account", key="switch_account"):
            logout()
        # Show login form to switch
        auth_ok, name, username = login_widget()
        if not auth_ok:
            st.stop()
        role = st.session_state.get("auth_role", "")
        if role not in allowed_roles:
            st.error("You do not have access to this page.")
            st.stop()
        return True, name, username

    # Not logged in yet
    auth_ok, name, username = login_widget()
    if not auth_ok:
        st.stop()
    role = st.session_state.get("auth_role", "")
    if role not in allowed_roles:
        st.error("You do not have access to this page.")
        st.stop()
    return True, name, username


__all__ = ["require_role", "login_widget"]


