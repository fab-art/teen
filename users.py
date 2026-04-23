"""
User authentication and authorization module.

Default user profiles can be overridden via secrets.toml:

[users.admin]
password = "your_password"
full_name = "Shop Owner"

[users.manager]
password = "your_password"
full_name = "Shop Manager"

[users.cashier1]
password = "your_password"
full_name = "Cashier One"
"""
import streamlit as st
from functools import lru_cache

# ── Default user profiles (overridden by secrets.toml if present) ──
DEFAULT_USERS = {
    "admin": {
        "password": "admin123",
        "full_name": "Shop Owner",
        "role": "admin",
    },
    "manager": {
        "password": "manager123",
        "full_name": "Shop Manager",
        "role": "manager",
    },
    "cashier": {
        "password": "cashier123",
        "full_name": "Cashier",
        "role": "cashier",
    },
}

# ── Permission mapping ───────────────────────────────────────────
PERMISSIONS = {
    # POS
    "place_orders": ["admin", "manager", "cashier"],
    # Inventory
    "view_inventory": ["admin", "manager"],
    "receive_stock": ["admin", "manager"],
    "adjust_inventory": ["admin"],
    "edit_prices": ["admin", "manager"],
    "manage_catalog": ["admin"],
    # Orders
    "view_orders": ["admin", "manager", "cashier"],
    "edit_orders": ["admin", "manager"],
    "void_lines": ["admin", "manager"],
    # Finance
    "view_finance": ["admin", "manager"],
    "view_profit": ["admin"],
    "log_expenses": ["admin", "manager"],
    "void_expenses": ["admin"],
    "manage_payables": ["admin", "manager"],
    # Users / Audit
    "view_audit": ["admin", "manager"],
    "manage_users": ["admin"],
}


def get_users() -> dict:
    """Merge default users with any overrides in secrets.toml [users.*]"""
    users = {k: dict(v) for k, v in DEFAULT_USERS.items()}
    try:
        secret_users = st.secrets.get("users", {})
        for username, overrides in secret_users.items():
            if username in users:
                users[username].update(overrides)
            else:
                users[username] = dict(overrides)
    except Exception:
        pass
    return users


def authenticate(username: str, password: str) -> dict | None:
    """Authenticate user credentials.
    
    Args:
        username: User's username
        password: User's password
    
    Returns:
        User dict if valid, None otherwise.
    """
    users = get_users()
    u = users.get(username.lower().strip())
    if u and password == u["password"]:
        return {"username": username.lower().strip(), **u}
    return None


def can(action: str) -> bool:
    """Check if current user has permission for an action."""
    role = st.session_state.get("role", "")
    return role in PERMISSIONS.get(action, [])


def current_role() -> str:
    """Get current user's role."""
    return st.session_state.get("role", "")


def current_user() -> dict | None:
    """Get current user dict from session state."""
    return st.session_state.get("user")


def require_auth():
    """Require authentication - redirect to login if not authenticated."""
    if not current_user():
        st.switch_page("Home.py")
        st.stop()


def require_permission(action: str):
    """Require specific permission - show error if unauthorized."""
    require_auth()
    if not can(action):
        st.error("Access restricted. You don't have permission for this section.")
        st.stop()


def logout():
    """Clear session and redirect to login page."""
    for k in ["user", "role", "full_name", "username"]:
        st.session_state.pop(k, None)
    st.switch_page("Home.py")
    st.stop()
