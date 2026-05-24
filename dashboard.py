"""Aba Dashboard — KPIs, gráficos Plotly e histórico de transações."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from modules import gsheets as gs

_COLORS = ["#C9A84C", "#2ECC71", "#3498DB", "#E74C3C", "#9B59B6", "#1ABC9C", "#E67E22", "#F39C12"]
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#EEF2F7",
    margin=dict(t=24, b=24, l=8, r=8),
)


def render() -> None:
    df   = gs.load_caixa()
    df_s = gs.load_socios()

    # ── KPIs ─────────────────────────────────────────────────────────
    entradas = df[df["Tipo"] == "Entrada"]["Valor"].sum() if not df.empty else 0.0
    saidas   = df[df["Tipo"] == "Saída"]["Valor"].sum()   if not df.empty else 0.0
    saldo    = entradas - saidas

    inad_count = 0
    mes_atual  = gs.MESES[date.today().month - 1]
    if not df_s.empty and mes_atual in df_s.columns:
        inad_count = int((df_s[mes_atual].astype(str).str.strip().str.lower() != "pago").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📥 Total Arrecadado",  f"R$ {entradas:,.2f}")
    c2.metric("📤 Total de Gastos",   f"R$ {saidas:,.2f}")
    c3.metric("💰 Saldo Atual",       f"R$ {saldo:,.2f}",
              delta=f"R$ {saldo:,.2f}", delta_color="normal")
    c4.metric(f"⚠️ Inadimplentes ({mes_atual})", f"{inad_count} sócios")

    st.divider()

    if df.empty:
        st.info("Nenhum dado encontrado. Acesse **Lançamentos** para começar a registrar movimentações.")
        return

    # ── Gráficos ──────────────────────────────────────────────────────
    col_l, col_r = st.columns([1.3, 1])

    with col_l:
        st.markdown("#### Gastos por Categoria")
        df_saidas = df[df["Tipo"] == "Saída"]
        if not df_saidas.empty:
            cat_sum = (
                df_saidas.groupby("Categoria")["Valor"]
                .sum().reset_index().sort_values("Valor", ascending=False)
            )
            fig_pie = px.pie(
                cat_sum, values="Valor", names="Categoria", hole=0.5,
                color_discrete_sequence=_COLORS,
            )
            fig_pie.update_traces(
                textposition="inside", textinfo="percent+label",
                marker=dict(line=dict(color="#060E1E", width=2)),
                pull=[0.04] + [0] * (len(cat_sum) - 1),
            )
            fig_pie.update_layout(**_LAYOUT, showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Nenhuma saída registrada ainda.")

    with col_r:
        st.markdown("#### Evolução do Saldo Acumulado")
        df_sorted = df.sort_values("Data").copy()
        df_sorted["Fluxo"] = df_sorted.apply(
            lambda r: r["Valor"] if r["Tipo"] == "Entrada" else -r["Valor"], axis=1
        )
        df_sorted["Saldo"] = df_sorted["Fluxo"].cumsum()

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=df_sorted["Data"].astype(str),
            y=df_sorted["Saldo"],
            mode="lines+markers",
            line=dict(color="#C9A84C", width=2.5),
            marker=dict(color="#E8C878", size=7),
            fill="tozeroy",
            fillcolor="rgba(201,168,76,0.1)",
            name="Saldo",
        ))
        fig_line.add_hline(y=0, line_dash="dot", line_color="#E74C3C", opacity=0.5)
        fig_line.update_layout(
            **_LAYOUT,
            xaxis_title="Data",
            yaxis_title="R$",
            yaxis_tickprefix="R$ ",
            showlegend=False,
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # ── Barras mensais ────────────────────────────────────────────────
    st.markdown("#### Entradas × Saídas por Mês")
    df_m = df.copy()
    df_m["Mês"] = pd.to_datetime(df_m["Data"], errors="coerce").dt.to_period("M").astype(str)
    df_pivot = (
        df_m.groupby(["Mês", "Tipo"])["Valor"].sum()
        .unstack(fill_value=0).reset_index()
    )
    fig_bar = go.Figure()
    if "Entrada" in df_pivot.columns:
        fig_bar.add_trace(go.Bar(
            x=df_pivot["Mês"], y=df_pivot["Entrada"],
            name="Entradas", marker_color="#2ECC71",
        ))
    if "Saída" in df_pivot.columns:
        fig_bar.add_trace(go.Bar(
            x=df_pivot["Mês"], y=df_pivot["Saída"],
            name="Saídas", marker_color="#E74C3C",
        ))
    fig_bar.update_layout(
        **_LAYOUT, barmode="group",
        xaxis_title="Mês", yaxis_title="R$",
        yaxis_tickprefix="R$ ",
        legend=dict(orientation="h", y=1.08),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Tabela recente ─────────────────────────────────────────────────
    st.divider()
    st.markdown("#### Últimas 15 Movimentações")
    df_show = df.sort_values("Data", ascending=False).head(15).copy()
    df_show["Valor"] = df_show["Valor"].apply(lambda v: f"R$ {v:,.2f}")
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Exportar CSV completo",
        csv_bytes,
        "fluxo_caixa_gremio_naval.csv",
        "text/csv",
    )
