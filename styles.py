import streamlit as st

FONTS_HTML = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=Jost:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
"""

GLOBAL_CSS = """
<style>
:root {
  --bg:        #0e0d0b;
  --s1:        #141210;
  --s2:        #1a1814;
  --s3:        #222018;
  --s4:        #2a2720;
  --gold:      #c49a2c;
  --gold2:     #e0b84a;
  --gold-bg:   rgba(196,154,44,0.10);
  --gold-bd:   rgba(196,154,44,0.22);
  --cream:     #e8e0cc;
  --cdim:      #9a9080;
  --cfaint:    #534f47;
  --danger:    #b84030;
  --success:   #4a8854;
  --info:      #3a6898;
  --warn:      #a07830;
  --bd:        rgba(232,224,204,0.07);
  --bd2:       rgba(232,224,204,0.13);
  --bd3:       rgba(232,224,204,0.20);
  --r:         4px;
  --rl:        8px;
  --rxl:       12px;
}

/* ── Reset & shell ─────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family: 'Jost', sans-serif !important;
}
[data-testid="stHeader"]  { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }

/* ── Sidebar ───────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--s1) !important;
  border-right: 1px solid var(--bd) !important;
  min-width: 220px !important;
  max-width: 220px !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Main content ──────────────────────────────────────────── */
.main .block-container {
  padding: 2rem 2.2rem 2rem 2.2rem !important;
  max-width: 1440px !important;
}

/* ── Typography ────────────────────────────────────────────── */
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

/* ── Metrics ───────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--s2) !important;
  border: 1px solid var(--bd) !important;
  border-radius: var(--rl) !important;
  padding: 1rem 1.1rem !important;
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

/* ── Inputs ────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stMultiSelect > div > div {
  background: var(--s3) !important;
  border: 1px solid var(--bd) !important;
  border-radius: var(--r) !important;
  color: var(--cream) !important;
  font-family: 'Jost', sans-serif !important;
  font-size: .85rem !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--gold-bd) !important;
  box-shadow: 0 0 0 2px rgba(196,154,44,0.07) !important;
}
.stSelectbox > div > div > div { color: var(--cream) !important; }
label[data-testid="stWidgetLabel"] p {
  font-size: .62rem !important; letter-spacing: .12em !important;
  text-transform: uppercase !important; color: var(--cfaint) !important;
  font-family: 'Jost', sans-serif !important;
}

/* ── Buttons ───────────────────────────────────────────────── */
.stButton > button {
  background: transparent !important;
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
  border-color: var(--gold) !important; color: #0e0d0b !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--gold2) !important; border-color: var(--gold2) !important;
}

/* ── Tabs ──────────────────────────────────────────────────── */
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

/* ── Expander ──────────────────────────────────────────────── */
[data-testid="stExpander"] {
  border: 1px solid var(--bd) !important;
  border-radius: var(--rl) !important;
  background: var(--s2) !important;
  overflow: hidden !important;
}
[data-testid="stExpander"] summary {
  font-family: 'Jost', sans-serif !important;
  font-size: .82rem !important; color: var(--cdim) !important;
  padding: .7rem 1rem !important;
}

/* ── Form ──────────────────────────────────────────────────── */
[data-testid="stForm"] {
  border: 1px solid var(--bd) !important;
  border-radius: var(--rl) !important;
  background: var(--s2) !important;
  padding: 1.1rem !important;
}

/* ── Dataframe ─────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--bd) !important;
  border-radius: var(--rl) !important;
  overflow: hidden !important;
}

/* ── Alerts ────────────────────────────────────────────────── */
[data-testid="stAlert"] {
  border-radius: var(--r) !important;
  border-left-width: 3px !important;
  font-family: 'Jost', sans-serif !important;
  font-size: .82rem !important;
}

/* ── Radio ─────────────────────────────────────────────────── */
[data-testid="stRadio"] > div { gap: .5rem !important; }
[data-testid="stRadio"] label { color: var(--cdim) !important; font-size: .82rem !important; }

/* ── Scrollbar ─────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--s4); border-radius: 2px; }

/* ── HR ────────────────────────────────────────────────────── */
hr { border: none !important; border-top: 1px solid var(--bd) !important; margin: 1.4rem 0 !important; }
</style>
"""

def inject():
    st.markdown(FONTS_HTML + GLOBAL_CSS, unsafe_allow_html=True)

# ── Component helpers ─────────────────────────────────────────

def badge(text, style="neutral"):
    S = {
        "neutral": "rgba(232,224,204,.07);color:#9a9080;border:1px solid rgba(232,224,204,.1)",
        "gold":    "rgba(196,154,44,.12);color:#c49a2c;border:1px solid rgba(196,154,44,.25)",
        "danger":  "rgba(184,64,48,.11);color:#b84030;border:1px solid rgba(184,64,48,.25)",
        "success": "rgba(74,136,84,.11);color:#4a8854;border:1px solid rgba(74,136,84,.25)",
        "info":    "rgba(58,104,152,.11);color:#3a6898;border:1px solid rgba(58,104,152,.25)",
        "warn":    "rgba(160,120,48,.11);color:#a07830;border:1px solid rgba(160,120,48,.25)",
        "admin":   "rgba(184,64,48,.13);color:#c05040;border:1px solid rgba(184,64,48,.3)",
        "manager": "rgba(196,154,44,.13);color:#c49a2c;border:1px solid rgba(196,154,44,.3)",
        "cashier": "rgba(74,136,84,.11);color:#5a9864;border:1px solid rgba(74,136,84,.25)",
    }
    s = S.get(style, S["neutral"])
    return f'<span style="display:inline-block;padding:2px 8px;border-radius:3px;font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;font-weight:500;background:{s.split(";")[0]};{s}">{text}</span>'

def kpi(label, value, color="cream", sub=None):
    C = {"cream":"#e8e0cc","gold":"#c49a2c","danger":"#b84030","success":"#4a8854","info":"#3a6898","warn":"#a07830"}
    c = C.get(color, C["cream"])
    s = f'<div style="font-family:DM Mono,monospace;font-size:10px;color:#534f47;margin-top:4px">{sub}</div>' if sub else ""
    return f"""<div style="background:#1a1814;border:1px solid rgba(232,224,204,0.07);border-radius:8px;padding:15px 17px">
  <div style="font-size:9.5px;letter-spacing:.15em;text-transform:uppercase;color:#534f47;margin-bottom:6px;font-family:Jost,sans-serif">{label}</div>
  <div style="font-family:Playfair Display,serif;font-size:26px;font-weight:500;color:{c};line-height:1">{value}</div>{s}
</div>"""

def section_title(title, sub=None):
    s = f'<p style="font-size:12px;color:#534f47;margin:3px 0 0;font-family:Jost,sans-serif">{sub}</p>' if sub else ""
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
    ths = "".join(f'<th style="text-align:left;padding:9px 13px;font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:#534f47;border-bottom:1px solid rgba(232,224,204,0.07);font-weight:500">{h}</th>' for h in headers)
    trs = ""
    for i, row in enumerate(rows):
        bg = "rgba(232,224,204,0.02)" if (striped and i % 2 == 0) else "transparent"
        tds = "".join(f'<td style="padding:10px 13px;font-size:12.5px;color:#9a9080;border-bottom:1px solid rgba(232,224,204,0.05)">{cell}</td>' for cell in row)
        trs += f'<tr style="background:{bg}">{tds}</tr>'
    return f'<div style="background:#1a1814;border:1px solid rgba(232,224,204,0.07);border-radius:8px;overflow:hidden"><table style="width:100%;border-collapse:collapse"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>'
