import streamlit as st
import json
from datetime import datetime
from supabase import create_client

# ── Constants ──────────────────────────────────────────────────
STATUS_COLORS = {"Pending": "gold", "Ready": "info", "Delivered": "success", "Cancelled": "danger"}
STATUS_HEX = {"Pending": "#b8890a", "Ready": "#1a6094", "Delivered": "#1e8449", "Cancelled": "#c0392b"}

@st.cache_resource
def get_sb():
    """Get cached Supabase client instance."""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def _sum_quantities_by_item(rows):
    """Aggregate inventory ledger quantity changes by item_id."""
    totals = {}
    for row in rows or []:
        item_id = row["item_id"]
        totals[item_id] = totals.get(item_id, 0) + row["quantity_change"]
    return totals

def load_inventory(sb=None):
    """Load inventory with stock levels efficiently.
    
    Args:
        sb: Optional Supabase client. If None, creates new connection.
    
    Returns:
        List of catalog items with computed 'stock' field.
    """
    if sb is None:
        sb = get_sb()
    
    # Fetch active catalog items
    cat = sb.table("catalog").select(
        "item_id,name,type,uom,current_landed_cost,default_sell_price,is_active"
    ).eq("is_active", True).order("name").execute().data
    
    if not cat:
        return []
    
    # Fetch inventory ledger and aggregate by item_id in one pass
    led = sb.table("inventory_ledger").select("item_id,quantity_change").execute().data
    
    totals = _sum_quantities_by_item(led)
    
    # Add stock levels to catalog items
    for c in cat:
        c["stock"] = round(max(totals.get(c["item_id"], 0), 0), 3)
    
    return cat

def moving_avg_lc(sb, item_id, new_qty, new_lc):
    """Calculate moving average landed cost for inventory valuation.
    
    Args:
        sb: Supabase client
        item_id: Item identifier
        new_qty: New quantity being added
        new_lc: New landed cost per unit
    
    Returns:
        Weighted average landed cost rounded to 2 decimals.
    """
    cat = sb.table("catalog").select("current_landed_cost").eq("item_id", item_id).single().execute()
    led = sb.table("inventory_ledger").select("quantity_change").eq("item_id", item_id).execute()
    
    old_cost = cat.data["current_landed_cost"] if cat.data else 0
    old_qty = max(sum(r["quantity_change"] for r in led.data) if led.data else 0, 0)
    
    if old_qty + new_qty > 0:
        return round(((old_qty * old_cost) + (new_qty * new_lc)) / (old_qty + new_qty), 2)
    return round(new_lc, 2)

def audit(table, record_id, action, old_data=None, new_data=None, reason=None, changed_fields=None):
    """Record an audit log entry.
    
    Args:
        table: Name of the affected table
        record_id: ID of the affected record
        action: Action type (INSERT, UPDATE, VOID, etc.)
        old_data: Previous state of the record (for UPDATE/VOID)
        new_data: New state of the record (for INSERT/UPDATE)
        reason: Reason for the change
        changed_fields: List of field names that changed
    """
    sb = get_sb()
    from users import current_user
    u = current_user()
    
    sb.table("audit_log").insert({
        "table_name": table,
        "record_id": str(record_id),
        "action": action,
        "old_data": json.dumps(old_data, default=str) if old_data else None,
        "new_data": json.dumps(new_data, default=str) if new_data else None,
        "changed_fields": changed_fields,
        "reason": reason,
        "performed_by_username": u.get("username") if u else None,
        "performed_by_name": u.get("full_name") if u else None,
    }).execute()

def fmt(n):
    """Format number as currency with 2 decimal places."""
    try:
        return f"{float(n):,.2f}"
    except (TypeError, ValueError):
        return "—"

def fmt_dt(s):
    """Format ISO datetime string to readable format."""
    if not s:
        return "—"
    try:
        return datetime.fromisoformat(s.replace("Z", "")).strftime("%d %b %Y %H:%M")
    except (ValueError, AttributeError):
        return str(s)[:16]


@st.cache_data(ttl=90, show_spinner=False)
def fetch_dashboard_snapshot(role: str):
    """
    Fetch dashboard data in a cache-friendly shape.

    Uses a short TTL to reduce repeated Supabase round-trips while keeping
    operational data relatively fresh for Streamlit Cloud sessions.
    """
    sb = get_sb()
    orders = (
        sb.table("sales_orders")
        .select("order_id,total_amount,deposit_paid,balance_due,status,customer_name,created_at")
        .order("created_at", desc=True)
        .limit(200)
        .execute()
        .data
    )

    payload = {"orders": orders}

    if role == "admin":
        payload.update(
            {
                "lines": sb.table("order_lines").select("line_cogs").execute().data,
                "expenses": sb.table("expenses").select("amount,category").execute().data,
                "inventory_catalog": sb.table("catalog").select("item_id,current_landed_cost").execute().data,
                "inventory_ledger": sb.table("inventory_ledger").select("item_id,quantity_change").execute().data,
            }
        )
    elif role == "manager":
        payload["expenses"] = (
            sb.table("expenses")
            .select("amount,category,description,expense_date")
            .order("expense_date", desc=True)
            .limit(50)
            .execute()
            .data
        )
    elif role == "cashier":
        payload["inventory"] = load_inventory(sb=sb)

    return payload


def compute_inventory_value(catalog_rows, ledger_rows):
    """Compute total inventory valuation from catalog costs and ledger balances."""
    totals = _sum_quantities_by_item(ledger_rows)
    return sum(max(totals.get(c["item_id"], 0), 0) * c["current_landed_cost"] for c in catalog_rows or [])
