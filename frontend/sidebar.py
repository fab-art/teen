"""
sidebar.py — call render_sidebar() at the top of every page.
Builds the persistent nav panel, respects role-based visibility.

Uses st.button + st.switch_page instead of st.page_link to avoid
a KeyError on page_data["url_pathname"] that occurs in newer Streamlit
versions when the PagesManager hasn't fully registered pages yet.
"""
import streamlit as st
import os
from users import can, current_role, current_user, logout
from styles import badge

# Nav items: (label, icon, page_file, required_permission_or_None)
NAV_ITEMS = [
    ("Dashboard",  "◈", "Home.py",               None),
    ("POS",        "◉", "pages/1_POS.py",         "place_orders"),
    ("Inventory",  "◫", "pages/2_Inventory.py",   "view_inventory"),
    ("Orders",     "◎", "pages/3_Orders.py",      "view_orders"),
    ("Finance",    "◑", "pages/4_Finance.py",     "view_finance"),
    ("Audit Log",  "◌", "pages/5_Audit_Log.py",   "view_audit"),
]

ROLE_BADGE = {
    "admin":   ("admin",   "Administrator"),
    "manager": ("manager", "Manager"),
    "cashier": ("cashier", "Cashier"),
}

def render_sidebar():
    st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: #f5f3ee !important;
    border-right: 1px solid rgba(0,0,0,0.07) !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

/* Nav buttons */
[data-testid="stSidebar"] [data-testid="stButton"] button {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 4px !important;
    color: #4a4640 !important;
    font-size: 12.5px !important;
    font-family: Jost, sans-serif !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
    text-align: left !important;
    padding: 9px 12px !important;
    margin: 2px 10px !important;
    width: calc(100% - 20px) !important;
    transition: background .15s, color .15s !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background: rgba(0,0,0,0.04) !important;
    border-color: transparent !important;
    color: #1a1612 !important;
}
/* Active nav button */
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
    background: rgba(184,137,10,0.09) !important;
    border-color: rgba(184,137,10,0.25) !important;
    color: #b8890a !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"]:hover {
    background: rgba(184,137,10,0.14) !important;
    color: #b8890a !important;
}
/* Sign-out button override */
[data-testid="stSidebar"] [data-testid="stButton"]:last-of-type button {
    border-color: rgba(232,224,204,0.1) !important;
    color: #847e76 !important;
    font-size: 11.5px !important;
    letter-spacing: .05em !important;
}
[data-testid="stSidebar"] [data-testid="stButton"]:last-of-type button:hover {
    border-color: rgba(192,57,43,0.4) !important;
    color: #c0392b !important;
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

    with st.sidebar:
        # ── Brand ─────────────────────────────────────────────
        st.markdown("""
<div style="padding:22px 20px 16px;border-bottom:1px solid rgba(0,0,0,0.07);margin-bottom:4px">
  <div style="font-family:'Playfair Display',serif;font-size:22px;font-weight:600;color:#b8890a;letter-spacing:.06em;line-height:1">Duka</div>
  <div style="font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:#847e76;margin-top:3px">Shop Management</div>
</div>""", unsafe_allow_html=True)

        # ── User info ──────────────────────────────────────────
        user = current_user()
        if user:
            role = current_role()
            bs, blabel = ROLE_BADGE.get(role, ("neutral", role))
            st.markdown(f"""
<div style="padding:10px 20px 12px;border-bottom:1px solid rgba(0,0,0,0.07);margin-bottom:8px">
  <div style="font-size:12.5px;color:#1a1612;font-family:Jost,sans-serif;margin-bottom:4px">{user.get('full_name','User')}</div>
  {badge(blabel, bs)}
</div>""", unsafe_allow_html=True)

        # ── Navigation ─────────────────────────────────────────
        # Determine the currently active page to highlight it
        try:
            current_script = st.context.pages.get("current", {}).get("script_path", "")
        except Exception:
            current_script = ""

        for label, icon, page, perm in NAV_ITEMS:
            if perm and not can(perm):
                continue
            # Highlight the active page button
            try:
                is_active = os.path.basename(current_script) == os.path.basename(page)
            except Exception:
                is_active = False
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True, type=btn_type):
                st.switch_page(page)

        # ── Sign out ───────────────────────────────────────────
        st.markdown("<div style='margin-top:16px;border-top:1px solid rgba(0,0,0,0.07);padding-top:12px'>", unsafe_allow_html=True)
        if st.button("Sign Out", key="sidebar_signout", use_container_width=True):
            logout()
        st.markdown("</div>", unsafe_allow_html=True)
