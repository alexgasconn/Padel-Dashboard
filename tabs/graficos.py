# tabs/graficos.py
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np

def render(filtered_df):
    st.subheader("Gráficos Avanzados")

    if filtered_df.empty:
        st.info("No hay datos para mostrar gráficos avanzados con los filtros actuales.")
        return
        
    # --- Matriz de Correlación ---
    numeric_cols = ["Merit", "Quimica", "Rendiment", "Game-Diff"]
    corr_df = filtered_df[numeric_cols].corr().stack().reset_index().rename(
        columns={0: 'Correlation', 'level_0': 'Variable 1', 'level_1': 'Variable 2'}
    )
    
    corr_chart = alt.Chart(corr_df).mark_rect().encode(
        x=alt.X('Variable 1:N', title=None),
        y=alt.Y('Variable 2:N', title=None),
        color=alt.Color('Correlation:Q', scale=alt.Scale(scheme='redblue', domain=(-1, 1))),
        tooltip=[
            alt.Tooltip('Variable 1:N', title='Variable 1'),
            alt.Tooltip('Variable 2:N', title='Variable 2'),
            alt.Tooltip('Correlation:Q', title='Correlación', format='.2f')
        ]
    ).properties(
        title='Matriz de Correlación'
    )
    st.altair_chart(corr_chart, use_container_width=True)

    # --- Distribución de Merit por Resultado ---
    boxplot_chart = alt.Chart(filtered_df).mark_boxplot(extent='min-max').encode(
        x=alt.X('Result:N', title="Resultado"),
        y=alt.Y('Merit:Q', title="Merit"),
        color=alt.Color('Result:N', scale=alt.Scale(domain=["W", "L", "N"], range=["#2ca02c", "#d62728", "grey"]), legend=None)
    ).properties(
        title="Distribución de Merit por Resultado del Partido"
    )
    st.altair_chart(boxplot_chart, use_container_width=True)
    
    # --- Distribución de Diferencia de Juegos ---
    game_diff_chart = alt.Chart(filtered_df).mark_bar().encode(
        alt.X("Game-Diff:Q", bin=alt.Bin(maxbins=20), title="Diferencia de Juegos"),
        alt.Y('count()', title="Frecuencia"),
        color=alt.Color("Result:N", scale=alt.Scale(domain=["W", "L", "N"], range=["#2ca02c", "#d62728", "grey"])),
        tooltip=["Result", "count()"]
    ).properties(
        width=800, height=400, title="Distribución de Diferencia de Juegos por Resultado"
    )
    st.altair_chart(game_diff_chart, use_container_width=True)