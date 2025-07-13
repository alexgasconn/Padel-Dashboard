# tabs/jugadores.py
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np

def render(filtered_df, teammates_df):
    st.subheader("Análisis de Rendimiento con Compañeros")

    if teammates_df.empty:
        st.info("No hay datos de compañeros para mostrar con los filtros actuales.")
        return

    # --- Gráfico 1: Probabilidad de Victoria (Ponderada) ---
    st.markdown("#### Probabilidad de Victoria por Compañero")
    st.write("Esta probabilidad se calcula ponderando múltiples factores: % de victorias, rendimiento, química, diferencia de juegos, merit y número de partidos jugados.")
    
    prob_chart = alt.Chart(teammates_df).mark_bar().encode(
        x=alt.X("Compañero:N", sort="-y", title="Compañero"),
        y=alt.Y("Probabilidad_Victoria:Q", title="Probabilidad de Victoria Ponderada (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Probabilidad_Victoria:Q", scale=alt.Scale(scheme="redyellowgreen"), legend=alt.Legend(title="Probabilidad")),
        tooltip=[
            alt.Tooltip("Compañero:N", title="Compañero"),
            alt.Tooltip("Probabilidad_Victoria:Q", title="Probabilidad Ponderada", format=".1f"),
            alt.Tooltip("Total_Partidos:Q", title="Partidos Jugados"),
            alt.Tooltip("Win_Rate_Sin_Empates:Q", title="% Victorias (Real)", format=".1f"),
            alt.Tooltip("Merit_Avg:Q", title="Merit Promedio", format=".2f")
        ]
    ).properties(
        title="Probabilidad de Victoria Ponderada por Compañero"
    )
    st.altair_chart(prob_chart, use_container_width=True)
    st.divider()

    # --- Gráfico 2: Evolución Acumulada de Merit con relleno de ceros ---
    st.markdown("#### Evolución del Aporte (Merit Acumulado)")
    st.write("Muestra cómo ha evolucionado tu aporte neto (Merit) con tus 5 compañeros más frecuentes. La línea se mantiene plana en los días sin partido.")
    
    if "Teammate" in filtered_df.columns and not filtered_df.empty:
        # Obtener los 5 compañeros con más partidos
        top_teammates = filtered_df['Teammate'].value_counts().nlargest(5).index
        df_top = filtered_df[filtered_df['Teammate'].isin(top_teammates)].copy()

        # Asegurar que Date es datetime
        df_top['Date'] = pd.to_datetime(df_top['Date'])

        # Crear un MultiIndex con todas las combinaciones de fechas y compañeros top
        date_range = pd.date_range(start=df_top['Date'].min(), end=df_top['Date'].max(), freq='D')
        multi_index = pd.MultiIndex.from_product([top_teammates, date_range], names=['Teammate', 'Date'])

        # Preparar los datos de partidos jugados
        df_played = df_top.groupby(['Teammate', 'Date'])['Merit'].sum().reset_index()

        # Crear el DataFrame completo rellenando los días sin partido
        df_full = df_played.set_index(['Teammate', 'Date']).reindex(multi_index, fill_value=0).reset_index()

        # Calcular la suma acumulada sobre el DataFrame completo
        df_full['Merit_Cumsum'] = df_full.groupby('Teammate')['Merit'].cumsum()
        
        # Filtrar para no mostrar el tooltip en los días con Merit = 0 (días no jugados)
        df_full['Tooltip_Merit'] = df_full['Merit'].replace(0, np.nan)


        line_chart = alt.Chart(df_full).mark_line().encode(
            x=alt.X('Date:T', title='Fecha'),
            y=alt.Y('Merit_Cumsum:Q', title='Merit Acumulado'),
            color=alt.Color('Teammate:N', title='Compañero'),
            tooltip=[
                alt.Tooltip('Date:T', title='Fecha'),
                alt.Tooltip('Teammate:N', title='Compañero'),
                alt.Tooltip('Merit_Cumsum:Q', title='Merit Acumulado'),
                alt.Tooltip('Tooltip_Merit:Q', title='Merit de este Partido (si se jugó)')
            ]
        ).properties(
            title="Evolución de Merit Acumulado con Compañeros Frecuentes"
        ).interactive()
        
        st.altair_chart(line_chart, use_container_width=True)
    st.divider()

    # --- Gráfico 3: Química vs. Rendimiento ---
    st.markdown("#### Relación Química vs. Rendimiento")
    st.write("Cada círculo es un partido. El color indica el resultado y el tamaño tu aporte (Merit) en ese partido.")

    if not filtered_df.empty:
        scatter = alt.Chart(filtered_df).mark_circle(size=100, opacity=0.7).encode(
            x=alt.X("Quimica:Q", title="Química", scale=alt.Scale(zero=False)),
            y=alt.Y("Rendiment:Q", title="Rendimiento", scale=alt.Scale(zero=False)),
            color=alt.Color("Result:N", scale=alt.Scale(domain=["W", "L", "N"], range=["#2ca02c", "#d62728", "grey"]), legend=alt.Legend(title="Resultado")),
            size=alt.Size("Merit:Q", scale=alt.Scale(range=[50, 500]), title="Merit del Partido"),
            tooltip=["Date", "Teammate", "Quimica", "Rendiment", "Merit", "Result"]
        ).properties(
            title="Química vs. Rendimiento"
        ).interactive()
        st.altair_chart(scatter, use_container_width=True)