# tabs/jugadores.py
import streamlit as st
import altair as alt
import pandas as pd


def render(filtered_df, teammates_df):
    st.subheader("Análisis de Compañeros")

    if teammates_df.empty:
        st.info("No hay datos de compañeros para mostrar con los filtros actuales.")
        return

    # Gráfico de Probabilidad de Victoria por Compañero
    prob_chart = alt.Chart(teammates_df).mark_bar().encode(
        x=alt.X("Compañero:N", sort="-y", title="Compañero"),
        y=alt.Y("Probabilidad_Victoria:Q",
                title="Probabilidad de Victoria (%)"),
        color=alt.Color("Probabilidad_Victoria:Q", scale=alt.Scale(
            scheme="redyellowgreen"), title="Probabilidad"),
        tooltip=["Compañero", "Probabilidad_Victoria", "Total_Partidos"]
    ).properties(title="Probabilidad de Victoria por Compañero")
    st.altair_chart(prob_chart, use_container_width=True)

    # Gráfico de Dispersión: Química vs. Rendimiento
    scatter = alt.Chart(filtered_df).mark_circle(size=100, opacity=0.7).encode(
        x=alt.X("Quimica:Q", title="Química", scale=alt.Scale(zero=False)),
        y=alt.Y("Rendiment:Q", title="Rendimiento",
                scale=alt.Scale(zero=False)),
        color=alt.Color("Result:N", scale=alt.Scale(
            domain=["W", "L", "N"], range=["#2ca02c", "#d62728", "grey"])),
        # size=alt.Size("Merit:Q", scale=alt.Scale(range=[50, 300]), title="Rating del Partido"),
        tooltip=["Teammate", "Quimica", "Rendiment", "Merit", "Result", "Date"]
    ).properties(title="Química vs. Rendimiento (Tamaño por Rating del Partido)")
    st.altair_chart(scatter, use_container_width=True)

    st.markdown("### Estadísticas de Compañeros")

    # Cálculo de win rate real (Victorias / Total_Partidos)
    teammates_df = teammates_df.copy()
    teammates_df["WinRate"] = (
        teammates_df["Victorias"] / teammates_df["Total_Partidos"] * 100).round(2)

    # Gráfico de línea: Acumulado de Merit por Compañero a lo largo del tiempo
    if "Teammate" in filtered_df.columns and "Merit" in filtered_df.columns and "Date" in filtered_df.columns:
        df_line = filtered_df.copy()
        df_line = df_line.sort_values("Date")
        df_line["Date"] = pd.to_datetime(df_line["Date"])
        df_line["Merit_Cumsum"] = df_line.groupby("Teammate")["Merit"].cumsum()

        line_chart = alt.Chart(df_line).mark_line().encode(
            x=alt.X("Date:T", title="Fecha"),
            y=alt.Y("Merit_Cumsum:Q", title="Merit Acumulado"),
            color=alt.Color("Teammate:N", title="Compañero"),
            tooltip=["Teammate", "Date", "Merit_Cumsum"]
        ).properties(title="Evolución Acumulada de Merit por Compañero")
        st.altair_chart(line_chart, use_container_width=True)
