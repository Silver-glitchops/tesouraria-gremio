"""Aba Relatórios — balanço mensal formatado pronto para envio à diretoria."""
from datetime import date

import pandas as pd
import streamlit as st

from modules import gsheets as gs


def render() -> None:
    st.subheader("📋 Gerador de Relatório Financeiro")

    c_sel, _ = st.columns([1, 2])
    with c_sel:
        mes_idx = st.selectbox(
            "Mês de referência",
            range(12),
            format_func=lambda i: gs.MESES[i],
            index=date.today().month - 1,
        )

    ano      = date.today().year
    mes_nome = gs.MESES[mes_idx]

    df   = gs.load_caixa()
    df_s = gs.load_socios()

    # Filtra pelo mês/ano selecionado
    if not df.empty:
        datas = pd.to_datetime(df["Data"], errors="coerce")
        df_mes = df[(datas.dt.month == mes_idx + 1) & (datas.dt.year == ano)].copy()
    else:
        df_mes = pd.DataFrame(columns=gs.CAIXA_COLS)

    entradas_mes = df_mes[df_mes["Tipo"] == "Entrada"]["Valor"].sum()
    saidas_mes   = df_mes[df_mes["Tipo"] == "Saída"]["Valor"].sum()
    saldo_mes    = entradas_mes - saidas_mes

    # Inadimplentes do mês
    inad_nomes: list[str] = []
    if not df_s.empty and mes_nome in df_s.columns:
        df_inad   = df_s[df_s[mes_nome].astype(str).str.strip().str.lower() != "pago"]
        inad_nomes = df_inad["Nome"].tolist()

    # ── KPIs ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Entradas — {mes_nome}", f"R$ {entradas_mes:,.2f}")
    c2.metric(f"Saídas — {mes_nome}",   f"R$ {saidas_mes:,.2f}")
    c3.metric("Saldo do Mês",           f"R$ {saldo_mes:,.2f}",
              delta=f"R$ {saldo_mes:,.2f}", delta_color="normal")
    c4.metric("Inadimplentes", f"{len(inad_nomes)} sócio(s)")

    st.divider()

    # ── Breakdowns ────────────────────────────────────────────────────
    col_e, col_s = st.columns(2)

    with col_e:
        st.markdown("**📥 Entradas por Categoria**")
        df_ent = df_mes[df_mes["Tipo"] == "Entrada"]
        if not df_ent.empty:
            resumo = (
                df_ent.groupby("Categoria")["Valor"]
                .sum().reset_index()
                .rename(columns={"Valor": "R$"})
                .sort_values("R$", ascending=False)
            )
            resumo["R$"] = resumo["R$"].apply(lambda v: f"R$ {v:,.2f}")
            st.dataframe(resumo, use_container_width=True, hide_index=True)
        else:
            st.info("Sem entradas no período.")

    with col_s:
        st.markdown("**📤 Saídas por Categoria**")
        df_sai = df_mes[df_mes["Tipo"] == "Saída"]
        if not df_sai.empty:
            resumo = (
                df_sai.groupby("Categoria")["Valor"]
                .sum().reset_index()
                .rename(columns={"Valor": "R$"})
                .sort_values("R$", ascending=False)
            )
            resumo["R$"] = resumo["R$"].apply(lambda v: f"R$ {v:,.2f}")
            st.dataframe(resumo, use_container_width=True, hide_index=True)
        else:
            st.info("Sem saídas no período.")

    st.divider()

    # ── Relatório Textual ─────────────────────────────────────────────
    st.markdown("#### 📄 Balanço para Envio à Diretoria")

    linhas_ent = _formatar_linhas(df_mes[df_mes["Tipo"] == "Entrada"],
                                  "(nenhuma entrada registrada)")
    linhas_sai = _formatar_linhas(df_mes[df_mes["Tipo"] == "Saída"],
                                  "(nenhuma saída registrada)")

    inad_bloco = (
        "\n".join(f"  • {n}" for n in inad_nomes)
        if inad_nomes
        else "  (todos os sócios estão adimplentes ✅)"
    )

    status_icon = "✅ SUPERÁVIT" if saldo_mes >= 0 else "❌ DÉFICIT"
    relatorio = f"""
╔══════════════════════════════════════════════════════════════════════╗
       GRÊMIO NAVAL — BALANÇO FINANCEIRO: {mes_nome.upper()} / {ano}
╚══════════════════════════════════════════════════════════════════════╝

📥  ENTRADAS .............. R$ {entradas_mes:>12,.2f}
{linhas_ent}
📤  SAÍDAS ................. R$ {saidas_mes:>12,.2f}
{linhas_sai}
──────────────────────────────────────────────────────────────────────
    {status_icon}:  R$ {abs(saldo_mes):>12,.2f}
──────────────────────────────────────────────────────────────────────

⚠️  SÓCIOS INADIMPLENTES EM {mes_nome.upper()} ({len(inad_nomes)}):
{inad_bloco}

Relatório gerado automaticamente pelo Sistema Integrado de Tesouraria.
    """.strip()

    st.text_area(
        "Texto do relatório (copie e cole onde precisar):",
        relatorio,
        height=460,
    )

    st.download_button(
        "📥 Baixar como .txt",
        relatorio.encode("utf-8"),
        f"balanco_{mes_nome.lower()}_{ano}.txt",
        "text/plain",
    )


def _formatar_linhas(df: pd.DataFrame, vazio: str) -> str:
    if df.empty:
        return f"    {vazio}\n"
    linhas = ""
    for _, r in df.iterrows():
        linhas += (
            f"    {'+'if r['Tipo']=='Entrada' else '-'} "
            f"R$ {r['Valor']:>10,.2f}  "
            f"[{r['Categoria']:<20}]  {r['Descrição']}\n"
        )
    return linhas
