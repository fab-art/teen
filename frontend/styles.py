import streamlit as st

FONTS_HTML = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=Jost:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
"""

GLOBAL_CSS = """
<style>
:root {
  --bg:        #f5f3ee;
  --s1:        #ffffff;
  --s2:        #faf8f4;
  --s3:        #f0ede6;
  --s4:        #e0ddd5;
  --gold:      #b8890a;
  --gold2:     #9a7208;
  --gold-bg:   rgba(184,137,10,0.08);
  --gold-bd:   rgba(184,137,10,0.22);
  --cream:     #1a1612;
  --cdim:      #4a4640;
  --cfaint:    #847e76;
  --danger:    #c0392b;
  --success:   #1e8449;
  --info:      #1a6094;
  --warn:      #b7770d;
  --bd:        rgba(0,0,0,0.08);
  --bd2:       rgba(0,0,0,0.13);
  --bd3:       rgba(0,0,0,0.20);
  --r:         4px;
  --rl:        8px;
  --rxl:       12px;
}
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family: 'Jost', sans-serif !important;
}
[data-testid="stHeader"]  { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }
[data-testid="stSidebar"] {
  background: var(--s1) !important;
  border-right: 1px solid var(--bd) !important;
  min-width: 220px !important;
  max-width: 220px !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
[data-testid="stSidebarNav"] { display: none !important; }
.main .block-container {
  padding: 2rem 2.2rem 2rem 2.2rem !important;
  max-width: 1440px !important;
}
h1 {
  font-family: 'Playfair Display', serif !important;
  font-size: 1.85rem !important; font-weight: 500 !important;
  letter-spacing: .02em !important; color: var(--cream) !important;
  margin: 0 0 .15rem !important; line-height: 1.2 !important;
}
h2 {
  font-family: 'Playfair Display', serif !important;
  font-size: 1.3rem !important; font-weight: 500 !important;
  color: var(--cream) !important; margin: 0 !important;
}
h3 {
  font-family: 'Jost', sans-serif !important;
  font-size: .65rem !important; font-weight: 500 !important;
  letter-spacing: .15em !important; text-transform: uppercase !important;
  color: var(--cfaint) !important; margin: 0 0 .5rem !important;
}
p, li { color: var(--cdim) !important; }
[data-testid="stMetric"] {
  background: var(--s1) !important;
  border: 1px solid var(--bd) !important;
  border-radius: var(--rl) !important;
  padding: 1rem 1.1rem !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stMetricLabel"] p {
  font-size: .6rem !important; letter-spacing: .15em !important;
  text-transform: uppercase !important; color: var(--cfaint) !important;
  font-family: 'Jost', sans-serif !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Playfair Display', serif !important;
  font-size: 1.75rem !important; font-weight: 500 !important;
  color: var(--cream) !important;
}
[data-testid="stMetricDelta"] svg { display: none !important; }
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stMultiSelect > div > div {
  background: var(--s1) !important;
  border: 1px solid var(--bd2) !important;
  border-radius: var(--r) !important;
  color: var(--cream) !important;
  font-family: 'Jost', sans-serif !important;
  font-size: .85rem !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--gold-bd) !important;
  box-shadow: 0 0 0 2px rgba(184,137,10,0.10) !important;
}
.stSelectbox > div > div > div { color: var(--cream) !important; }
label[data-testid="stWidgetLabel"] p {
  font-size: .62rem !important; letter-spacing: .12em !important;
  text-transform: uppercase !important; color: var(--cfaint) !important;
  font-family: 'Jost', sans-serif !important;
}
.stButton > button {
  background: var(--s1) !important;
  border: 1px solid var(--bd2) !important;
  color: var(--cdim) !important;
  font-family: 'Jost', sans-serif !important;
  font-size: .68rem !important; font-weight: 500 !important;
  letter-spacing: .09em !important; text-transform: uppercase !important;
  border-radius: var(--r) !important;
  padding: .42rem .9rem !important;
  transition: all .15s !important;
}
.stButton > button:hover {
  border-color: var(--gold-bd) !important;
  color: var(--gold) !important; background: var(--gold-bg) !important;
}
.stButton > button[kind="primary"] {
  background: var(--gold) !important;
  border-color: var(--gold) !important; color: #ffffff !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--gold2) !important; border-color: var(--gold2) !important;
}
.nav-cards .stButton > button {
  height: 86px !important;
  flex-direction: column !important;
  font-size: .78rem !important;
  font-weight: 500 !important;
  letter-spacing: .04em !important;
  text-transform: none !important;
  border-radius: var(--rl) !important;
  border: 1.5px solid var(--bd2) !important;
  background: var(--s1) !important;
  color: var(--cdim) !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
  transition: all .15s !important;
  white-space: pre-wrap !important;
  line-height: 1.5 !important;
}
.nav-cards .stButton > button:hover {
  border-color: var(--gold-bd) !important;
  color: var(--gold) !important;
  background: var(--gold-bg) !important;
  box-shadow: 0 3px 10px rgba(184,137,10,0.12) !important;
  transform: translateY(-1px) !important;
}
[data-testid="stTabs"] { gap: 0 !important; }
[data-testid="stTabs"] > div:first-child {
  border-bottom: 1px solid var(--bd) !important; gap: 0 !important;
}
button[role="tab"] {
  font-family: 'Jost', sans-serif !important;
  font-size: .63rem !important; letter-spacing: .13em !important;
  text-transform: uppercase !important;
  color: var(--cfaint) !important; border-radius: 0 !important;
  padding: .45rem 1rem !important; background: transparent !important;
  border: none !important; border-bottom: 2px solid transparent !important;
}
button[role="tab"][aria-selected="true"] {
  color: var(--gold) !important;
  border-bottom-color: var(--gold) !important;
}
button[role="tab"]:hover { color: var(--cdim) !important; }
[data-testid="stExpander"] {
  border: 1px solid var(--bd) !important;
  border-radius: var(--rl) !important;
  background: var(--s1) !important;
  overflow: hidden !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stExpander"] summary {
  font-family: 'Jost', sans-serif !important;
  font-size: .82rem !important; color: var(--cdim) !important;
  padding: .7rem 1rem !important;
}
[data-testid="stForm"] {
  border: 1px solid var(--bd) !important;
  border-radius: var(--rl) !important;
  background: var(--s1) !important;
  padding: 1.1rem !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stDataFrame"] {
  border: 1px solid var(--bd) !important;
  border-radius: var(--rl) !important;
  overflow: hidden !important;
}
[data-testid="stAlert"] {
  border-radius: var(--r) !important;
  border-left-width: 3px !important;
  font-family: 'Jost', sans-serif !important;
  font-size: .82rem !important;
}
[data-testid="stRadio"] > div { gap: .5rem !important; }
[data-testid="stRadio"] label { color: var(--cdim) !important; font-size: .82rem !important; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--s4); border-radius: 2px; }
hr { border: none !important; border-top: 1px solid var(--bd) !important; margin: 1.4rem 0 !important; }
</style>
"""

def inject():
    st.markdown(FONTS_HTML + GLOBAL_CSS, unsafe_allow_html=True)

def badge(text, style="neutral"):
    S = {
        "neutral": "rgba(0,0,0,0.06);color:#4a4640;border:1px solid rgba(0,0,0,0.12)",
        "gold":    "rgba(184,137,10,0.10);color:#b8890a;border:1px solid rgba(184,137,10,0.25)",
        "danger":  "rgba(192,57,43,0.09);color:#c0392b;border:1px solid rgba(192,57,43,0.25)",
        "success": "rgba(30,132,73,0.09);color:#1e8449;border:1px solid rgba(30,132,73,0.25)",
        "info":    "rgba(26,96,148,0.09);color:#1a6094;border:1px solid rgba(26,96,148,0.25)",
        "warn":    "rgba(183,119,13,0.09);color:#b7770d;border:1px solid rgba(183,119,13,0.25)",
        "admin":   "rgba(192,57,43,0.10);color:#c0392b;border:1px solid rgba(192,57,43,0.3)",
        "manager": "rgba(184,137,10,0.11);color:#b8890a;border:1px solid rgba(184,137,10,0.3)",
        "cashier": "rgba(30,132,73,0.09);color:#1e8449;border:1px solid rgba(30,132,73,0.25)",
    }
    s = S.get(style, S["neutral"])
    bg = s.split(";")[0]
    return (f'<span style="display:inline-block;padding:2px 8px;border-radius:3px;'
            f'font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;'
            f'font-weight:500;background:{bg};{s}">{text}</span>')

def kpi(label, value, color="cream", sub=None):
    C = {
        "cream":   "#1a1612",
        "gold":    "#b8890a",
        "danger":  "#c0392b",
        "success": "#1e8449",
        "info":    "#1a6094",
        "warn":    "#b7770d",
    }
    c = C.get(color, C["cream"])
    s = f'<div style="font-family:DM Mono,monospace;font-size:10px;color:#847e76;margin-top:4px">{sub}</div>' if sub else ""
    return (
        f'<div style="background:#ffffff;border:1px solid rgba(0,0,0,0.08);'
        f'border-radius:8px;padding:15px 17px;box-shadow:0 1px 3px rgba(0,0,0,0.04)">'
        f'<div style="font-size:9.5px;letter-spacing:.15em;text-transform:uppercase;'
        f'color:#847e76;margin-bottom:6px;font-family:Jost,sans-serif">{label}</div>'
        f'<div style="font-family:Playfair Display,serif;font-size:26px;font-weight:500;'
        f'color:{c};line-height:1">{value}</div>{s}</div>'
    )

def section_title(title, sub=None):
    s = f'<p style="font-size:12px;color:#847e76;margin:3px 0 0;font-family:Jost,sans-serif">{sub}</p>' if sub else ""
    st.markdown(f'<div style="margin-bottom:1.4rem"><h1>{title}</h1>{s}</div>', unsafe_allow_html=True)

def fmt(n):
    try: return f"{float(n):,.2f}"
    except: return "—"

def fmt_dt(s):
    if not s: return "—"
    try:
        from datetime import datetime
        return datetime.fromisoformat(s.replace("Z","")).strftime("%d %b %Y %H:%M")
    except: return str(s)[:16]

def divider():
    st.markdown("<hr>", unsafe_allow_html=True)

def table_html(headers, rows, striped=True):
    ths = "".join(
        f'<th style="text-align:left;padding:9px 13px;font-size:9.5px;letter-spacing:.12em;'
        f'text-transform:uppercase;color:#847e76;border-bottom:1px solid rgba(0,0,0,0.08);'
        f'font-weight:500;background:#f5f3ee">{h}</th>'
        for h in headers
    )
    trs = ""
    for i, row in enumerate(rows):
        bg = "rgba(0,0,0,0.015)" if (striped and i % 2 == 0) else "#ffffff"
        tds = "".join(
            f'<td style="padding:10px 13px;font-size:12.5px;color:#4a4640;'
            f'border-bottom:1px solid rgba(0,0,0,0.04)">{cell}</td>'
            for cell in row
        )
        trs += f'<tr style="background:{bg}">{tds}</tr>'
    return (
        f'<div style="background:#ffffff;border:1px solid rgba(0,0,0,0.08);'
        f'border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.04)">'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>'
    )
