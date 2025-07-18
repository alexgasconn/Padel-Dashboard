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

    # --- Gráfico 2: Cluster de Rendimiento ---
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

    # --- Gráfico 3: Evolución de Merit Acumulado por Lugar (corregido con relleno de ceros) ---
    st.markdown("#### Evolución del Aporte (Merit Acumulado) por Lugar")
    st.write("Muestra cómo ha evolucionado tu aporte neto (Merit) en tus 5 canchas más frecuentes. La línea se mantiene plana en los días sin partido.")

    if "Location" in filtered_df.columns and not filtered_df.empty:
        # Obtener los 5 lugares más frecuentes
        top_locations = filtered_df['Location'].value_counts().nlargest(5).index
        df_top = filtered_df[filtered_df['Location'].isin(top_locations)].copy()

        # Asegurar que Date es datetime
        df_top['Date'] = pd.to_datetime(df_top['Date'])

        # Crear un MultiIndex con todas las combinaciones de fechas y lugares
        date_range = pd.date_range(start=df_top['Date'].min(), end=df_top['Date'].max(), freq='D')
        multi_index = pd.MultiIndex.from_product([top_locations, date_range], names=['Location', 'Date'])

        # Sumar Merit diario por lugar
        df_played = df_top.groupby(['Location', 'Date'])['Merit'].sum().reset_index()

        # Completar días sin partidos con mérito = 0
        df_full = df_played.set_index(['Location', 'Date']).reindex(multi_index, fill_value=0).reset_index()

        # Calcular acumulado y preparar tooltip limpio
        df_full['Merit_Cumsum'] = df_full.groupby('Location')['Merit'].cumsum()
        df_full['Tooltip_Merit'] = df_full['Merit'].replace(0, np.nan)

        # Gráfico
        line_chart = alt.Chart(df_full).mark_line().encode(
            x=alt.X('Date:T', title='Fecha'),
            y=alt.Y('Merit_Cumsum:Q', title='Merit Acumulado'),
            color=alt.Color('Location:N', title='Lugar'),
            tooltip=[
                alt.Tooltip('Date:T', title='Fecha'),
                alt.Tooltip('Location:N', title='Lugar'),
                alt.Tooltip('Merit_Cumsum:Q', title='Merit Acumulado'),
                alt.Tooltip('Tooltip_Merit:Q', title='Merit de este Partido (si se jugó)')
            ]
        ).properties(
            title="Evolución de Merit Acumulado en Lugares Frecuentes"
        ).interactive()

        st.altair_chart(line_chart, use_container_width=True)


    # --- NUEVA SECCIÓN: Racha de los últimos 6 partidos ---
    st.markdown("#### 🏟️ Estado de Forma en Lugares Frecuentes")
    st.write("Racha de resultados en los últimos 6 partidos jugados en tus canchas más habituales.")
    if "Location" in filtered_df.columns and not filtered_df.empty:
        top_places_streak = filtered_df['Location'].value_counts().nlargest(6).index.tolist()

        if len(top_places_streak) > 0:
            rows = [top_places_streak[:3], top_places_streak[3:]]
            
            for row in rows:
                cols = st.columns(len(row))
                for i, place in enumerate(row):
                    with cols[i]:
                        st.markdown(f"**{place}**")

                        place_games = filtered_df[filtered_df['Location'] == place].sort_values('Date', ascending=False).head(6)

                        if not place_games.empty:
                            streak_icons = {'W': '✅', 'L': '❌', 'N': '➖'}
                            streak_str = " ".join([streak_icons.get(res, '❓') for res in place_games['Result'][::-1]])
                            wins_in_streak = (place_games['Result'] == 'W').sum()

                            st.metric(
                                label=f"Últimos {len(place_games)} Partidos",
                                value=streak_str,
                                delta=f"{wins_in_streak} Victorias",
                                delta_color="normal"
                            )
                        else:
                            st.write("No hay partidos recientes.")
        else:
            st.info("No hay lugares con suficientes partidos para mostrar una racha.")
    else:
        st.info("No hay datos disponibles para mostrar esta sección.")
