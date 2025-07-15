# tabs/temporal.py
import streamlit as st
import altair as alt
import pandas as pd

def render(filtered_df):
    st.subheader("Análisis de Rendimiento a lo Largo del Tiempo")

    if filtered_df.empty:
        st.info("No hay datos para el análisis temporal con los filtros actuales.")
        return

    # --- Gráfico 1: Evolución del Rating (con Media Móvil) ---
    st.markdown("#### Evolución de tu Nivel General (Suavizada)")
    st.write("Esta línea muestra la **tendencia de tu Rating Acumulado** (media móvil de 5 partidos) para visualizar tu progreso a largo plazo de forma más clara.")

    # Asegurarse de que el dataframe esté ordenado por fecha
    df_sorted = filtered_df.sort_values("Date").reset_index(drop=True)

    # 1. Calcular el Rating Acumulado (Suma acumulada del Merit de cada partido)
    df_sorted['Rating_Acumulado'] = df_sorted['Merit'].cumsum()

    # 2. APLICAR LA MEDIA MÓVIL (ROLLING MEAN) DE 5 PARTIDOS
    df_sorted['Rating_Suavizado'] = df_sorted['Rating_Acumulado'].rolling(window=5, min_periods=1).mean()

    # 3. Crear el gráfico usando la nueva columna 'Rating_Suavizado'
    rating_line = alt.Chart(df_sorted).mark_line(
        color='cornflowerblue', 
        strokeWidth=3,
        point=alt.OverlayMarkDef(color="red", size=20, opacity=0) # Puntos invisibles para el tooltip
    ).encode(
        x=alt.X("Date:T", title="Fecha"),
        y=alt.Y('Rating_Suavizado:Q', title='Rating Acumulado (Suavizado)', scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip('Date:T', title='Fecha'),
            alt.Tooltip('Rating_Suavizado:Q', title='Rating Suavizado', format='.2f'),
            alt.Tooltip('Rating_Acumulado:Q', title='Rating Real (ese día)', format='.2f'),
            alt.Tooltip('Teammate:N', title='Compañero'),
            alt.Tooltip('Result:N', title='Resultado'),
        ]
    ).properties(
        title="Evolución del Rating Acumulado (Media Móvil de 5 Partidos)"
    ).interactive()
        
    st.altair_chart(rating_line, use_container_width=True)
    st.divider()

    # --- Gráfico 2: Heatmap por Momento del Día ---
    st.markdown("#### ¿Cuándo Juegas Más? Frecuencia por Momento del Día")
    st.write("El color de cada celda indica el **número de partidos jugados**. Pasa el ratón para ver el % de victorias y otras estadísticas.")
    
    temp_df_daily = filtered_df.copy()
    
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
        Partidos=("Result", "count"),
        WinRate=("Result", lambda x: (x == 'W').mean() * 100),
        Merit_Avg=("Merit", "mean")
    ).reset_index()
    
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    heatmap_daily = alt.Chart(heatmap_data_daily).mark_rect().encode(
        x=alt.X("TimeOfDay:N", title="Momento del Día", sort=time_order),
        y=alt.Y("Weekday:N", title="Día de la semana", sort=weekday_order),
        color=alt.Color("Partidos:Q", title="Nº de Partidos", scale=alt.Scale(scheme="blues")),
        tooltip=[
            alt.Tooltip("Weekday:N", title="Día"), 
            alt.Tooltip("TimeOfDay:N", title="Momento del Día"), 
            alt.Tooltip("Partidos:Q", title="Nº Partidos"),
            alt.Tooltip("WinRate:Q", title="% Victorias", format=".1f"), 
            alt.Tooltip("Merit_Avg:Q", title="Merit Promedio", format=".2f")
        ]
    ).properties(title="Heatmap de Frecuencia de Partidos por Momento del Día")
    
    st.altair_chart(heatmap_daily, use_container_width=True)
    st.divider()

    # --- Gráfico 3: Heatmap por Estación y Año ---
    st.markdown("#### Frecuencia de Juego Estacional")
    st.write("El color de cada celda indica el **número de partidos jugados** en cada estación. Pasa el ratón para ver el % de victorias.")
    
    temp_df_seasonal = filtered_df.copy()

    def get_season(month_name):
        if month_name in ["December", "January", "February"]: return "Invierno"
        if month_name in ["March", "April", "May"]: return "Primavera"
        if month_name in ["June", "July", "August"]: return "Verano"
        if month_name in ["September", "October", "November"]: return "Otoño"
        return "Desconocido"
        
    temp_df_seasonal['Season'] = temp_df_seasonal['Month'].apply(get_season)
    season_order = ["Primavera", "Verano", "Otoño", "Invierno"] # Orden cronológico-visual

    seasonal_data = temp_df_seasonal.groupby(["Year", "Season"]).agg(
        Partidos=("Result", "count"),
        WinRate=("Result", lambda x: (x == 'W').mean() * 100)
    ).reset_index()

    heatmap_seasonal = alt.Chart(seasonal_data).mark_rect().encode(
        x=alt.X('Season:N', title='Estación del Año', sort=season_order),
        y=alt.Y('Year:O', title='Año', axis=alt.Axis(labelAngle=0)),
        color=alt.Color('Partidos:Q', title='Nº de Partidos', scale=alt.Scale(scheme="blues")),
        tooltip=[
            alt.Tooltip('Year:O', title='Año'),
            alt.Tooltip('Season:N', title='Estación'),
            alt.Tooltip('Partidos:Q', title='Nº de Partidos'),
            alt.Tooltip('WinRate:Q', title='% Victorias', format='.1f')
        ]
    ).properties(
        title="Heatmap de Frecuencia de Partidos por Estación y Año"
    )

    st.altair_chart(heatmap_seasonal, use_container_width=True)



    # --- Gráfico 4: Evolución de Victorias y Derrotas Acumuladas ---
    st.markdown("#### 📊 Evolución de Victorias vs Derrotas")
    st.write("Visualiza cómo se ha ido acumulando tu número de victorias y derrotas a lo largo del tiempo. La separación entre ambas curvas refleja tu rendimiento global.")

    df_result = filtered_df.copy().sort_values("Date").reset_index(drop=True)
    df_result['Win'] = (df_result['Result'] == 'W').astype(int)
    df_result['Loss'] = (df_result['Result'] == 'L').astype(int)
    
    df_result['Wins_Acum'] = df_result['Win'].cumsum()
    df_result['Losses_Acum'] = df_result['Loss'].cumsum()

    chart_base = alt.Chart(df_result).encode(x=alt.X("Date:T", title="Fecha"))

    win_line = chart_base.mark_line(color="green", strokeWidth=3).encode(
        y=alt.Y("Wins_Acum:Q", title="Total Acumulado"),
        tooltip=[
            alt.Tooltip("Date:T", title="Fecha"),
            alt.Tooltip("Wins_Acum:Q", title="Victorias acumuladas")
        ]
    )

    loss_line = chart_base.mark_line(color="red", strokeDash=[4, 4], strokeWidth=2).encode(
        y="Losses_Acum:Q",
        tooltip=[
            alt.Tooltip("Date:T", title="Fecha"),
            alt.Tooltip("Losses_Acum:Q", title="Derrotas acumuladas")
        ]
    )

    result_chart = (win_line + loss_line).properties(
        title="Evolución Acumulada de Victorias y Derrotas"
    ).interactive()

    st.altair_chart(result_chart, use_container_width=True)
