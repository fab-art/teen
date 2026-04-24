import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from styles import inject, section_title, kpi, fmt, table_html
from users import require_permission, can
from sidebar import render_sidebar, render_home_button
from db import get_sb, audit, load_inventory, moving_avg_lc, insert_with_schema_fallback, update_with_schema_fallback
from db import get_sb, audit, load_inventory, moving_avg_lc, insert_with_schema_fallback

st.set_page_config(page_title="Inventory — Duka", page_icon="◫", layout="wide", initial_sidebar_state="expanded")
inject()
require_permission("view_inventory")
render_sidebar()

sb  = get_sb()
section_title("Inventory", "Stock levels, inwarding & adjustments")
render_home_button()

inv = load_inventory()
df  = pd.DataFrame(inv) if inv else pd.DataFrame()

# KPIs
if not df.empty:
    low_count = int((df["stock"] < 5).sum())
    inv_val   = float((df["stock"]*df["current_landed_cost"]).sum())
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(kpi("Total Items",     str(len(df))),                                   unsafe_allow_html=True)
    with c2: st.markdown(kpi("Low Stock",       str(low_count),"danger" if low_count else "success"), unsafe_allow_html=True)
    with c3: st.markdown(kpi("Inventory Value", fmt(inv_val),"gold"),                            unsafe_allow_html=True)
    with c4: st.markdown(kpi("Total Units",     f"{float(df['stock'].sum()):,.1f}"),              unsafe_allow_html=True)
    st.markdown("")

tab1, tab2, tab3, tab4 = st.tabs(["Stock Levels","Receive Stock","Adjustments","Catalog"])

with tab1:
    search = st.text_input("Search", placeholder="Filter items...", label_visibility="collapsed")
    data   = [c for c in inv if search.lower() in c["name"].lower()] if search else inv
    rows = []
    for c in data:
        sc = "#b84030" if c["stock"]<5 else ("#a07830" if c["stock"]<15 else "#4a8854")
        rows.append([
            f'<span style="color:#e8e0cc;font-weight:500">{c["name"]}</span>',
            f'<span style="font-size:10px;color:#534f47">{c["type"]}</span>',
            f'<span style="font-size:10px;color:#534f47">{c["uom"]}</span>',
            f'<span style="font-family:DM Mono,monospace;color:{sc}">{c["stock"]}</span>',
            f'<span style="font-family:DM Mono,monospace;color:#9a9080">{fmt(c["current_landed_cost"])}</span>',
            f'<span style="font-family:DM Mono,monospace;color:#c49a2c">{fmt(c["default_sell_price"])}</span>',
        ])
    st.markdown(table_html(["Item","Type","UOM","Stock","Landed Cost","Sell Price"], rows) if rows else "<p>No items.</p>", unsafe_allow_html=True)

with tab2:
    if not can("receive_stock"):
        st.warning("Manager or Admin required.")
    else:
        suppliers = sb.table("suppliers").select("supplier_id,name").order("name").execute().data
        sup_map   = {s["name"]:s["supplier_id"] for s in suppliers}
        with st.expander("+ Add Supplier"):
            with st.form("new_sup"):
                sn=st.text_input("Name"); sp=st.text_input("Phone")
                if st.form_submit_button("Add"):
                    if sn: sb.table("suppliers").insert({"name":sn,"phone":sp}).execute(); st.success("Added!"); st.rerun()
        mode = st.radio("Item", ["Existing","New"], horizontal=True)
        with st.form("receive"):
            if mode=="Existing" and not df.empty:
                sel_name = st.selectbox("Item", df["name"].tolist())
                item_id  = df[df["name"]==sel_name]["item_id"].values[0]
                new_name = new_type = new_uom = None
            else:
                item_id=None; new_name=st.text_input("Item Name")
                c1,c2=st.columns(2); new_type=c1.selectbox("Type",["Material","Product","Service"]); new_uom=c2.selectbox("UOM",["Meters","Pieces","Flat Rate"])
            c1,c2=st.columns(2); qty=c1.number_input("Quantity",min_value=0.01,value=1.0,step=0.5); purchase=c2.number_input("Purchase Price",min_value=0.0)
            c1,c2=st.columns(2); freight=c1.number_input("Freight",min_value=0.0); pay=c2.selectbox("Payment",["On Credit","Paid"])
            sup_sel=st.selectbox("Supplier",list(sup_map.keys()) if sup_map else ["—"])
            lc=(purchase+freight)/qty if qty else 0
            st.markdown(f'<div style="background:rgba(196,154,44,0.09);border:1px solid rgba(196,154,44,0.2);border-radius:4px;padding:9px 13px;display:flex;justify-content:space-between;margin-top:8px"><span style="font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:#534f47">Landed Cost / Unit</span><span style="font-family:DM Mono,monospace;color:#c49a2c">{fmt(lc)}</span></div>', unsafe_allow_html=True)
            if st.form_submit_button("Receive Stock", type="primary", use_container_width=True):
                if not item_id:
                    if not new_name: st.error("Item name required"); st.stop()
                    res=sb.table("catalog").insert({"name":new_name,"type":new_type,"uom":new_uom,"current_landed_cost":round(lc,2),"default_sell_price":round(lc*1.3,2)}).execute()
                    item_id=res.data[0]["item_id"]; audit("catalog",item_id,"INSERT",new_data=res.data[0],reason="New item on inward")
                else:
                    old=sb.table("catalog").select("current_landed_cost").eq("item_id",item_id).single().execute().data
                    new_avg=moving_avg_lc(sb,item_id,qty,lc)
                    sb.table("catalog").update({"current_landed_cost":new_avg}).eq("item_id",item_id).execute()
                    audit("catalog",item_id,"UPDATE",old_data=old,new_data={"current_landed_cost":new_avg},changed_fields=["current_landed_cost"],reason="Landed cost update on inward")
                led=insert_with_schema_fallback(sb, "inventory_ledger", {"item_id":item_id,"transaction_type":"INWARD","quantity_change":qty,"unit_cost":round(lc,2),"created_by":st.session_state.get("username")}) or {}
                inv_d={"item_id":item_id,"quantity":qty,"purchase_price":purchase,"freight_cost":freight,"status":pay,"created_by":st.session_state.get("username")}
                if sup_map.get(sup_sel): inv_d["supplier_id"]=sup_map[sup_sel]
                insert_with_schema_fallback(sb, "purchase_invoices", inv_d)
                audit("inventory_ledger",led.get("ledger_id", item_id),"INSERT",new_data=led,reason="Stock inward")
                st.success("Stock received!"); st.rerun()

with tab3:
    if not can("adjust_inventory"):
        st.warning("Admin only.")
    else:
        st.markdown('<div style="background:rgba(184,64,48,0.07);border:1px solid rgba(184,64,48,0.18);border-radius:6px;padding:10px 14px;font-size:11.5px;color:#b84030;margin-bottom:14px">Adjustments are permanent and logged. Every change requires a reason.</div>', unsafe_allow_html=True)
        sub1, sub2 = st.tabs(["Quantity Adjustment","Price Edit"])
        with sub1:
            if not df.empty:
                with st.form("adj"):
                    ai=st.selectbox("Item",df["name"].tolist()); ar=df[df["name"]==ai].iloc[0]
                    st.markdown(f'<span style="font-size:11.5px;color:#9a9080">Current stock: <span style="color:#e8e0cc;font-family:DM Mono,monospace">{ar["stock"]}</span> {ar["uom"]}</span>', unsafe_allow_html=True)
                    c1,c2=st.columns(2); at=c1.selectbox("Type",["Physical Count Correction","Damaged/Waste","Manual Addition","Opening Balance"]); ac=c2.number_input("Change (+/-)",value=0.0,step=0.5)
                    ar2=st.text_area("Reason (required)")
                    if st.form_submit_button("Apply",type="primary"):
                        if not ar2: st.error("Reason required")
                        elif ac==0: st.error("Change cannot be zero")
                        else:
                            led=insert_with_schema_fallback(sb, "inventory_ledger", {"item_id":ar["item_id"],"transaction_type":"ADJUSTMENT","quantity_change":ac,"notes":f"{at}: {ar2}","created_by":st.session_state.get("username")}) or {}
                            audit("inventory_ledger",led.get("ledger_id", ar["item_id"]),"ADJUST",new_data={"item":ai,"change":ac,"type":at},reason=ar2)
                            st.success(f"Adjustment applied: {'+' if ac>0 else ''}{ac} {ar['uom']}"); st.rerun()
        with sub2:
            if not df.empty:
                with st.form("price_edit"):
                    pi=st.selectbox("Item",df["name"].tolist(),key="pe"); pr=df[df["name"]==pi].iloc[0]
                    c1,c2=st.columns(2); nlc=c1.number_input("New Landed Cost",value=float(pr["current_landed_cost"]),min_value=0.0); nsp=c2.number_input("New Sell Price",value=float(pr["default_sell_price"]),min_value=0.0)
                    preason=st.text_input("Reason")
                    if st.form_submit_button("Update Prices",type="primary"):
                        if not preason: st.error("Reason required")
                        else:
                            old={"current_landed_cost":pr["current_landed_cost"],"default_sell_price":pr["default_sell_price"]}
                            new={"current_landed_cost":nlc,"default_sell_price":nsp}
                            sb.table("catalog").update(new).eq("item_id",pr["item_id"]).execute()
                            audit("catalog",pr["item_id"],"UPDATE",old_data=old,new_data=new,changed_fields=["current_landed_cost","default_sell_price"],reason=preason)
                            st.success("Prices updated!"); st.rerun()

with tab4:
    all_cat=sb.table("catalog").select("*").order("name").execute().data
    for item in all_cat:
        active=item.get("is_active",True)
        c1,c2,c3,c4=st.columns([3,1,1,1])
        c1.markdown(f'<span style="color:{"#e8e0cc" if active else "#534f47"};font-size:13px">{"" if active else "⊘ "}{item["name"]}</span> <span style="font-size:10px;color:#534f47">{item["uom"]}</span>', unsafe_allow_html=True)
        c2.markdown(f'<span style="font-size:11px;font-family:DM Mono,monospace;color:#9a9080">LC: {fmt(item["current_landed_cost"])}</span>', unsafe_allow_html=True)
        c3.markdown(f'<span style="font-size:11px;font-family:DM Mono,monospace;color:#c49a2c">SP: {fmt(item["default_sell_price"])}</span>', unsafe_allow_html=True)
        if can("manage_catalog"):
            if c4.button("Deactivate" if active else "Reactivate",key=f"tog_{item['item_id']}"):
                old={"is_active":active}
                upd = update_with_schema_fallback(sb, "catalog", {"is_active":not active}, "item_id", item["item_id"])
                if upd is None:
                    st.warning("Catalog active/inactive toggle is not supported by this database schema.")
                else:
                    audit("catalog",item["item_id"],"UPDATE",old_data=old,new_data={"is_active":not active},changed_fields=["is_active"],reason=f"Item {'deactivated' if active else 'reactivated'}")
                    st.rerun()
