import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from styles import inject, section_title, fmt, divider
from users import require_auth, can
from sidebar import render_sidebar, render_home_button
from db import get_sb, audit, fetch_catalog_for_pos, fetch_catalog_cost_map, insert_with_schema_fallback

st.set_page_config(page_title="POS — Duka", page_icon="◉", layout="wide", initial_sidebar_state="expanded")
inject()
require_auth()
render_sidebar()

sb = get_sb()
section_title("Point of Sale", "Create new orders")
render_home_button()

catalog = fetch_catalog_for_pos(sb)
if "cart" not in st.session_state:
    st.session_state.cart = []

col_l, col_r = st.columns([1,1], gap="large")

with col_l:
    st.markdown('<h3>Add Item</h3>', unsafe_allow_html=True)
    if not catalog:
        st.info("No items in catalog yet.")
    else:
        cat_map = {f"{c['name']} ({c['uom']})": c for c in catalog}
        sel = st.selectbox("Product / Material", list(cat_map.keys()))
        item = cat_map[sel]
        c1, c2 = st.columns(2)
        qty   = c1.number_input("Quantity", min_value=0.01, value=1.0, step=0.5)
        price = c2.number_input("Unit Price", min_value=0.0, value=float(item["default_sell_price"]), step=0.5)
        if can("edit_prices"):
            lc = item["current_landed_cost"] or 0
            margin = price - lc
            st.markdown(f'<span style="font-size:11px;color:#534f47">LC: {fmt(lc)} · Margin: {fmt(margin)}</span>', unsafe_allow_html=True)
        if st.button("+ Add to Cart", use_container_width=True):
            ex = next((l for l in st.session_state.cart if l["item_id"]==item["item_id"] and l["unit_price"]==price), None)
            if ex: ex["quantity"] = round(ex["quantity"] + qty, 3)
            else: st.session_state.cart.append({"item_id":item["item_id"],"name":item["name"],"uom":item["uom"],"quantity":qty,"unit_price":price,"landed_cost":item["current_landed_cost"]})
            st.rerun()

    divider()
    st.markdown('<h3>Customer</h3>', unsafe_allow_html=True)
    cname   = st.text_input("Name")
    cphone  = st.text_input("Phone")
    deposit = st.number_input("Upfront Deposit", min_value=0.0, value=0.0, step=100.0)
    notes   = st.text_area("Notes", height=65)

with col_r:
    st.markdown('<h3>Cart</h3>', unsafe_allow_html=True)
    if not st.session_state.cart:
        st.markdown('<div style="text-align:center;padding:48px 20px;border:1px solid rgba(232,224,204,0.07);border-radius:8px;color:#534f47"><div style="font-family:Playfair Display,serif;font-size:18px;color:#9a9080;margin-bottom:5px">Cart is empty</div>Add items from the left</div>', unsafe_allow_html=True)
    else:
        total = sum(l["quantity"]*l["unit_price"] for l in st.session_state.cart)
        balance = total - deposit

        rows_html = ""
        for i, line in enumerate(st.session_state.cart):
            lt = line["quantity"] * line["unit_price"]
            rows_html += f'<tr><td style="padding:10px 13px;color:#e8e0cc;font-size:13px">{line["name"]}</td><td style="padding:10px 13px;font-family:DM Mono,monospace;font-size:11.5px;color:#9a9080;text-align:right">{line["quantity"]} {line["uom"]}</td><td style="padding:10px 13px;font-family:DM Mono,monospace;font-size:11.5px;color:#9a9080;text-align:right">{fmt(line["unit_price"])}</td><td style="padding:10px 13px;font-family:DM Mono,monospace;font-size:12px;color:#c49a2c;text-align:right">{fmt(lt)}</td></tr>'

        st.markdown(f"""
<div style="background:#1a1814;border:1px solid rgba(232,224,204,0.07);border-radius:8px;overflow:hidden;margin-bottom:12px">
  <table style="width:100%;border-collapse:collapse">
    <thead><tr style="border-bottom:1px solid rgba(232,224,204,0.07)">
      <th style="padding:9px 13px;text-align:left;font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:#534f47">Item</th>
      <th style="padding:9px 13px;text-align:right;font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:#534f47">Qty</th>
      <th style="padding:9px 13px;text-align:right;font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:#534f47">Price</th>
      <th style="padding:9px 13px;text-align:right;font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:#534f47">Total</th>
    </tr></thead>
    <tbody style="border-collapse:collapse">{rows_html}</tbody>
    <tfoot>
      <tr style="border-top:1px solid rgba(232,224,204,0.07)">
        <td colspan="3" style="padding:12px 13px;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#534f47">Total</td>
        <td style="padding:12px 13px;font-family:Playfair Display,serif;font-size:26px;font-weight:500;color:#c49a2c;text-align:right">{fmt(total)}</td>
      </tr>
      <tr><td colspan="3" style="padding:0 13px 11px;font-family:DM Mono,monospace;font-size:11px;color:#534f47">Balance due</td>
      <td style="padding:0 13px 11px;font-family:DM Mono,monospace;font-size:12px;color:#b84030;text-align:right">{fmt(balance)}</td></tr>
    </tfoot>
  </table>
</div>""", unsafe_allow_html=True)

        st.markdown('<h3 style="margin-bottom:8px">Remove Items</h3>', unsafe_allow_html=True)
        for i, line in enumerate(st.session_state.cart):
            ca, cb = st.columns([4,1])
            ca.markdown(f'<span style="font-size:12px;color:#9a9080">{line["name"]} — {line["quantity"]} {line["uom"]}</span>', unsafe_allow_html=True)
            if cb.button("×", key=f"rm_{i}"): st.session_state.cart.pop(i); st.rerun()

        divider()
        ca, cb = st.columns(2)
        if ca.button("Clear Cart", use_container_width=True): st.session_state.cart=[]; st.rerun()
        if cb.button("Place Order", type="primary", use_container_width=True):
            if not cname: st.error("Customer name required.")
            else:
                with st.spinner("Processing..."):
                    ids = [l["item_id"] for l in st.session_state.cart]
                    cm = fetch_catalog_cost_map(sb, ids)
                    total = sum(l["quantity"]*l["unit_price"] for l in st.session_state.cart)
                    order = insert_with_schema_fallback(sb, "sales_orders", {"customer_name":cname,"customer_phone":cphone,"total_amount":total,"deposit_paid":deposit,"status":"Pending","notes":notes,"created_by":st.session_state.get("username")}) or {}
                    oid = order.get("order_id")
                    if oid is None:
                        st.error("Order created but no order_id was returned by the database schema.")
                        st.stop()
                    for line in st.session_state.cart:
                        cogs=(cm.get(line["item_id"],0) or 0)*line["quantity"]
                        insert_with_schema_fallback(sb, "order_lines", {"order_id":oid,"item_id":line["item_id"],"quantity":line["quantity"],"unit_price":line["unit_price"],"line_cogs":cogs})
                        insert_with_schema_fallback(sb, "inventory_ledger", {"item_id":line["item_id"],"transaction_type":"SALE","quantity_change":-line["quantity"],"unit_cost":cm.get(line["item_id"],0),"reference_id":oid,"created_by":st.session_state.get("username")})
                    audit("sales_orders",oid,"INSERT",new_data=order,reason="POS order placed")
                    st.success(f"Order placed! Balance due: {fmt(total-deposit)}")
                    st.session_state.cart=[]; st.rerun()
