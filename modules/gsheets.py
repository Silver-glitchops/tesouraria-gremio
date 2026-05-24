"""
Motor de dados: lê/escreve no Google Sheets.
Fallback automático para st.session_state quando as credenciais
não estiverem configuradas (modo demo local).
"""
import streamlit as st
import pandas as pd

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
CAIXA_COLS  = ["Data", "Descrição", "Tipo", "Categoria", "Valor"]
SOCIOS_COLS = ["Nome", "Telefone"] + MESES


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _credentials_ok() -> bool:
    try:
        return (
            "gcp_service_account" in st.secrets
            and "gsheets" in st.secrets
        )
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _get_client():
    """Cria e cacheia o cliente gspread para o ciclo de vida do processo."""
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=scopes
    )
    return gspread.authorize(creds)


def _get_worksheet(tab: str):
    client = _get_client()
    url = st.secrets["gsheets"]["spreadsheet_url"]
    return client.open_by_url(url).worksheet(tab)


# ─────────────────────────────────────────────────────────────────────────────
# GSheets — leitura com cache de 60 s
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def _fetch_caixa_remote() -> pd.DataFrame:
    ws = _get_worksheet("Fluxo_Caixa")
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=CAIXA_COLS)
    df = pd.DataFrame(records)
    df["Data"]  = pd.to_datetime(df["Data"], errors="coerce").dt.date
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
    return df


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_socios_remote() -> pd.DataFrame:
    ws = _get_worksheet("Socios")
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=SOCIOS_COLS)
    return pd.DataFrame(records)


# ─────────────────────────────────────────────────────────────────────────────
# Session-state fallback (modo demo sem credenciais)
# ─────────────────────────────────────────────────────────────────────────────

def _ss_caixa() -> pd.DataFrame:
    if "ss_caixa" not in st.session_state:
        st.session_state.ss_caixa = pd.DataFrame(columns=CAIXA_COLS)
    return st.session_state.ss_caixa.copy()


def _ss_socios() -> pd.DataFrame:
    if "ss_socios" not in st.session_state:
        st.session_state.ss_socios = pd.DataFrame(columns=SOCIOS_COLS)
    return st.session_state.ss_socios.copy()


# ─────────────────────────────────────────────────────────────────────────────
# API pública de leitura
# ─────────────────────────────────────────────────────────────────────────────

def load_caixa() -> pd.DataFrame:
    if not _credentials_ok():
        return _ss_caixa()
    try:
        return _fetch_caixa_remote()
    except Exception as e:
        st.warning(f"⚠️ GSheets indisponível ({e}). Usando dados locais.")
        return _ss_caixa()


def load_socios() -> pd.DataFrame:
    if not _credentials_ok():
        return _ss_socios()
    try:
        return _fetch_socios_remote()
    except Exception as e:
        st.warning(f"⚠️ GSheets indisponível ({e}). Usando dados locais.")
        return _ss_socios()


# ─────────────────────────────────────────────────────────────────────────────
# API pública de escrita
# ─────────────────────────────────────────────────────────────────────────────

def append_caixa(row: dict) -> None:
    """Adiciona uma linha ao fluxo de caixa."""
    # 1. Atualiza session state imediatamente (feedback instantâneo)
    df = _ss_caixa()
    st.session_state.ss_caixa = pd.concat(
        [df, pd.DataFrame([row])], ignore_index=True
    )
    # 2. Persiste no GSheets se possível
    if _credentials_ok():
        try:
            ws = _get_worksheet("Fluxo_Caixa")
            ws.append_row([
                str(row["Data"]),
                row["Descrição"],
                row["Tipo"],
                row["Categoria"],
                float(row["Valor"]),
            ])
            _fetch_caixa_remote.clear()
        except Exception as e:
            st.error(f"Erro ao persistir no GSheets: {e}")


def save_socios(df: pd.DataFrame) -> None:
    """Sobrescreve toda a planilha de sócios."""
    st.session_state.ss_socios = df.copy()
    if _credentials_ok():
        try:
            ws = _get_worksheet("Socios")
            ws.clear()
            ws.update([df.columns.tolist()] + df.astype(str).values.tolist())
            _fetch_socios_remote.clear()
        except Exception as e:
            st.error(f"Erro ao persistir no GSheets: {e}")


def add_socio(nome: str, telefone: str) -> bool:
    """Adiciona um sócio. Retorna False se já existe."""
    df = load_socios()
    if nome in df["Nome"].values:
        return False
    nova = {col: "Pendente" for col in SOCIOS_COLS}
    nova["Nome"]     = nome
    nova["Telefone"] = telefone
    df = pd.concat([df, pd.DataFrame([nova])], ignore_index=True)
    save_socios(df)
    return True
