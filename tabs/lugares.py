# tabs/lugares.py
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np

def render(filtered_df, locations_df):
    st.subheader("Análisis de Rendimiento por Lugar")

    if locations_df.empty:
        st.info("No hay datos de lugares para mostrar con los filtros actuales.")
        return

    # --- Gráfico 1: Probabilidad de Victoria por Lugar ---
    st.markdown("#### Probabilidad de Victoria")
    st.write("Calcula una probabilidad de victoria ponderada para cada lugar, considerando múltiples factores de tu rendimiento.")
    
    location_prob_chart = alt.Chart(locations_df).mark_bar().encode(
        x=alt.X("Lugar:N", sort="-y", title="Lugar"),
        y=alt.Y("Probabilidad_Victoria:Q", title="Probabilidad de Victoria (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Probabilidad_Victoria:Q", scale=alt.Scale(scheme="redyellowgreen"), legend=alt.Legend(title="Probabilidad")),
        tooltip=["Lugar", "Probabilidad_Victoria", "Total_Partidos", "Win_Rate_Sin_Empates", "Merit_Avg"]
    ).properties(title="Probabilidad de Victoria por Lugar")
    st.altair_chart(location_prob_chart, use_container_width=True)
    st.divider()

    # --- Gráfico 2: Métricas de Rendimiento por Lugar ---
    st.markdown("#### Cluster de Rendimiento")
    st.write("Compara el Merit y Rendimiento promedio en cada lugar. El tamaño del punto indica el número de partidos jugados.")

    location_metrics = alt.Chart(locations_df).mark_point(size=150, filled=True, opacity=0.8).encode(
        x=alt.X("Merit_Avg:Q", title="Merit Promedio"),
        y=alt.Y("Rendiment_Avg:Q", title="Rendimiento Promedio"),
        color=alt.Color("Probabilidad_Victoria:Q", scale=alt.Scale(scheme="redyellowgreen"), title="Prob. Victoria"),
        size=alt.Size("Total_Partidos:Q", scale=alt.Scale(range=[100, 500]), title="Partidos Jugados"),
        tooltip=["Lugar", "Merit_Avg", "Rendiment_Avg", "Probabilidad_Victoria", "Total_Partidos"]
    ).properties(
        title="Métricas de Rendimiento por Lugar"
    ).interactive()
    st.altair_chart(location_metrics, use_container_width=True)
    st.divider()

    # --- Gráfico 3: Evolución de Merit Acumulado por Lugar ---
    st.markdown("#### Evolución del Aporte (Merit Acumulado) por Lugar")
    st.write("Muestra cómo ha evolucionado tu aporte neto (Merit) en tus 5 canchas más frecuentes a lo largo del tiempo.")
    
    # Comprobación de que 'Lugar' existe y el dataframe no está vacío
    if "Lugar" in filtered_df.columns and not filtered_df.empty:
        # Obtener los 5 lugares con más partidos
        top_places = filtered_df['Lugar'].value_counts().nlargest(5).index
        df_top = filtered_df[filtered_df['Lugar'].isin(top_places)].copy()

        # Proceder solo si df_top tiene datos después de filtrar
        if not df_top.empty:
            df_top['Date'] = pd.to_datetime(df_top['Date'])

            date_range = pd.date_range(start=df_top['Date'].min(), end=df_top['Date'].max(), freq='D')
            multi_index = pd.MultiIndex.from_product([top_places, date_range], names=['Lugar', 'Date'])

            df_played = df_top.groupby(['Lugar', 'Date'])['Merit'].sum().reset_index()
            df_full = df_played.set_index(['Lugar', 'Date']).reindex(multi_index, fill_value=0).reset_index()
            df_full['Merit_Cumsum'] = df_full.groupby('Lugar')['Merit'].cumsum()
            df_full['Tooltip_Merit'] = df_full['Merit'].replace(0, np.nan)

            line_chart = alt.Chart(df_full).mark_line().encode(
                x=alt.X('Date:T', title='Fecha'),
                y=alt.Y('Merit_Cumsum:Q', title='Merit Acumulado'),
                # CORREGIDO: Título de la leyenda y campo del tooltip
                color=alt.Color('Lugar:N', title='Lugar'),
                tooltip=[
                    alt.Tooltip('Date:T', title='Fecha'),
                    alt.Tooltip('Lugar:N', title='Lugar'),
                    alt.Tooltip('Merit_Cumsum:Q', title='Merit Acumulado'),
                    alt.Tooltip('Tooltip_Merit:Q', title='Merit de este Partido (si se jugó)')
                ]
            ).properties(
                # CORREGIDO: Título del gráfico
                title="Evolución de Merit Acumulado en Lugares Frecuentes"
            ).interactive()
            
            st.altair_chart(line_chart, use_container_width=True)