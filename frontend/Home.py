import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from styles import inject, kpi, section_title, fmt, divider, table_html
from users import authenticate, current_user, current_role, can

st.set_page_config(page_title="Duka ERP", page_icon="🪟", layout="wide", initial_sidebar_state="expanded")
inject()

# ════════════════════════════════════════════════════════════
# LOGIN SCREEN
# ════════════════════════════════════════════════════════════
if not current_user():
    # Hide sidebar on login screen
    st.markdown("<style>[data-testid='stSidebar']{display:none!important}</style>", unsafe_allow_html=True)

    st.markdown("""
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div style="width:100%;max-width:380px;padding:0 16px">
    <div style="text-align:center;margin-bottom:36px">
      <div style="font-family:Playfair Display,serif;font-size:48px;font-weight:600;color:#b8890a;letter-spacing:.06em;line-height:1">Duka</div>
      <div style="font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:#847e76;margin-top:6px">Shop Management System</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    # Centre the form
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login", clear_on_submit=False):
            st.markdown('<div style="margin-bottom:4px"><h3>Sign in</h3></div>', unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="admin / manager / cashier")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Enter username and password.")
            else:
                user = authenticate(username, password)
                if user:
                    st.session_state.user      = user
                    st.session_state.role      = user["role"]
                    st.session_state.full_name = user["full_name"]
                    st.session_state.username  = user["username"]
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        # Show hint
        st.markdown("""
<div style="margin-top:16px;background:rgba(184,137,10,0.06);border:1px solid rgba(184,137,10,0.18);border-radius:6px;padding:12px 14px;font-size:11px;color:#847e76;line-height:1.8">
  Default accounts:<br>
  <span style="font-family:DM Mono,monospace;color:#4a4640">admin</span> / <span style="font-family:DM Mono,monospace;color:#4a4640">admin123</span><br>
  <span style="font-family:DM Mono,monospace;color:#4a4640">manager</span> / <span style="font-family:DM Mono,monospace;color:#4a4640">manager123</span><br>
  <span style="font-family:DM Mono,monospace;color:#4a4640">cashier</span> / <span style="font-family:DM Mono,monospace;color:#4a4640">cashier123</span>
</div>""", unsafe_allow_html=True)
    st.stop()

# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════
from sidebar import render_sidebar
render_sidebar()

# ════════════════════════════════════════════════════════════
# DASHBOARD — content varies by role
# ════════════════════════════════════════════════════════════
from db import get_sb, fmt_dt

sb   = get_sb()
role = current_role()
name = st.session_state.get("full_name", "User")

section_title("Dashboard", f"Welcome back, {name}")

# ── Quick-access navigation ───────────────────────────────────
NAV_CARDS = [
    ("◉", "Point of Sale",  "Create new orders",            "pages/1_POS.py",       "place_orders"),
    ("◫", "Inventory",      "Stock levels & inward",         "pages/2_Inventory.py", "view_inventory"),
    ("◎", "Orders",         "Manage & track all orders",     "pages/3_Orders.py",    "view_orders"),
    ("◑", "Finance",        "Revenue, expenses & payables",  "pages/4_Finance.py",   "view_finance"),
    ("◌", "Audit Log",      "Immutable change record",       "pages/5_Audit_Log.py", "view_audit"),
]
visible = [(ic, lb, ds, pg) for ic, lb, ds, pg, perm in NAV_CARDS if can(perm)]
if visible:
    st.markdown('<div class="nav-cards">', unsafe_allow_html=True)
    cols = st.columns(len(visible), gap="small")
    for col, (icon, label, desc, page) in zip(cols, visible):
        with col:
            if st.button(f"{icon}\n{label}\n{desc}", key=f"navcard_{label}", use_container_width=True):
                st.switch_page(page)
    st.markdown('</div>', unsafe_allow_html=True)

divider()

# ── Shared data fetches ───────────────────────────────────────
orders   = sb.table("sales_orders").select("order_id,total_amount,deposit_paid,balance_due,status,customer_name,created_at").order("created_at", desc=True).limit(200).execute().data
catalog  = sb.table("catalog").select("item_id,name,uom,stock_on_hand:current_landed_cost,default_sell_price").execute().data if role == "cashier" else []

# ════════════════════════════════════════════════════════════
# ADMIN DASHBOARD — full company metrics
# ════════════════════════════════════════════════════════════
if role == "admin":
    lines    = sb.table("order_lines").select("line_cogs").execute().data
    expenses = sb.table("expenses").select("amount,category").execute().data
    inv_data = sb.table("catalog").select("item_id,current_landed_cost").execute().data
    led_data = sb.table("inventory_ledger").select("item_id,quantity_change").execute().data

    # Calculations
    revenue   = sum(o["total_amount"] for o in orders if o["status"] != "Cancelled")
    cogs      = sum(l["line_cogs"] for l in lines)
    total_exp = sum(e["amount"] for e in expenses)
    gross     = revenue - cogs
    net       = gross - total_exp
    balance   = sum(o["balance_due"] for o in orders if o["status"] not in ["Cancelled","Delivered"])
    pending   = sum(1 for o in orders if o["status"] == "Pending")

    # Inventory value
    totals = {}
    for r in led_data:
        totals[r["item_id"]] = totals.get(r["item_id"], 0) + r["quantity_change"]
    inv_value = sum(max(totals.get(c["item_id"],0),0) * c["current_landed_cost"] for c in inv_data)

    # Row 1 — Core P&L
    st.markdown('<h3>Profit & Loss</h3>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi("Gross Revenue",    fmt(revenue), "gold"),    unsafe_allow_html=True)
    with c2: st.markdown(kpi("Cost of Goods",    fmt(cogs)),               unsafe_allow_html=True)
    with c3: st.markdown(kpi("Gross Profit",     fmt(gross),  "success" if gross>=0 else "danger"), unsafe_allow_html=True)
    with c4: st.markdown(kpi("Net Profit",       fmt(net),    "success" if net>=0   else "danger"), unsafe_allow_html=True)

    st.markdown("")

    # Row 2 — Operations
    st.markdown('<h3>Operations</h3>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi("Outstanding Balance",  fmt(balance),  "danger"),   unsafe_allow_html=True)
    with c2: st.markdown(kpi("Pending Orders",       str(pending),  "warn"),     unsafe_allow_html=True)
    with c3: st.markdown(kpi("Total Expenses",       fmt(total_exp),"danger"),   unsafe_allow_html=True)
    with c4: st.markdown(kpi("Inventory Value",      fmt(inv_value),"info"),     unsafe_allow_html=True)

    divider()

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<h3>Recent Orders</h3>', unsafe_allow_html=True)
        recent = orders[:12]
        if recent:
            SC = {"Pending":"#b8890a","Ready":"#1a6094","Delivered":"#1e8449","Cancelled":"#c0392b"}
            rows = []
            for o in recent:
                sc = SC.get(o["status"], "#847e76")
                rows.append([
                    f'<span style="color:#1a1612">{o["customer_name"]}</span>',
                    f'<span style="font-family:DM Mono,monospace;color:#b8890a">{fmt(o["total_amount"])}</span>',
                    f'<span style="font-size:10px;padding:2px 7px;background:rgba(0,0,0,0);border:1px solid {sc}40;color:{sc};border-radius:3px;letter-spacing:.06em">{o["status"]}</span>',
                    f'<span style="font-family:DM Mono,monospace;font-size:11px;color:#847e76">{fmt_dt(o["created_at"])}</span>',
                ])
            st.markdown(table_html(["Customer","Total","Status","Date"], rows), unsafe_allow_html=True)

    with col_right:
        st.markdown('<h3>Expenses by Category</h3>', unsafe_allow_html=True)
        cat_totals = {}
        for e in expenses:
            cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]
        if cat_totals:
            rows = []
            for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1]):
                pct = amt / total_exp * 100 if total_exp else 0
                rows.append([
                    f'<span style="color:#4a4640">{cat}</span>',
                    f'<span style="font-family:DM Mono,monospace;color:#c0392b">{fmt(amt)}</span>',
                    f'<div style="background:rgba(0,0,0,0.05);border-radius:2px;height:4px;overflow:hidden"><div style="background:#b8890a;height:4px;width:{pct:.1f}%"></div></div>',
                ])
            st.markdown(table_html(["Category","Amount","Share"], rows), unsafe_allow_html=True)

    divider()
    # User management
    st.markdown('<h3>User Accounts</h3>', unsafe_allow_html=True)
    from users import get_users
    users = get_users()
    ROLE_BADGE = {"admin":"rgba(192,57,43,.10);color:#c0392b;border:1px solid rgba(192,57,43,.3)",
                  "manager":"rgba(184,137,10,0.11);color:#b8890a;border:1px solid rgba(184,137,10,0.3)",
                  "cashier":"rgba(30,132,73,0.09);color:#1e8449;border:1px solid rgba(30,132,73,0.25)"}
    rows = []
    for uname, u in users.items():
        rb = ROLE_BADGE.get(u["role"],"")
        rows.append([
            f'<span style="font-family:DM Mono,monospace;color:#1a1612">{uname}</span>',
            f'<span style="color:#4a4640">{u["full_name"]}</span>',
            f'<span style="display:inline-block;padding:2px 8px;border-radius:3px;font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;font-weight:500;{rb}">{u["role"]}</span>',
        ])
    st.markdown(table_html(["Username","Name","Role"], rows), unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;color:#847e76;margin-top:8px">To change passwords or add users, edit <code>secrets.toml</code> or the DEFAULT_USERS in users.py</p>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# MANAGER DASHBOARD — sales + expenses, no profit
# ════════════════════════════════════════════════════════════
elif role == "manager":
    expenses = sb.table("expenses").select("amount,category,description,expense_date").order("expense_date", desc=True).limit(50).execute().data

    revenue   = sum(o["total_amount"] for o in orders if o["status"] != "Cancelled")
    total_exp = sum(e["amount"] for e in expenses)
    balance   = sum(o["balance_due"] for o in orders if o["status"] not in ["Cancelled","Delivered"])
    pending   = sum(1 for o in orders if o["status"] == "Pending")
    delivered = sum(1 for o in orders if o["status"] == "Delivered")

    # Metrics (no COGS, no profit)
    st.markdown('<h3>Sales Overview</h3>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi("Total Revenue",        fmt(revenue),   "gold"),  unsafe_allow_html=True)
    with c2: st.markdown(kpi("Outstanding Balance",  fmt(balance),   "danger"),unsafe_allow_html=True)
    with c3: st.markdown(kpi("Pending Orders",       str(pending),   "warn"),  unsafe_allow_html=True)
    with c4: st.markdown(kpi("Delivered Orders",     str(delivered), "success"),unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<h3>Expenses</h3>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 3])
    with c1: st.markdown(kpi("Total Expenses", fmt(total_exp), "danger"), unsafe_allow_html=True)

    divider()

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<h3>Recent Orders</h3>', unsafe_allow_html=True)
        SC = {"Pending":"#b8890a","Ready":"#1a6094","Delivered":"#1e8449","Cancelled":"#c0392b"}
        rows = []
        for o in orders[:15]:
            sc = SC.get(o["status"], "#847e76")
            rows.append([
                f'<span style="color:#1a1612">{o["customer_name"]}</span>',
                f'<span style="font-family:DM Mono,monospace;color:#b8890a">{fmt(o["total_amount"])}</span>',
                f'<span style="font-family:DM Mono,monospace;color:#c0392b">{fmt(o["balance_due"])}</span>',
                f'<span style="font-size:10px;padding:2px 7px;border:1px solid {sc}40;color:{sc};border-radius:3px;letter-spacing:.06em">{o["status"]}</span>',
            ])
        st.markdown(table_html(["Customer","Total","Balance","Status"], rows) if rows else '<p>No orders yet.</p>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<h3>Recent Expenses</h3>', unsafe_allow_html=True)
        rows = []
        for e in expenses[:12]:
            rows.append([
                f'<span style="color:#4a4640">{e.get("description","")[:28]}</span>',
                f'<span style="font-family:DM Mono,monospace;color:#c0392b">{fmt(e["amount"])}</span>',
                f'<span style="font-size:11px;color:#847e76">{e.get("expense_date","")}</span>',
            ])
        st.markdown(table_html(["Description","Amount","Date"], rows) if rows else '<p>No expenses yet.</p>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# CASHIER DASHBOARD — goods list + today's orders
# ════════════════════════════════════════════════════════════
elif role == "cashier":
    from db import load_inventory
    inv = load_inventory()

    # Simple stats for cashier
    total_items = len(inv)
    low_stock   = [c for c in inv if c["stock"] < 5]
    today_orders = [o for o in orders if o.get("created_at","")[:10] == __import__("datetime").date.today().isoformat()]

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi("Items Available",  str(total_items),       "cream"), unsafe_allow_html=True)
    with c2: st.markdown(kpi("Low Stock Items",  str(len(low_stock)),    "warn" if low_stock else "success"), unsafe_allow_html=True)
    with c3: st.markdown(kpi("Orders Today",     str(len(today_orders)), "gold"),  unsafe_allow_html=True)

    divider()

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<h3>Available Goods</h3>', unsafe_allow_html=True)
        search = st.text_input("Search items", placeholder="Type to filter...", label_visibility="collapsed")
        filtered = [c for c in inv if search.lower() in c["name"].lower()] if search else inv

        rows = []
        for c in filtered:
            stock_color = "#c0392b" if c["stock"] < 5 else ("#b7770d" if c["stock"] < 15 else "#1e8449")
            rows.append([
                f'<span style="color:#1a1612;font-weight:500">{c["name"]}</span>',
                f'<span style="font-size:10px;color:#847e76;background:rgba(0,0,0,0.05);padding:2px 7px;border-radius:3px">{c["uom"]}</span>',
                f'<span style="font-family:DM Mono,monospace;color:{stock_color};font-size:12px">{c["stock"]}</span>',
                f'<span style="font-family:DM Mono,monospace;color:#b8890a;font-size:12px">{fmt(c["default_sell_price"])}</span>',
            ])
        st.markdown(table_html(["Item","Unit","In Stock","Sell Price"], rows) if rows else "<p>No items found.</p>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<h3>Today\'s Orders</h3>', unsafe_allow_html=True)
        if today_orders:
            SC = {"Pending":"#b8890a","Ready":"#1a6094","Delivered":"#1e8449","Cancelled":"#c0392b"}
            rows = []
            for o in today_orders:
                sc = SC.get(o["status"], "#847e76")
                rows.append([
                    f'<span style="color:#1a1612">{o["customer_name"]}</span>',
                    f'<span style="font-family:DM Mono,monospace;color:#b8890a;font-size:12px">{fmt(o["total_amount"])}</span>',
                    f'<span style="font-size:10px;padding:2px 7px;border:1px solid {sc}40;color:{sc};border-radius:3px">{o["status"]}</span>',
                ])
            st.markdown(table_html(["Customer","Total","Status"], rows), unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center;padding:32px;color:#847e76;border:1px solid rgba(0,0,0,0.05);border-radius:8px"><div style="font-family:Playfair Display,serif;font-size:16px;color:#4a4640;margin-bottom:4px">No orders today</div>Head to POS to create one</div>', unsafe_allow_html=True)

        if low_stock:
            st.markdown("")
            st.markdown('<h3>Low Stock Alerts</h3>', unsafe_allow_html=True)
            rows = [[f'<span style="color:#c0392b">{c["name"]}</span>', f'<span style="font-family:DM Mono,monospace;color:#c0392b">{c["stock"]}</span>', f'<span style="color:#847e76">{c["uom"]}</span>'] for c in low_stock]
            st.markdown(table_html(["Item","Stock","Unit"], rows), unsafe_allow_html=True)
