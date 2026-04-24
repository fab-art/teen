import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from styles import inject, section_title, kpi, fmt, fmt_dt, divider, table_html
from users import require_permission, can
from sidebar import render_sidebar, render_home_button
from db import get_sb, audit
from postgrest.exceptions import APIError

st.set_page_config(page_title="Finance — Duka", page_icon="◑", layout="wide", initial_sidebar_state="expanded")
inject()
require_permission("view_finance")
render_sidebar()

sb = get_sb()
section_title("Finance", "Revenue, expenses & payables")
render_home_button()


def _select_with_optional_is_voided(table_name, select_clause, *, order_by=None, desc=False, limit=None):
    """Query helper that tolerates deployments where `is_voided` does not exist."""
    def _build_query(include_is_voided_filter: bool):
        query = sb.table(table_name).select(select_clause)
        if include_is_voided_filter:
            query = query.eq("is_voided", False)
        if order_by:
            query = query.order(order_by, desc=desc)
        if limit:
            query = query.limit(limit)
        return query

    try:
        return _build_query(True).execute().data
    except APIError as err:
        if "is_voided" not in str(err):
            raise
        return _build_query(False).execute().data



def _select_with_optional_is_voided(table_name, select_clause, *, order_by=None, desc=False, limit=None):
    """Query helper that tolerates deployments where `is_voided` does not exist."""
    def _build_query(include_is_voided_filter: bool):
        query = sb.table(table_name).select(select_clause)
        if include_is_voided_filter:
            query = query.eq("is_voided", False)
        if order_by:
            query = query.order(order_by, desc=desc)
        if limit:
            query = query.limit(limit)
        return query

    try:
        return _build_query(True).execute().data
    except APIError as err:
        if "is_voided" not in str(err):
            raise
        return _build_query(False).execute().data


orders   = sb.table("sales_orders").select("total_amount,status").neq("status","Cancelled").execute().data
lines    = _select_with_optional_is_voided("order_lines", "line_cogs")
expenses = _select_with_optional_is_voided("expenses", "amount")
invoices = _select_with_optional_is_voided("purchase_invoices", "landed_cost,suppliers(name),status")
invoices = [inv for inv in invoices if inv.get("status") == "On Credit"] if invoices else []

revenue   = sum(o["total_amount"] for o in orders)
cogs      = sum(l["line_cogs"] for l in lines)
total_exp = sum(e["amount"] for e in expenses)
gross     = revenue - cogs
net       = gross - total_exp

# KPIs — hide profit for manager
role_can_profit = can("view_profit")
if role_can_profit:
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(kpi("Revenue",       fmt(revenue),"gold"),                              unsafe_allow_html=True)
    with c2: st.markdown(kpi("COGS",          fmt(cogs)),                                        unsafe_allow_html=True)
    with c3: st.markdown(kpi("Gross Profit",  fmt(gross), "success" if gross>=0 else "danger"),  unsafe_allow_html=True)
    with c4: st.markdown(kpi("Expenses",      fmt(total_exp),"danger"),                          unsafe_allow_html=True)
    with c5: st.markdown(kpi("Net Profit",    fmt(net),   "success" if net>=0   else "danger"),  unsafe_allow_html=True)
else:
    # Manager: revenue + expenses only, no profit shown
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(kpi("Revenue",     fmt(revenue),"gold"),    unsafe_allow_html=True)
    with c2: st.markdown(kpi("Expenses",    fmt(total_exp),"danger"), unsafe_allow_html=True)
    with c3: st.markdown(kpi("Payables",    fmt(sum(i["landed_cost"] or 0 for i in invoices)),"warn"), unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;color:#847e76;margin-top:6px">Profit figures are restricted to admin role.</p>', unsafe_allow_html=True)

divider()

tab_ap, tab_exp, tab_inv = st.tabs(["Accounts Payable","Expenses","Purchase Invoices"])

with tab_ap:
    if invoices:
        ap={}
        for inv in invoices:
            n=inv["suppliers"]["name"] if inv.get("suppliers") else "Unknown"
            ap[n]=ap.get(n,0)+(inv["landed_cost"] or 0)
        total_ap=sum(ap.values())
        rows=[]
        for n,a in sorted(ap.items(),key=lambda x:-x[1]):
            pct=a/total_ap*100 if total_ap else 0
            bar=f'<div style="background:rgba(0,0,0,0.05);border-radius:2px;height:3px;overflow:hidden"><div style="background:#c0392b;height:3px;width:{pct:.1f}%"></div></div>'
            rows.append([f'<span style="color:#1a1612">{n}</span>', f'<span style="font-family:DM Mono,monospace;color:#c0392b">{fmt(a)}</span>', bar])
        st.markdown(table_html(["Supplier","Owed","Share"],rows), unsafe_allow_html=True)
        st.markdown(f'<div style="margin-top:10px;font-family:DM Mono,monospace;font-size:12px;color:#847e76">Total payable: <span style="color:#c0392b">{fmt(total_ap)}</span></div>', unsafe_allow_html=True)
        if can("manage_payables"):
            st.markdown("")
            credit_invs=_select_with_optional_is_voided(
                "purchase_invoices",
                "invoice_id,purchase_price,freight_cost,suppliers(name),invoice_date,status",
            )
            credit_invs = [inv for inv in credit_invs if inv.get("status") == "On Credit"]
            if credit_invs:
                inv_opts={f'{i.get("suppliers",{}).get("name","?") if i.get("suppliers") else "?"} — {fmt((i["purchase_price"] or 0)+(i["freight_cost"] or 0))} — {fmt_dt(i["invoice_date"])}':i for i in credit_invs}
                with st.form("mark_paid"):
                    sel=st.selectbox("Mark Invoice as Paid",list(inv_opts.keys()))
                    if st.form_submit_button("Mark Paid",type="primary"):
                        inv=inv_opts[sel]; old=dict(inv)
                        sb.table("purchase_invoices").update({"status":"Paid"}).eq("invoice_id",inv["invoice_id"]).execute()
                        audit("purchase_invoices",inv["invoice_id"],"UPDATE",old_data=old,new_data={"status":"Paid"},changed_fields=["status"],reason="Manually marked as paid")
                        st.success("Marked as paid."); st.rerun()
    else:
        st.success("No outstanding payables.")

with tab_exp:
    col1,col2 = st.columns([1,1],gap="large")
    with col1:
        st.markdown('<h3>Log Expense</h3>', unsafe_allow_html=True)
        with st.form("exp_form"):
            desc=st.text_input("Description")
            c1,c2=st.columns(2); amt=c1.number_input("Amount",min_value=0.0); cat=c2.selectbox("Category",["Electricity","Transport","Rent","Salaries","Supplies","Other"])
            if st.form_submit_button("Log",type="primary",use_container_width=True):
                if not desc or not amt: st.error("Fill description and amount")
                else:
                    res=sb.table("expenses").insert({"description":desc,"amount":amt,"category":cat,"created_by":st.session_state.get("username")}).execute().data[0]
                    audit("expenses",res["expense_id"],"INSERT",new_data=res,reason="Expense logged")
                    st.success("Logged!"); st.rerun()
    with col2:
        st.markdown('<h3>Recent Expenses</h3>', unsafe_allow_html=True)
        all_exp=sb.table("expenses").select("*").order("expense_date",desc=True).limit(30).execute().data
        for e in all_exp:
            voided=e.get("is_voided",False)
            c1,c2=st.columns([4,1])
            opacity="opacity:0.35;" if voided else ""
            c1.markdown(f'<div style="{opacity}padding:6px 0;border-bottom:1px solid rgba(0,0,0,0.04)"><span style="font-size:13px;color:#1a1612">{e["description"]}</span> <span style="font-family:DM Mono,monospace;font-size:11.5px;color:#b8890a;margin-left:6px">{fmt(e["amount"])}</span> <span style="font-size:10px;color:#847e76;margin-left:5px">{e.get("expense_date","")}</span></div>', unsafe_allow_html=True)
            if not voided and can("void_expenses"):
                if c2.button("Void",key=f"ve_{e['expense_id']}"):
                    old=dict(e); sb.table("expenses").update({"is_voided":True}).eq("expense_id",e["expense_id"]).execute()
                    audit("expenses",e["expense_id"],"VOID",old_data=old,reason="Voided by admin")
                    st.rerun()

with tab_inv:
    all_invs=sb.table("purchase_invoices").select("*,catalog(name),suppliers(name)").order("invoice_date",desc=True).limit(50).execute().data
    if all_invs:
        rows=[]
        for inv in all_invs:
            voided=inv.get("is_voided",False)
            iname=inv["catalog"]["name"] if inv.get("catalog") else "—"
            sname=inv["suppliers"]["name"] if inv.get("suppliers") else "—"
            stat_c="#c0392b" if inv["status"]=="On Credit" else "#1e8449"
            rows.append([
                f'<span style="font-family:DM Mono,monospace;font-size:11px;color:#847e76">{"VOID" if voided else fmt_dt(inv["invoice_date"])}</span>',
                f'<span style="color:#1a1612">{iname}</span>',
                f'<span style="color:#4a4640">{sname}</span>',
                f'<span style="font-family:DM Mono,monospace;color:#4a4640">{inv["quantity"]}</span>',
                f'<span style="font-family:DM Mono,monospace;color:#b8890a">{fmt(inv["landed_cost"])}</span>',
                f'<span style="font-size:10px;color:{stat_c}">{inv["status"]}</span>',
            ])
        st.markdown(table_html(["Date","Item","Supplier","Qty","Landed Cost","Status"],rows), unsafe_allow_html=True)
    else:
        st.info("No purchase invoices yet.")
