# tabs/lugares.py
import streamlit as st
import altair as alt
import pandas as pd

def render(filtered_df, locations_df):
    st.subheader("Análisis de Lugares")

    if locations_df.empty:
        st.info("No hay datos de lugares para mostrar con los filtros actuales.")
        return

    # Gráfico de Probabilidad de Victoria por Lugar
    location_prob_chart = alt.Chart(locations_df).mark_bar().encode(
        x=alt.X("Lugar:N", sort="-y", title="Lugar"),
        y=alt.Y("Probabilidad_Victoria:Q", title="Probabilidad de Victoria (%)"),
        color=alt.Color("Probabilidad_Victoria:Q", scale=alt.Scale(scheme="redyellowgreen")),
        tooltip=["Lugar", "Probabilidad_Victoria", "Total_Partidos"]
    ).properties(title="Probabilidad de Victoria por Lugar")
    st.altair_chart(location_prob_chart, use_container_width=True)

    # Gráfico de Métricas de Rendimiento por Lugar
    location_metrics = alt.Chart(locations_df).mark_point(size=150, filled=True, opacity=0.8).encode(
        x=alt.X("Merit_Avg:Q", title="Rating Promedio"),
        y=alt.Y("Rendiment_Avg:Q", title="Rendimiento Promedio"),
        color=alt.Color("Probabilidad_Victoria:Q", scale=alt.Scale(scheme="redyellowgreen"), title="Prob. Victoria"),
        size=alt.Size("Total_Partidos:Q", scale=alt.Scale(range=[100, 500]), title="Partidos Jugados"),
        tooltip=["Lugar", "Merit_Avg", "Rendiment_Avg", "Probabilidad_Victoria", "Total_Partidos"]
    ).properties(title="Métricas de Rendimiento por Lugar")
    st.altair_chart(location_metrics, use_container_width=True)



    if "Lugar" in filtered_df.columns and not filtered_df.empty:
        # Obtener los 5 compañeros con más partidos
        top_places = filtered_df['Lugar'].value_counts().nlargest(5).index
        df_top = filtered_df[filtered_df['Lugar'].isin(top_places)].copy()

        # Asegurar que Date es datetime
        df_top['Date'] = pd.to_datetime(df_top['Date'])

        # Crear un MultiIndex con todas las combinaciones de fechas y compañeros top
        date_range = pd.date_range(start=df_top['Date'].min(), end=df_top['Date'].max(), freq='D')
        multi_index = pd.MultiIndex.from_product([top_places, date_range], names=['Lugar', 'Date'])

        # Preparar los datos de partidos jugados
        df_played = df_top.groupby(['Lugar', 'Date'])['Merit'].sum().reset_index()

        # Crear el DataFrame completo rellenando los días sin partido
        df_full = df_played.set_index(['Lugar', 'Date']).reindex(multi_index, fill_value=0).reset_index()

        # Calcular la suma acumulada sobre el DataFrame completo
        df_full['Merit_Cumsum'] = df_full.groupby('Lugar')['Merit'].cumsum()
        
        # Filtrar para no mostrar el tooltip en los días con Merit = 0 (días no jugados)
        df_full['Tooltip_Merit'] = df_full['Merit'].replace(0, np.nan)


        line_chart = alt.Chart(df_full).mark_line().encode(
            x=alt.X('Date:T', title='Fecha'),
            y=alt.Y('Merit_Cumsum:Q', title='Merit Acumulado'),
            color=alt.Color('Lugar:N', title='Compañero'),
            tooltip=[
                alt.Tooltip('Date:T', title='Fecha'),
                alt.Tooltip('Lugar:N', title='Compañero'),
                alt.Tooltip('Merit_Cumsum:Q', title='Merit Acumulado'),
                alt.Tooltip('Tooltip_Merit:Q', title='Merit de este Partido (si se jugó)')
            ]
        ).properties(
            title="Evolución de Merit Acumulado con Compañeros Frecuentes"
        ).interactive()
        
        st.altair_chart(line_chart, use_container_width=True)
    st.divider()