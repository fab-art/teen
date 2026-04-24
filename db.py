# -*- coding: utf-8 -*-
import streamlit as st
import json
from datetime import datetime
from supabase import create_client
from postgrest.exceptions import APIError

# ── Constants ──────────────────────────────────────────────────
STATUS_COLORS = {"Pending": "gold", "Ready": "info", "Delivered": "success", "Cancelled": "danger"}
STATUS_HEX = {"Pending": "#b8890a", "Ready": "#1a6094", "Delivered": "#1e8449", "Cancelled": "#c0392b"}

@st.cache_resource
def get_sb():
    """Get cached Supabase client instance."""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def _safe_execute(query):
    """Execute a Supabase query and return data, swallowing schema mismatch API errors."""
    try:
        return query.execute().data
    except Exception:
        return None


def _sum_quantities_by_item(rows):
    """Aggregate inventory ledger quantity changes by item_id."""
    totals = {}
    for row in rows or []:
        item_id = row["item_id"]
        totals[item_id] = totals.get(item_id, 0) + row["quantity_change"]
    return totals


def _missing_column_from_error(err):
    """Parse PostgREST missing-column errors and return the column name."""
    message = str(err)
    marker = "Could not find the '"
    if marker not in message:
        return None
    try:
        return message.split(marker, 1)[1].split("' column", 1)[0]
    except Exception:
        return None

def load_inventory(sb=None):
    """Load inventory with stock levels efficiently.
    
    Args:
        sb: Optional Supabase client. If None, creates new connection.
    
    Returns:
        List of catalog items with computed 'stock' field.
    """
    if sb is None:
        sb = get_sb()
    
    # Fetch active catalog items (with fallback for schemas that do not have is_active)
    cat = _safe_execute(
        sb.table("catalog")
        .select("item_id,name,type,uom,current_landed_cost,default_sell_price,is_active")
        .eq("is_active", True)
        .order("name")
    )
    if cat is None:
        cat = _safe_execute(
            sb.table("catalog")
            .select("item_id,name,type,uom,current_landed_cost,default_sell_price")
            .order("name")
        ) or []
    
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
    
    payload = {
        "table_name": table,
        "record_id": str(record_id),
        "action": action,
        "old_data": json.dumps(old_data, default=str) if old_data else None,
        "new_data": json.dumps(new_data, default=str) if new_data else None,
        "changed_fields": changed_fields,
        "reason": reason,
        "performed_by_username": u.get("username") if u else None,
        "performed_by_name": u.get("full_name") if u else None,
    }

    # Backward-compatible insert for deployments where audit_log schema differs.
    # If PostgREST reports a missing column, remove it and retry.
    while True:
        try:
            sb.table("audit_log").insert(payload).execute()
            break
        except Exception as err:
            missing_col = _missing_column_from_error(err)
            if not missing_col:
                raise
            message = str(err)
            marker = "Could not find the '"
            if marker not in message:
                raise

            try:
                missing_col = message.split(marker, 1)[1].split("' column", 1)[0]
            except Exception:
                raise

            if missing_col not in payload:
                raise
            payload.pop(missing_col, None)

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
    orders_result = (
        sb.table("sales_orders")
        .select("order_id,total_amount,deposit_paid,balance_due,status,customer_name,created_at")
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )
    payload = {"orders": orders_result.data or []}

    if role == "admin":
        inventory_catalog = _safe_execute(sb.table("catalog").select("item_id,current_landed_cost"))
        if inventory_catalog is None:
            item_only_rows = _safe_execute(sb.table("catalog").select("item_id")) or []
            inventory_catalog = [
                {"item_id": row["item_id"], "current_landed_cost": 0}
                for row in item_only_rows
            ]

        payload["lines"] = _safe_execute(sb.table("order_lines").select("line_cogs")) or []
        payload["expenses"] = _safe_execute(sb.table("expenses").select("amount,category")) or []
        payload["inventory_catalog"] = inventory_catalog
        payload["inventory_ledger"] = (
            _safe_execute(sb.table("inventory_ledger").select("item_id,quantity_change")) or []
        )

    if role == "manager":
        payload["expenses"] = (
            _safe_execute(
                sb.table("expenses")
                .select("amount,category,description,expense_date")
                .order("expense_date", desc=True)
                .limit(50)
            )
            or []
        )

    if role == "cashier":
        payload["inventory"] = load_inventory(sb=sb)

    return payload


def compute_inventory_value(catalog_rows, ledger_rows):
    """Compute total inventory valuation from catalog costs and ledger balances."""
    totals = _sum_quantities_by_item(ledger_rows)
    return sum(max(totals.get(c["item_id"], 0), 0) * c["current_landed_cost"] for c in catalog_rows or [])


def fetch_catalog_for_pos(sb):
    """
    Fetch POS catalog data with compatibility fallbacks for older/newer schemas.
    """
    select_candidates = [
        ("item_id,name,uom,default_sell_price,current_landed_cost,is_active", True),
        ("item_id,name,uom,default_sell_price,current_landed_cost", False),
        ("item_id,name,uom,default_sell_price,is_active", True),
        ("item_id,name,uom,default_sell_price", False),
        ("item_id,name,uom,current_landed_cost,is_active", True),
        ("item_id,name,uom,current_landed_cost", False),
        ("item_id,name,uom", False),
    ]

    rows = []
    for select_clause, has_is_active in select_candidates:
        query = sb.table("catalog").select(select_clause).order("name")
        if has_is_active:
            query = query.eq("is_active", True)
        rows = _safe_execute(query)
        if rows is not None:
            break

    normalized = []
    for row in rows or []:
        normalized.append(
            {
                "item_id": row.get("item_id"),
                "name": row.get("name", "Unnamed Item"),
                "uom": row.get("uom", "unit"),
                "default_sell_price": float(row.get("default_sell_price") or 0),
                "current_landed_cost": float(row.get("current_landed_cost") or 0),
            }
        )
    return normalized


def fetch_catalog_cost_map(sb, item_ids):
    """Return {item_id: current_landed_cost} with fallback for missing cost columns."""
    if not item_ids:
        return {}
    rows = _safe_execute(
        sb.table("catalog").select("item_id,current_landed_cost").in_("item_id", item_ids)
    )
    if rows is None:
        rows = _safe_execute(sb.table("catalog").select("item_id").in_("item_id", item_ids)) or []
        return {r["item_id"]: 0 for r in rows}
    return {r["item_id"]: float(r.get("current_landed_cost") or 0) for r in rows}


def insert_with_schema_fallback(sb, table_name, payload):
    """
    Insert row while tolerating missing columns in older schemas.

    If PostgREST reports a missing column, the column is removed from payload
    and the insert is retried.
    """
    row = dict(payload)
    while True:
        try:
            result = sb.table(table_name).insert(row).execute()
            return (result.data or [None])[0]
        except Exception as err:
            missing_col = _missing_column_from_error(err)
            if not missing_col:
                raise
            if missing_col not in row:
                raise
            row.pop(missing_col, None)


def update_with_schema_fallback(sb, table_name, payload, match_col, match_val):
    """
    Update row while tolerating missing payload columns in older schemas.
    """
    row = dict(payload)
    while True:
        if not row:
            return None
        try:
            return sb.table(table_name).update(row).eq(match_col, match_val).execute().data
        except Exception as err:
            missing_col = _missing_column_from_error(err)
            if not missing_col:
                raise
            if missing_col == match_col:
                return None
            message = str(err)
            marker = "Could not find the '"
            if marker not in message:
                raise
            missing_col = message.split(marker, 1)[1].split("' column", 1)[0]
            if missing_col not in row:
                raise
            row.pop(missing_col, None)
