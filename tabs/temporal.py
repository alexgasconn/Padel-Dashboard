# tabs/temporal.py
import streamlit as st
import altair as alt
import pandas as pd

def render(filtered_df):
    st.subheader("Análisis de Rendimiento a lo Largo del Tiempo")

    if filtered_df.empty:
        st.info("No hay datos para el análisis temporal con los filtros actuales.")
        return

    # --- Gráfico 1: Evolución del Rating ---
    st.markdown("#### Evolución de tu Nivel General")
    st.write("Esta línea muestra tu **Rating Acumulado** a lo largo del tiempo, que representa tu progreso y nivel general.")

    df_sorted = filtered_df.sort_values("Date").reset_index(drop=True)
    df_sorted['Rating_Acumulado'] = df_sorted['Merit'].cumsum()

    rating_line = alt.Chart(df_sorted).mark_line(color='cornflowerblue', strokeWidth=3).encode(
        x=alt.X("Date:T", title="Fecha"),
        y=alt.Y('Rating_Acumulado:Q', title='Rating Acumulado', scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip('Date:T', title='Fecha'), alt.Tooltip('Rating_Acumulado:Q', title='Rating Acumulado', format='.2f'), alt.Tooltip('Teammate:N', title='Compañero')]
    ).properties(
        title="Evolución del Rating Acumulado"
    ).interactive()
    
    st.altair_chart(rating_line, use_container_width=True)
    st.divider()

    # --- Gráfico 2: Heatmap por Momento del Día ---
    st.markdown("#### ¿Cuándo Juegas Mejor? Rendimiento por Momento del Día")
    
    temp_df_daily = filtered_df.copy()
    
    # Función para categorizar la hora
    def get_time_of_day(hour_obj):
        if pd.isna(hour_obj): return "No especificado"
        h = hour_obj.hour
        if 5 <= h <= 11: return "Mañana (5-11)"
        if 12 <= h <= 16: return "Mediodía (12-16)"
        if 17 <= h <= 20: return "Tarde (17-20)"
        return "Noche (21-4)"

    temp_df_daily['TimeOfDay'] = temp_df_daily['Hour'].apply(get_time_of_day)
    time_order = ["Mañana (5-11)", "Mediodía (12-16)", "Tarde (17-20)", "Noche (21-4)", "No especificado"]
    
    heatmap_data_daily = temp_df_daily.groupby(["Weekday", "TimeOfDay"]).agg(
        WinRate=("Result", lambda x: (x == 'W').mean() * 100),
        Merit_Avg=("Merit", "mean"),
        Partidos=("Result", "count")
    ).reset_index()
    
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    metric_to_show_daily = st.selectbox(
        "Elige la métrica para el heatmap diario:",
        ["WinRate", "Merit_Avg", "Partidos"],
        format_func=lambda x: {"WinRate": "% Victorias", "Merit_Avg": "Merit Promedio", "Partidos": "Nº Partidos"}[x],
        key="daily_heatmap_metric"
    )

    color_scale_daily = {
        "WinRate": alt.Scale(scheme="redyellowgreen", domain=[0, 100]),
        "Merit_Avg": alt.Scale(scheme="redblue"),
        "Partidos": alt.Scale(scheme="viridis")
    }[metric_to_show_daily]
    
    color_title_daily = {"WinRate": "% Victorias", "Merit_Avg": "Merit Promedio", "Partidos": "Nº Partidos"}[metric_to_show_daily]

    heatmap_daily = alt.Chart(heatmap_data_daily).mark_rect().encode(
        x=alt.X("TimeOfDay:N", title="Momento del Día", sort=time_order),
        y=alt.Y("Weekday:N", title="Día de la semana", sort=weekday_order),
        color=alt.Color(f"{metric_to_show_daily}:Q", title=color_title_daily, scale=color_scale_daily),
        tooltip=[
            alt.Tooltip("Weekday:N", title="Día"), 
            alt.Tooltip("TimeOfDay:N", title="Momento del Día"), 
            alt.Tooltip("WinRate:Q", title="% Victorias", format=".1f"), 
            alt.Tooltip("Merit_Avg:Q", title="Merit Promedio", format=".2f"), 
            alt.Tooltip("Partidos:Q", title="Nº Partidos")
        ]
    ).properties(title=f"Heatmap de {color_title_daily} por Momento del Día")
    
    st.altair_chart(heatmap_daily, use_container_width=True)
    st.divider()

    # --- Gráfico 3: Heatmap por Estación y Año ---
    st.markdown("#### Frecuencia y Rendimiento Estacional")
    
    temp_df_seasonal = filtered_df.copy()

    # Función para categorizar el mes en estaciones
    def get_season(month_name):
        if month_name in ["December", "January", "February"]: return "Invierno"
        if month_name in ["March", "April", "May"]: return "Primavera"
        if month_name in ["June", "July", "August"]: return "Verano"
        if month_name in ["September", "October", "November"]: return "Otoño"
        return "Desconocido"
        
    temp_df_seasonal['Season'] = temp_df_seasonal['Month'].apply(get_season)
    season_order = ["Invierno", "Primavera", "Verano", "Otoño"]

    seasonal_data = temp_df_seasonal.groupby(["Year", "Season"]).agg(
        Partidos=("Result", "count"),
        WinRate=("Result", lambda x: (x == 'W').mean() * 100)
    ).reset_index()

    metric_to_show_seasonal = st.selectbox(
        "Elige la métrica para el heatmap estacional:",
        ["Partidos", "WinRate"],
        format_func=lambda x: "Nº de Partidos" if x == "Partidos" else "% de Victorias",
        key="seasonal_heatmap_metric"
    )
    
    color_scale_seasonal = (
        alt.Scale(scheme="viridis") if metric_to_show_seasonal == "Partidos" 
        else alt.Scale(scheme="redyellowgreen", domain=[0, 100])
    )
    color_title_seasonal = "Nº de Partidos" if metric_to_show_seasonal == "Partidos" else "% de Victorias"

    heatmap_seasonal = alt.Chart(seasonal_data).mark_rect().encode(
        x=alt.X('Season:N', title='Estación del Año', sort=season_order),
        y=alt.Y('Year:O', title='Año', axis=alt.Axis(labelAngle=0)),
        color=alt.Color(f'{metric_to_show_seasonal}:Q', title=color_title_seasonal, scale=color_scale_seasonal),
        tooltip=[
            alt.Tooltip('Year:O', title='Año'),
            alt.Tooltip('Season:N', title='Estación'),
            alt.Tooltip('Partidos:Q', title='Nº de Partidos'),
            alt.Tooltip('WinRate:Q', title='% Victorias', format='.1f')
        ]
    ).properties(
        title=f"Heatmap de {color_title_seasonal} por Estación y Año"
    )

    st.altair_chart(heatmap_seasonal, use_container_width=True)