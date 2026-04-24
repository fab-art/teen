import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from styles import inject, section_title, fmt, fmt_dt
from users import require_permission, can
from sidebar import render_sidebar, render_home_button
import db as db_module
from db import get_sb, audit, insert_with_schema_fallback, update_with_schema_fallback
from db import get_sb, audit

insert_with_schema_fallback = getattr(
    db_module,
    "insert_with_schema_fallback",
    lambda sb, table_name, payload: (sb.table(table_name).insert(payload).execute().data or [None])[0],
)
update_with_schema_fallback = getattr(
    db_module,
    "update_with_schema_fallback",
    lambda sb, table_name, payload, match_col, match_val: sb.table(table_name).update(payload).eq(match_col, match_val).execute().data,
)

st.set_page_config(page_title="Orders — Duka", page_icon="◎", layout="wide", initial_sidebar_state="expanded")
inject()
require_permission("view_orders")
render_sidebar()

sb = get_sb()
section_title("Orders", "Manage, edit and track all orders")
render_home_button()

SC_HEX = {"Pending":"#b8890a","Ready":"#1a6094","Delivered":"#1e8449","Cancelled":"#c0392b"}

c1,c2,c3 = st.columns([2,1,1])
search        = c1.text_input("Search customer", placeholder="Type to filter...")
status_filter = c2.selectbox("Status",["All","Pending","Ready","Delivered","Cancelled"])
limit         = c3.selectbox("Show",[25,50,100])

q = sb.table("sales_orders").select("*").order("created_at",desc=True).limit(limit)
if status_filter != "All": q = q.eq("status",status_filter)
orders = q.execute().data
if search: orders = [o for o in orders if search.lower() in o["customer_name"].lower()]

if not orders:
    st.info("No orders found.")
else:
    for order in orders:
        status = order["status"]
        sc = SC_HEX.get(status,"#847e76")
        badge_html = f'<span style="font-size:10px;padding:2px 7px;border:1px solid {sc}40;color:{sc};border-radius:3px;letter-spacing:.06em">{status}</span>'
        header_txt = f'{order["customer_name"]} — {fmt(order["total_amount"])} — {fmt_dt(order["created_at"])}'

        with st.expander(header_txt):
            col1, col2 = st.columns([3,2])

            with col1:
                lines = sb.table("order_lines").select("*,catalog(name,uom)").eq("order_id",order["order_id"]).execute().data
                if lines:
                    rows_html = ""
                    for l in lines:
                        voided = l.get("is_voided",False)
                        iname  = l["catalog"]["name"] if l.get("catalog") else "—"
                        uom    = l["catalog"]["uom"]  if l.get("catalog") else ""
                        style  = "color:#847e76;text-decoration:line-through" if voided else "color:#1a1612"
                        vb     = ' <span style="font-size:9px;color:#c0392b;border:1px solid rgba(192,57,43,.3);padding:1px 5px;border-radius:2px">VOID</span>' if voided else ""
                        rows_html += f'<tr><td style="padding:9px 13px;{style};font-size:13px">{iname}{vb}</td><td style="padding:9px 13px;font-family:DM Mono,monospace;font-size:11.5px;color:#4a4640;text-align:right">{l["quantity"]} {uom}</td><td style="padding:9px 13px;font-family:DM Mono,monospace;font-size:11.5px;color:#4a4640;text-align:right">{fmt(l["unit_price"])}</td><td style="padding:9px 13px;font-family:DM Mono,monospace;font-size:12px;color:#b8890a;text-align:right">{fmt(l["quantity"]*l["unit_price"])}</td></tr>'
                        if l.get("void_reason"): rows_html += f'<tr><td colspan="4" style="padding:0 13px 8px;font-size:11px;color:#847e76;font-style:italic">Reason: {l["void_reason"]}</td></tr>'

                    st.markdown(f'<div style="background:#faf8f4;border:1px solid rgba(0,0,0,0.07);border-radius:6px;overflow:hidden;margin-bottom:10px"><table style="width:100%;border-collapse:collapse"><thead><tr style="border-bottom:1px solid rgba(0,0,0,0.07)"><th style="padding:8px 13px;text-align:left;font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:#847e76">Item</th><th style="padding:8px 13px;text-align:right;font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:#847e76">Qty</th><th style="padding:8px 13px;text-align:right;font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:#847e76">Price</th><th style="padding:8px 13px;text-align:right;font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:#847e76">Total</th></tr></thead><tbody>{rows_html}</tbody><tfoot><tr style="border-top:1px solid rgba(0,0,0,0.07)"><td colspan="3" style="padding:9px 13px;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#847e76">Total · Deposit · Balance</td><td style="padding:9px 13px;font-family:DM Mono,monospace;font-size:12px;color:#b8890a;text-align:right">{fmt(order["total_amount"])} · {fmt(order["deposit_paid"])} · {fmt(order["balance_due"])}</td></tr></tfoot></table></div>', unsafe_allow_html=True)

                # Void line
                if can("void_lines") and status not in ["Cancelled","Delivered"]:
                    active_lines = [l for l in lines if not l.get("is_voided") and l.get("catalog")]
                    if active_lines:
                        st.markdown('<h3 style="margin-top:6px">Void a Line</h3>', unsafe_allow_html=True)
                        void_opts = {f'{l["catalog"]["name"]} × {l["quantity"]}':l for l in active_lines}
                        with st.form(f"void_{order['order_id']}"):
                            vs = st.selectbox("Line",list(void_opts.keys()))
                            vr = st.text_input("Reason")
                            if st.form_submit_button("Void Line",type="primary"):
                                if not vr: st.error("Reason required")
                                else:
                                    vl=void_opts[vs]; old=dict(vl)
                                    upd = update_with_schema_fallback(sb, "order_lines", {"is_voided":True,"void_reason":vr,"voided_by":st.session_state.get("username")}, "line_id", vl["line_id"])
                                    if upd is None:
                                        st.warning("This database schema does not support line-level void updates.")
                                        st.stop()
                                    update_with_schema_fallback(sb, "order_lines", {"is_voided":True,"void_reason":vr,"voided_by":st.session_state.get("username")}, "line_id", vl["line_id"])
                                    insert_with_schema_fallback(sb, "inventory_ledger", {"item_id":vl["item_id"],"transaction_type":"VOID_SALE","quantity_change":vl["quantity"],"unit_cost":vl["line_cogs"]/vl["quantity"] if vl["quantity"] else 0,"reference_id":order["order_id"],"notes":f"Void: {vr}","created_by":st.session_state.get("username")})
                                    try:
                                        remaining=sb.table("order_lines").select("quantity,unit_price").eq("order_id",order["order_id"]).eq("is_voided",False).execute().data
                                    except Exception:
                                        remaining=sb.table("order_lines").select("quantity,unit_price").eq("order_id",order["order_id"]).execute().data
                                    new_total=sum(l["quantity"]*l["unit_price"] for l in remaining)
                                    update_with_schema_fallback(sb, "sales_orders", {"total_amount":new_total}, "order_id", order["order_id"])
                                    audit("order_lines",vl["line_id"],"VOID",old_data=old,reason=vr)
                                    st.success("Line voided."); st.rerun()

            with col2:
                st.markdown(f'<div style="font-size:12.5px;color:#4a4640;line-height:2;background:#faf8f4;border:1px solid rgba(0,0,0,0.07);border-radius:6px;padding:14px 16px"><span style="color:#847e76">Customer:</span> <span style="color:#1a1612">{order["customer_name"]}</span><br><span style="color:#847e76">Phone:</span> {order.get("customer_phone") or "—"}<br><span style="color:#847e76">Status:</span> <span style="color:{SC_HEX.get(status,"#847e76")}">{status}</span><br><span style="color:#847e76">Notes:</span> {order.get("notes") or "—"}</div>', unsafe_allow_html=True)

                if can("edit_orders"):
                    st.markdown('<h3 style="margin-top:12px">Edit Order</h3>', unsafe_allow_html=True)
                    with st.form(f"edit_{order['order_id']}"):
                        ns  = st.selectbox("Status",["Pending","Ready","Delivered","Cancelled"],index=["Pending","Ready","Delivered","Cancelled"].index(status))
                        nd  = st.number_input("Deposit",min_value=0.0,value=float(order["deposit_paid"]),step=100.0)
                        nn  = st.text_input("Notes",value=order.get("notes") or "")
                        er  = st.text_input("Reason (required)")
                        if st.form_submit_button("Save",type="primary"):
                            if not er: st.error("Reason required")
                            else:
                                changes={}; cf=[]
                                if ns!=status: changes["status"]=ns; cf.append("status")
                                if nd!=order["deposit_paid"]: changes["deposit_paid"]=nd; cf.append("deposit_paid")
                                if nn!=(order.get("notes") or ""): changes["notes"]=nn; cf.append("notes")
                                if changes:
                                    update_with_schema_fallback(sb, "sales_orders", changes, "order_id", order["order_id"])
                                    audit("sales_orders",order["order_id"],"UPDATE",old_data=dict(order),new_data=changes,changed_fields=cf,reason=er)
                                    st.success("Updated."); st.rerun()
