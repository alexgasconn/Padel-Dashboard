# tabs/jugadores.py
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np


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

    # Gráfico de línea: Acumulado de Merit por Compañero a lo largo del tiempo (solo top 5 con más partidos)
    if "Teammate" in filtered_df.columns and "Merit" in filtered_df.columns and "Date" in filtered_df.columns:
        # Obtener top 5 compañeros con más partidos
        top_teammates = (
            filtered_df["Teammate"]
            .value_counts()
            .nlargest(5)
            .index
        )
        df_line = filtered_df[filtered_df["Teammate"].isin(top_teammates)].copy()
        df_line["Date"] = pd.to_datetime(df_line["Date"])
        df_line = df_line.sort_values("Date")

        # Crear rango de fechas completo
        all_dates = pd.date_range(df_line["Date"].min(), df_line["Date"].max())

        # Preparar DataFrame para asegurar que todos los compañeros tengan todas las fechas
        df_full = (
            df_line.set_index("Date")
            .groupby("Teammate")
            .apply(lambda x: x.reindex(all_dates, fill_value=np.nan))
            .reset_index(level=0)
            .reset_index()
            .rename(columns={"index": "Date"})
        )

        # Rellenar valores de Merit con 0 donde falten partidos
        df_full["Merit"] = df_full["Merit"].fillna(0)

        # Calcular Merit acumulado y rolling mean
        df_full["Merit_Cumsum"] = df_full.groupby("Teammate")["Merit"].cumsum()
        df_full["Merit_Cumsum_Roll"] = (
            df_full.groupby("Teammate")["Merit_Cumsum"].transform(lambda x: x.rolling(window=3, min_periods=1).mean())
        )

        line_chart = alt.Chart(df_full).mark_line().encode(
            x=alt.X("Date:T", title="Fecha"),
            y=alt.Y("Merit_Cumsum_Roll:Q", title="Merit Acumulado (Rolling Mean 3)"),
            color=alt.Color("Teammate:N", title="Compañero"),
            tooltip=["Teammate", "Date", "Merit_Cumsum_Roll"]
        ).properties(title="Evolución Acumulada de Merit por Compañero (Top 5, Rolling Mean 3)")
        st.altair_chart(line_chart, use_container_width=True)
