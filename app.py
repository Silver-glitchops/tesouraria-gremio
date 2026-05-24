"""
⚓ Tesouraria Grêmio Naval — app.py
Ponto de entrada da aplicação. Configure as credenciais do Google Sheets
em .streamlit/secrets.toml antes de rodar em produção.
"""
import streamlit as st

st.set_page_config(
    page_title="Tesouraria — Grêmio Naval",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — Tema Marítimo (Navy × Gold)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Nunito:ital,wght@0,300;0,400;0,600;1,400&display=swap');

    /* ── Cores ─────────────────────────────────────────────── */
    :root {
        --bg:          #060D1B;
        --surface:     #0C1A31;
        --card:        #102244;
        --border:      rgba(201, 168, 76, 0.18);
        --gold:        #C9A84C;
        --gold-hi:     #E8C878;
        --text:        #EEF2F7;
        --muted:       #7A8EA8;
        --success:     #27AE60;
        --danger:      #C0392B;
        --warn:        #E67E22;
    }

    /* ── Base ──────────────────────────────────────────────── */
    .stApp { background-color: var(--bg); color: var(--text); font-family: 'Nunito', sans-serif; }
    .block-container { padding-top: 1.5rem; }

    /* ── Tipografia ────────────────────────────────────────── */
    h1, h2, h3, h4 { font-family: 'Cinzel', serif !important; color: var(--gold) !important; letter-spacing: 0.04em; }
    h1 { font-size: 1.9rem !important; }
    h4 { font-size: 1rem !important; color: var(--gold-hi) !important; }

    /* ── Tabs ───────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface);
        border-radius: 10px;
        padding: 4px 6px;
        gap: 4px;
        border: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        color: var(--muted);
        font-family: 'Cinzel', serif;
        font-size: 0.82rem;
        border-radius: 8px;
        padding: 6px 14px;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background: var(--gold) !important;
        color: var(--bg) !important;
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab"]:hover { color: var(--gold-hi); }

    /* ── Metric cards ───────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem 1.25rem;
    }
    [data-testid="stMetricLabel"] p {
        color: var(--muted) !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.09em;
    }
    [data-testid="stMetricValue"]  { color: var(--gold-hi) !important; font-family: 'Cinzel', serif; font-size: 1.5rem !important; }
    [data-testid="stMetricDelta"]  { font-size: 0.8rem !important; }

    /* ── Buttons ────────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, var(--gold), var(--gold-hi));
        color: var(--bg);
        border: none;
        border-radius: 8px;
        font-family: 'Cinzel', serif;
        font-weight: 700;
        letter-spacing: 0.05em;
        padding: 0.45rem 1.25rem;
        transition: all 0.18s ease;
        box-shadow: 0 2px 8px rgba(201,168,76,0.25);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(201,168,76,0.45);
    }

    /* ── Form inputs ─────────────────────────────────────────── */
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox > div > div {
        background-color: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
    }
    .stDateInput input { background: var(--card) !important; color: var(--text) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }
    label { color: var(--muted) !important; font-size: 0.82rem; letter-spacing: 0.04em; }

    /* ── DataFrame ───────────────────────────────────────────── */
    .stDataFrame { border: 1px solid var(--border) !important; border-radius: 10px !important; }
    .stDataFrame [data-testid="stDataFrameResizable"] { border-radius: 10px; }

    /* ── Alerts ──────────────────────────────────────────────── */
    .stAlert { border-radius: 10px !important; }
    [data-testid="stNotificationContentSuccess"] { background: rgba(39,174,96,0.12) !important; }
    [data-testid="stNotificationContentError"]   { background: rgba(192,57,43,0.12) !important; }

    /* ── Expander ────────────────────────────────────────────── */
    details { border: 1px solid var(--border) !important; border-radius: 10px !important; background: var(--surface) !important; }
    summary { color: var(--gold) !important; font-family: 'Cinzel', serif; font-size: 0.88rem; }

    /* ── Divider ─────────────────────────────────────────────── */
    hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

    /* ── WhatsApp badge ──────────────────────────────────────── */
    .wpp-btn {
        display: inline-block;
        background: #25D366;
        color: #fff !important;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        text-decoration: none;
        letter-spacing: 0.03em;
        transition: opacity 0.15s;
    }
    .wpp-btn:hover { opacity: 0.85; }

    /* ── Scrollbar ───────────────────────────────────────────── */
    ::-webkit-scrollbar       { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--gold); border-radius: 3px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Cabeçalho
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center;padding:0.5rem 0 1rem;">
        <div style="font-size:2.4rem;">⚓</div>
        <h1 style="margin:0.1rem 0 0;">GRÊMIO NAVAL</h1>
        <p style="color:#7A8EA8;font-size:0.8rem;letter-spacing:0.18em;
                  text-transform:uppercase;margin-top:0.3rem;">
            Sistema Integrado de Tesouraria
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Banner de modo demo
try:
    import streamlit as _st
    if "gcp_service_account" not in _st.secrets:
        raise KeyError
except Exception:
    st.warning(
        "🔒 **Modo Demo** — os dados ficam apenas na memória desta sessão. "
        "Configure `.streamlit/secrets.toml` com suas credenciais do Google Sheets "
        "para persistência real.",
        icon="ℹ️",
    )

# ─────────────────────────────────────────────────────────────────────────────
# Abas
# ─────────────────────────────────────────────────────────────────────────────
from modules import dashboard, lancamentos, socios, relatorios, simulador  # noqa: E402

tabs = st.tabs([
    "📊 Dashboard",
    "💸 Lançamentos",
    "👥 Sócios & Cobranças",
    "📋 Relatórios",
    "🧮 Simulador de Eventos",
])

with tabs[0]: dashboard.render()
with tabs[1]: lancamentos.render()
with tabs[2]: socios.render()
with tabs[3]: relatorios.render()
with tabs[4]: simulador.render()
