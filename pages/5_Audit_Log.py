import streamlit as st
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from styles import inject, section_title, fmt_dt
from users import require_permission
from sidebar import render_sidebar
from db import get_sb

st.set_page_config(page_title="Audit Log — Duka", page_icon="◌", layout="wide", initial_sidebar_state="expanded")
inject()
require_permission("view_audit")
render_sidebar()

sb = get_sb()
section_title("Audit Log", "Immutable record of all data changes")

st.markdown('<div style="background:rgba(184,137,10,0.06);border:1px solid rgba(184,137,10,0.18);border-radius:6px;padding:10px 14px;font-size:11.5px;color:#4a4640;margin-bottom:18px">All entries are append-only. Modifications and deletions of this log are blocked at the database level (RLS). Every change across all tables is recorded here permanently.</div>', unsafe_allow_html=True)

AC = {"INSERT":"#1e8449","UPDATE":"#b8890a","VOID":"#c0392b","ADJUST":"#1a6094","DELETE":"#c0392b"}
AC_BG = {"INSERT":"rgba(74,136,84,.1)","UPDATE":"rgba(196,154,44,.1)","VOID":"rgba(184,64,48,.1)","ADJUST":"rgba(26,96,148,0.09)","DELETE":"rgba(184,64,48,.1)"}

c1,c2,c3,c4 = st.columns([2,1,1,1])
search_q     = c1.text_input("Search reason or record ID", label_visibility="collapsed", placeholder="Search...")
table_filter = c2.selectbox("Table",["All","sales_orders","order_lines","catalog","inventory_ledger","purchase_invoices","expenses"])
action_filter= c3.selectbox("Action",["All","INSERT","UPDATE","VOID","ADJUST","DELETE"])
limit        = c4.selectbox("Show",[50,100,200])

q = sb.table("audit_log").select("*").order("performed_at",desc=True).limit(limit)
if table_filter  != "All": q=q.eq("table_name",table_filter)
if action_filter != "All": q=q.eq("action",action_filter)
logs = q.execute().data
if search_q:
    sq=search_q.lower()
    logs=[l for l in logs if sq in (l.get("record_id") or "").lower() or sq in (l.get("reason") or "").lower()]

if not logs:
    st.info("No audit entries found.")
else:
    # Summary row
    action_counts={}
    for l in logs: action_counts[l["action"]]=action_counts.get(l["action"],0)+1
    sc_html = " &nbsp;·&nbsp; ".join(f'<span style="color:{AC.get(a,"#847e76")};font-family:DM Mono,monospace;font-size:11px">{a}: {c}</span>' for a,c in sorted(action_counts.items()))
    st.markdown(f'<div style="font-size:11px;color:#847e76;margin-bottom:14px">{len(logs)} entries &nbsp;·&nbsp; {sc_html}</div>', unsafe_allow_html=True)

    for log in logs:
        action  = log.get("action","?")
        table   = log.get("table_name","?")
        by_name = log.get("performed_by_name") or log.get("performed_by_username") or "—"
        ac  = AC.get(action,"#847e76")
        abg = AC_BG.get(action,"rgba(232,224,204,0.04)")
        reason_txt = log.get("reason") or ""

        with st.expander(f"{action} · {table} · {by_name} · {fmt_dt(log.get('performed_at',''))}"):
            # Header row
            st.markdown(f"""
<div style="display:flex;gap:16px;align-items:center;margin-bottom:10px;flex-wrap:wrap">
  <span style="background:{abg};border:1px solid {ac}40;color:{ac};font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;padding:2px 8px;border-radius:3px;font-weight:500">{action}</span>
  <span style="font-family:DM Mono,monospace;font-size:11px;color:#847e76">table: <span style="color:#4a4640">{table}</span></span>
  <span style="font-family:DM Mono,monospace;font-size:11px;color:#847e76">id: <span style="color:#4a4640">{(log["record_id"] or "")[:20]}...</span></span>
  <span style="font-family:DM Mono,monospace;font-size:11px;color:#847e76">by: <span style="color:#4a4640">{by_name}</span></span>
</div>""", unsafe_allow_html=True)

            if reason_txt:
                st.markdown(f'<div style="background:rgba(184,137,10,0.06);border-left:2px solid #b8890a;padding:7px 11px;border-radius:0 3px 3px 0;font-size:12px;color:#4a4640;margin-bottom:10px"><span style="color:#b8890a;font-weight:500">Reason:</span> {reason_txt}</div>', unsafe_allow_html=True)

            if log.get("changed_fields"):
                st.markdown(f'<div style="font-size:11px;color:#847e76;margin-bottom:8px">Changed: <span style="color:#4a4640">{", ".join(log["changed_fields"])}</span></div>', unsafe_allow_html=True)

            if log.get("old_data") or log.get("new_data"):
                dc1,dc2 = st.columns(2)
                for col, key, label, val_color in [(dc1,"old_data","Before","#c0392b"),(dc2,"new_data","After","#1e8449")]:
                    with col:
                        if log.get(key):
                            st.markdown(f'<h3>{label}</h3>', unsafe_allow_html=True)
                            try:
                                d = json.loads(log[key]) if isinstance(log[key],str) else log[key]
                                rows_h = "".join(f'<tr><td style="padding:3px 8px;font-size:11px;color:#847e76">{k}</td><td style="padding:3px 8px;font-size:11px;font-family:DM Mono,monospace;color:{val_color}">{str(v)[:60]}</td></tr>' for k,v in d.items())
                                st.markdown(f'<table style="width:100%;border-collapse:collapse;background:#ffffff;border:1px solid rgba(0,0,0,0.05);border-radius:4px">{rows_h}</table>', unsafe_allow_html=True)
                            except: st.code(str(log[key])[:200])
