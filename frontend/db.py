import streamlit as st
import json
from datetime import datetime
from supabase import create_client

@st.cache_resource
def get_sb():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def load_inventory():
    sb = get_sb()
    cat = sb.table("catalog").select("item_id,name,type,uom,current_landed_cost,default_sell_price,is_active").eq("is_active", True).order("name").execute().data
    led = sb.table("inventory_ledger").select("item_id,quantity_change").execute().data
    totals = {}
    for r in led:
        totals[r["item_id"]] = totals.get(r["item_id"], 0) + r["quantity_change"]
    for c in cat:
        c["stock"] = round(max(totals.get(c["item_id"], 0), 0), 3)
    return cat

def moving_avg_lc(sb, item_id, new_qty, new_lc):
    cat = sb.table("catalog").select("current_landed_cost").eq("item_id", item_id).single().execute()
    led = sb.table("inventory_ledger").select("quantity_change").eq("item_id", item_id).execute()
    old_cost = cat.data["current_landed_cost"] if cat.data else 0
    old_qty  = max(sum(r["quantity_change"] for r in led.data) if led.data else 0, 0)
    if old_qty + new_qty > 0:
        return round(((old_qty * old_cost) + (new_qty * new_lc)) / (old_qty + new_qty), 2)
    return round(new_lc, 2)

def audit(table, record_id, action, old_data=None, new_data=None, reason=None, changed_fields=None):
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
    try: return f"{float(n):,.2f}"
    except: return "—"

def fmt_dt(s):
    if not s: return "—"
    try: return datetime.fromisoformat(s.replace("Z","")).strftime("%d %b %Y %H:%M")
    except: return str(s)[:16]

STATUS_COLORS = {"Pending":"gold","Ready":"info","Delivered":"success","Cancelled":"danger"}
