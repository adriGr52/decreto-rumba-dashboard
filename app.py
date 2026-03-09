"""
Acercamiento al Impacto — Decreto Rumba
Dashboard interactivo para medición de impacto del Decreto 293/2025
Secretaría Distrital de Salud de Bogotá
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json
try:
    import geopandas as gpd
    import folium
    from streamlit_folium import st_folium
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

# ── Configuración ──────────────────────────────────────────────
st.set_page_config(
    page_title="Acercamiento al Impacto — Decreto Rumba",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Colores ────────────────────────────────────────────────────
FOCAL = "#16A34A"
CONTROL = "#64748B"
DECRETO = "#DC2626"
ACCENT = "#0D7377"
ROJO = "#DC2626"
AMARILLO = "#D97706"
VERDE = "#16A34A"
AZUL_PRE = "#3B82F6"
ROJO_POST = "#EF4444"

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Arial", color="#E2E8F0", size=12),
    margin=dict(l=60, r=30, t=60, b=80),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=470,
)

FOOTER = "Fuente: SIVELCE (dic 2024 – feb 2026) | SDS Bogotá | Marzo 2026"

MES_CORTO = {
    "01": "ene", "02": "feb", "03": "mar", "04": "abr",
    "05": "may", "06": "jun", "07": "jul", "08": "ago",
    "09": "sep", "10": "oct", "11": "nov", "12": "dic",
}


def mes_label(m):
    parts = m.split("-")
    return f"{MES_CORTO.get(parts[1], parts[1])}-{parts[0][2:]}"


# ── Carga de datos ─────────────────────────────────────────────
@st.cache_data
def load_data():
    with open("dashboard_data.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_shapefile():
    if not HAS_GEO:
        return None
    gdf = gpd.read_file("shapes/ZonaDecretoRumba.shp")
    manual_match = {
        'BOSA CENTRO': 'APROBADA', 'BOYACA SANTA MARIA': 'APROBADA',
        '1 DE MAYO': 'NO_APROBADA', 'CUADRA PICHA': 'APROBADA',
        'LA FAVORITA': 'APROBADA', 'RESTREPO': 'NO_APROBADA',
        'LOMBARDIA': 'APROBADA', 'MARICHUELA': 'NO_APROBADA',
        'CALLE 172A': 'APROBADA', 'ALAMOS': 'APROBADA',
        'MODELIA': 'APROBADA', 'GALAN': 'APROBADA',
        'FERIAS': 'APROBADA', 'ZONA ROSA': 'APROBADA',
        'GALERIAS': 'NO_APROBADA', 'SUBAZAR': 'APROBADA',
        'CHAPINERO': 'APROBADA', 'LOS PORTICOS': 'APROBADA',
        'NORMANDIA': 'NO_APROBADA', 'CALLE 8 SUR': 'APROBADA',
        'MARLY': 'APROBADA', 'CALLE 116': 'NO_APROBADA',
        'CENTRO FONTIBON': 'APROBADA', 'SAN JOSE': 'NO_APROBADA',
        'PALERMO': 'NO_APROBADA', 'SAN ANDRESITO': 'APROBADA',
        'LAS FERIAS ZONA I': 'APROBADA',
    }
    zona_decreto_name = {
        'BOSA CENTRO': 'Bosa Centro', 'BOYACA SANTA MARIA': 'Boyacá - Santa María',
        'CUADRA PICHA': 'Cuadra Alegre', 'LA FAVORITA': 'La Favorita',
        'LOMBARDIA': 'Lombardía', 'CALLE 172A': 'Calle 172A',
        'ALAMOS': 'Álamos', 'MODELIA': 'Modelia', 'GALAN': 'El Galán',
        'FERIAS': 'Las Ferias Zona 2', 'ZONA ROSA': 'Zona Rosa',
        'SUBAZAR': 'Subazar', 'CHAPINERO': 'Chapinero Central',
        'LOS PORTICOS': 'Los Pórticos', 'CALLE 8 SUR': 'Calle Octava Sur',
        'MARLY': 'Marly', 'CENTRO FONTIBON': 'Centro Fontibón',
        'SAN ANDRESITO': 'San Andresito San José',
        'LAS FERIAS ZONA I': 'Las Ferias Zona 1',
    }
    gdf['ESTADO'] = gdf['NOMBRE_ZON'].map(manual_match).fillna('DESCONOCIDO')
    gdf['ZONA_DECRETO'] = gdf['NOMBRE_ZON'].map(zona_decreto_name).fillna('')
    gdf = gdf.to_crs(epsg=4326)
    return gdf


D = load_data()
META = D["meta"]

FRANJA_DISPLAY = {
    "F1": "🔴 Crítica (3-5 AM) — Ventana del decreto",
    "F2": "Ampliada (2-5 AM)",
    "F3": "Ampliada (3-6 AM)",
    "F4": "Extendida (1-6 AM)",
    "F5": "🔵 Nocturna (10 PM-6 AM) — Mayor poder",
    "F6": "Madrugada (12-6 AM)",
}

FRANJA_MAP = {f["id"]: f["nombre"] for f in META["franjas"]}
FRANJA_IDS = list(FRANJA_MAP.keys())
TIP_MAP = {t["id"]: t["nombre"] for t in META["tipologias"]}
TIP_IDS = list(TIP_MAP.keys())
MESES = META["meses"]
MESES_LABELS = [mes_label(m) for m in MESES]
CORTE = META["corte"]
TOTAL = META["total"]
LOC_FOCAL = META["locFocal"]
LOC_CONTROL = META["locControl"]

# Map zona localidad → clean loc name for semáforo linkage
ZONA_LOC_MAP = {
    'BOSA': 'Bosa', 'ENGATIVA': 'Engativa', 'KENNEDY': 'Kennedy',
    'LOS MARTIRES': 'Martires', 'SUBA': 'Suba', 'USAQUEN': 'Usaquen',
    'FONTIBON': 'Fontibon', 'PUENTE ARANDA': 'Puente Aranda',
    'CHAPINERO': 'Chapinero',
}


# ── Helpers ────────────────────────────────────────────────────
def get_series(fid, tid):
    return D["series"].get(f"{fid}_{tid}", [])

def get_series_loc(fid, loc):
    return D["seriesLoc"].get(f"{fid}_{loc}", [])

def get_did(fid, tid):
    return D["did"].get(f"{fid}_{tid}", {})

def get_sem(fid, tid):
    return D["sem"].get(f"{fid}_{tid}", [])

def get_poder(fid, tid, diseno):
    return D["poder"].get(f"{fid}_{tid}_{diseno}", {})

def cat_xaxis():
    return dict(
        type="category", categoryorder="array", categoryarray=MESES_LABELS,
        gridcolor="rgba(255,255,255,0.08)", tickangle=-45,
    )

def make_layout(**overrides):
    """Build layout dict merging PLOTLY_LAYOUT base with overrides (no conflicts)."""
    layout = dict(PLOTLY_LAYOUT)
    layout.update(overrides)
    return layout


def decreto_vline(fig):
    corte_label = mes_label(CORTE)
    fig.add_shape(
        type="line", x0=corte_label, x1=corte_label, y0=0, y1=1,
        yref="paper", line=dict(color=DECRETO, width=2, dash="dash"),
    )
    fig.add_annotation(
        x=corte_label, y=1, yref="paper", text="Decreto 293",
        showarrow=False, font=dict(color=DECRETO, size=11), yanchor="bottom",
    )


# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏛️ DECRETO RUMBA")
    st.caption("Acercamiento al Impacto")
    st.divider()

    st.markdown("**Franja horaria**")
    franja_sel = st.radio(
        "Franja", FRANJA_IDS,
        format_func=lambda x: FRANJA_DISPLAY.get(x, FRANJA_MAP[x]),
        label_visibility="collapsed",
    )
    st.caption(
        "La franja crítica (3-5 AM) es donde aplica la diferencia "
        "regulatoria del decreto. Franjas más amplias tienen más eventos "
        "y mayor poder estadístico para detectar cambios."
    )

    st.divider()
    st.markdown("**Tipología**")
    tip_sel = st.radio(
        "Tipología", TIP_IDS,
        format_func=lambda x: TIP_MAP[x],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption(f"SIVELCE (depurado)  \ndic 2024 – feb 2026  \nN = {TOTAL:,}")

franja_label = FRANJA_DISPLAY.get(franja_sel, FRANJA_MAP[franja_sel])
tip_label = TIP_MAP[tip_sel]

# ── Título ─────────────────────────────────────────────────────
st.markdown(
    "<h2 style='margin-bottom:0'>Acercamiento al Impacto — Decreto Rumba</h2>"
    "<p style='color:#94A3B8;margin-top:0'>"
    "Secretaría Distrital de Salud de Bogotá | Fuente: SIVELCE"
    "</p>",
    unsafe_allow_html=True,
)

# ── Tabs ───────────────────────────────────────────────────────
tabs = st.tabs([
    "📊 General", "🗺️ Mapa", "📍 Localidades", "🚦 Semáforo",
    "📐 DiD", "🍺 Alcohol", "⚡ Poder", "📖 Metodología",
])

# ================================================================
# TAB 1: GENERAL
# ================================================================
with tabs[0]:
    st.info(
        "📊 **Evolución mensual de eventos** en la franja y tipología seleccionadas. "
        "La línea verde (focal) debería separarse de la gris (control) después del "
        "decreto si hay efecto. Hover para ver alcohol."
    )

    s = get_series(franja_sel, tip_sel)
    if not s:
        st.warning("Sin datos para esta combinación.")
    else:
        pre = [r for r in s if r["m"] < CORTE]
        post = [r for r in s if r["m"] >= CORTE]

        sum_prF = sum(r["F"] for r in pre)
        sum_poF = sum(r["F"] for r in post)
        sum_prC = sum(r["C"] for r in pre)
        sum_poC = sum(r["C"] for r in post)

        n_pre_m = max(len(pre), 1)
        n_post_m = max(len(post), 1)
        avg_prF = sum_prF / n_pre_m
        avg_poF = sum_poF / n_post_m
        avg_prC = sum_prC / n_pre_m
        avg_poC = sum_poC / n_post_m

        delta_F = ((avg_poF / avg_prF) - 1) * 100 if avg_prF > 0 else 0
        delta_C = ((avg_poC / avg_prC) - 1) * 100 if avg_prC > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pre Focal (7m)", f"{sum_prF:,}", f"{delta_F:+.1f}% vs prom/mes pre")
        c2.metric("Post Focal (8m)", f"{sum_poF:,}")
        c3.metric("Pre Control (7m)", f"{sum_prC:,}", f"{delta_C:+.1f}% vs prom/mes pre")
        c4.metric("Post Control (8m)", f"{sum_poC:,}")

        total_franja = sum_prF + sum_poF + sum_prC + sum_poC
        st.caption(
            f"N eventos en franja seleccionada: {total_franja:,} | "
            f"Franja: {franja_label} | Tipología: {tip_label} | "
            f"Focal = 9 localidades con zonas de rumba | Control = 5 localidades sin zonas"
        )

        st.divider()

        # Serie temporal
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=MESES_LABELS, y=[r["F"] for r in s], name="Focal",
            line=dict(color=FOCAL, width=2.5), mode="lines+markers",
            marker=dict(size=6),
            hovertemplate="Mes: %{x}<br>Focal: %{y}<br>Alcohol: %{customdata}<extra></extra>",
            customdata=[r["aF"] for r in s],
        ))
        fig.add_trace(go.Scatter(
            x=MESES_LABELS, y=[r["C"] for r in s], name="Control",
            line=dict(color=CONTROL, width=2.5), mode="lines+markers",
            marker=dict(size=6),
            hovertemplate="Mes: %{x}<br>Control: %{y}<br>Alcohol: %{customdata}<extra></extra>",
            customdata=[r["aC"] for r in s],
        ))
        fig.update_layout(**make_layout(
            title=f"Serie temporal — {franja_label} | {tip_label}",
            xaxis_title="Mes", yaxis_title="Eventos",
            xaxis=cat_xaxis(),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        ))
        decreto_vline(fig)
        st.plotly_chart(fig, use_container_width=True)

        # % Alcohol
        pct_alc_F = [(r["aF"] / r["F"] * 100) if r["F"] > 0 else 0 for r in s]
        pct_alc_C = [(r["aC"] / r["C"] * 100) if r["C"] > 0 else 0 for r in s]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=MESES_LABELS, y=pct_alc_F, name="% Alcohol Focal",
            line=dict(color=FOCAL, width=2), mode="lines+markers", marker=dict(size=5),
        ))
        fig2.add_trace(go.Scatter(
            x=MESES_LABELS, y=pct_alc_C, name="% Alcohol Control",
            line=dict(color=CONTROL, width=2), mode="lines+markers", marker=dict(size=5),
        ))
        fig2.update_layout(**make_layout(
            title=f"% eventos con presencia de alcohol — {franja_label} | {tip_label}",
            xaxis_title="Mes", yaxis_title="% con alcohol",
            xaxis=cat_xaxis(),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        ))
        decreto_vline(fig2)
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(FOOTER)


# ================================================================
# TAB 2: MAPA
# ================================================================
with tabs[1]:
    st.info(
        "🗺️ **Mapa de las 27 zonas evaluadas.** Verde = aprobada (19 zonas en 9 localidades). "
        "Gris = no aprobada (8 zonas). Click en una zona para ver sus datos."
    )

    st.markdown(f"#### 🗺️ 19 Zonas Focalizadas del Decreto 293/2025")

    _map_ok = True
    if not HAS_GEO:
        st.error("Las dependencias geográficas (geopandas, folium) no están disponibles. "
                 "Verifica que requirements.txt incluya geopandas, folium y streamlit-folium.")
        _map_ok = False
    else:
        try:
            gdf = load_shapefile()
            if gdf is None:
                raise ImportError("geopandas no disponible")
        except Exception as e:
            st.error(f"No se pudo cargar el shapefile: {e}")
            _map_ok = False

    if _map_ok:
        # Get semáforo for last month to color approved zones
        sem_tip_map = "T1"  # Default to siniestros viales
        sem_data = get_sem(franja_sel, sem_tip_map)
        post_meses_all = sorted(set(r["m"] for r in sem_data)) if sem_data else []
        last_month = post_meses_all[-1] if post_meses_all else None

        loc_semaforo = {}
        if last_month:
            for entry in sem_data:
                if entry["m"] == last_month:
                    loc_semaforo[entry["l"]] = entry["s"]

        color_sem = {"R": "#DC2626", "A": "#D97706", "V": "#16A34A"}

        # Build folium map
        fmap = folium.Map(
            location=[4.65, -74.1], zoom_start=11,
            tiles="CartoDB dark_matter",
        )

        for _, row in gdf.iterrows():
            is_approved = row['ESTADO'] == 'APROBADA'

            if is_approved:
                loc_raw = str(row['LocaNombre']).strip().upper()
                loc_clean = ZONA_LOC_MAP.get(loc_raw, None)
                sem_code = loc_semaforo.get(loc_clean, None) if loc_clean else None

                if sem_code and sem_code in color_sem:
                    fill_color = color_sem[sem_code]
                    sem_label = {"R": "ROJO", "A": "AMARILLO", "V": "VERDE"}.get(sem_code, "—")
                else:
                    fill_color = VERDE
                    sem_label = "—"
            else:
                fill_color = "#6B7280"
                sem_label = "N/A"
                loc_clean = "—"

            zona_name = row['ZONA_DECRETO'] if row['ZONA_DECRETO'] else row['NOMBRE_ZON']
            popup_html = (
                f"<div style='font-family:Arial;font-size:13px;min-width:200px'>"
                f"<b>{zona_name}</b><br>"
                f"Localidad: {row['LocaNombre']}<br>"
                f"Barrio: {row['BARRIO']}<br>"
                f"Área: {row['AREA_Ha']:.2f} Ha<br>"
                f"Estado: <b>{'✅ Aprobada' if is_approved else '❌ No aprobada'}</b><br>"
                f"Semáforo ({TIP_MAP.get(sem_tip_map, '')}, {mes_label(last_month) if last_month else '—'}): "
                f"<b>{sem_label}</b>"
                f"</div>"
            )

            folium.GeoJson(
                row.geometry.__geo_interface__,
                style_function=lambda feature, fc=fill_color, approved=is_approved: {
                    'fillColor': fc,
                    'color': '#E2E8F0' if approved else '#4B5563',
                    'weight': 2 if approved else 1,
                    'fillOpacity': 0.6 if approved else 0.25,
                },
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=zona_name,
            ).add_to(fmap)

        st_folium(fmap, width=None, height=550, use_container_width=True)

        if last_month:
            st.caption(
                f"Color de zonas aprobadas: semáforo de {TIP_MAP.get(sem_tip_map, '')} "
                f"({franja_label}) para {mes_label(last_month)}. "
                f"Verde = normal, amarillo = precaución, rojo = alerta."
            )

        st.warning(
            "⚠️ **Nota:** Los datos SIVELCE se reportan a nivel de localidad, no de zona. "
            "El color refleja el indicador de la **localidad** que contiene la zona."
        )

        # Summary table
        n_aprobadas = (gdf['ESTADO'] == 'APROBADA').sum()
        n_no_aprobadas = (gdf['ESTADO'] == 'NO_APROBADA').sum()
        area_aprobadas = gdf[gdf['ESTADO'] == 'APROBADA']['AREA_Ha'].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Zonas aprobadas", n_aprobadas)
        c2.metric("Zonas no aprobadas", n_no_aprobadas)
        c3.metric("Área total aprobada", f"{area_aprobadas:.1f} Ha")

    st.caption(FOOTER)


# ================================================================
# TAB 3: LOCALIDADES
# ================================================================
with tabs[2]:
    st.info(
        "📍 **Explorador por localidad.** Selecciona una localidad para ver su serie "
        "mensual. La línea horizontal gris marca la media pre-decreto. "
        "Las barras doradas muestran eventos con alcohol."
    )

    loc_options = [f"🟢 {l} (focal)" for l in LOC_FOCAL] + [f"⚪ {l} (control)" for l in LOC_CONTROL]
    loc_names = LOC_FOCAL + LOC_CONTROL

    sel_display = st.selectbox("Seleccionar localidad", loc_options)
    sel_idx = loc_options.index(sel_display)
    sel_loc = loc_names[sel_idx]

    sl = get_series_loc(franja_sel, sel_loc)
    if not sl:
        st.warning("Sin datos para esta localidad y franja.")
    else:
        ns = [r["n"] for r in sl]
        als = [r["a"] for r in sl]

        pre_vals = [r["n"] for r in sl if r["m"] < CORTE]
        media_pre = sum(pre_vals) / len(pre_vals) if pre_vals else 0

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=MESES_LABELS, y=als, name="Con alcohol",
            marker_color=AMARILLO, opacity=0.5,
            hovertemplate="Mes: %{x}<br>Con alcohol: %{y}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=MESES_LABELS, y=ns, name="Total eventos",
            line=dict(color=ACCENT, width=3), mode="lines+markers",
            marker=dict(size=7),
            hovertemplate="Mes: %{x}<br>Total: %{y}<extra></extra>",
        ))
        fig.add_hline(
            y=media_pre, line_dash="dot", line_color="#94A3B8",
            annotation_text=f"Media pre = {media_pre:.1f}",
            annotation_position="top right",
            annotation_font_color="#94A3B8",
        )
        fig.update_layout(**make_layout(
            title=f"{sel_loc} — {franja_label} | Eventos mensuales",
            xaxis_title="Mes", yaxis_title="Eventos",
            barmode="overlay",
            xaxis=cat_xaxis(),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        ))
        decreto_vline(fig)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Tabla de indicadores
        rows = []
        for r in sl:
            if r["m"] >= CORTE:
                obs = r["n"]
                delta = ((obs - media_pre) / media_pre * 100) if media_pre > 0 else 0
                if abs(delta) < 10:
                    interp = "🟢 Normal"
                elif abs(delta) < 20:
                    interp = "🟡 Precaución"
                else:
                    interp = "🔴 Alerta"
                rows.append({
                    "Mes": mes_label(r["m"]),
                    "Conteo": obs,
                    "Media pre": f"{media_pre:.1f}",
                    "Δ%": f"{delta:+.1f}%",
                    "Interpretación": interp,
                })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(FOOTER)


# ================================================================
# TAB 4: SEMÁFORO
# ================================================================
with tabs[3]:
    st.info(
        "🚦 **Sistema semáforo mensual.** Cada celda muestra el cambio % respecto "
        "al promedio pre-decreto y el conteo absoluto. Rojo = alerta, "
        "amarillo = precaución, verde = normal."
    )

    st.markdown(f"#### 🚦 Semáforo — {franja_label}")

    sem_tip = st.radio(
        "Tipología (semáforo)", ["T1", "T2"],
        format_func=lambda x: TIP_MAP[x],
        horizontal=True, key="sem_tip",
    )

    sem_data = get_sem(franja_sel, sem_tip)
    if not sem_data:
        st.warning("Sin datos de semáforo para esta combinación.")
    else:
        post_meses = sorted(set(r["m"] for r in sem_data))
        post_meses_labels = [mes_label(m) for m in post_meses]
        locs = LOC_FOCAL

        z_colors = []
        z_text = []
        hover_text = []

        for loc in locs:
            row_colors = []
            row_text = []
            row_hover = []
            for m_val in post_meses:
                entry = next((r for r in sem_data if r["l"] == loc and r["m"] == m_val), None)
                if entry:
                    s_code = entry["s"]
                    row_colors.append({"R": 0, "A": 0.5, "V": 1, "G": 0.25}.get(s_code, 0.25))
                    row_text.append(f"{entry['d']:+.0f}%<br>({entry['c']})")
                    estado = {"R": "ROJO", "A": "AMARILLO", "V": "VERDE"}.get(s_code, "GRIS")
                    row_hover.append(
                        f"<b>{loc}</b> | {mes_label(m_val)}<br>"
                        f"Conteo: {entry['c']}<br>"
                        f"Baseline: {entry['b']}<br>"
                        f"Δ: {entry['d']:+.1f}%<br>"
                        f"Estado: {estado}"
                    )
                else:
                    row_colors.append(0.25)
                    row_text.append("")
                    row_hover.append("")
            z_colors.append(row_colors)
            z_text.append(row_text)
            hover_text.append(row_hover)

        colorscale = [[0, ROJO], [0.25, "#475569"], [0.5, AMARILLO], [1, VERDE]]

        fig = go.Figure(data=go.Heatmap(
            z=z_colors, x=post_meses_labels, y=locs,
            text=z_text, texttemplate="%{text}",
            textfont=dict(size=10),
            hovertext=hover_text, hoverinfo="text",
            colorscale=colorscale, showscale=False,
            xgap=2, ygap=2,
        ))
        fig.update_layout(**make_layout(
            title=f"Semáforo — {franja_label} | {TIP_MAP[sem_tip]}",
            xaxis_title="Mes", yaxis_title="",
            height=470,
            xaxis=dict(type="category", tickangle=-45),
            yaxis=dict(autorange="reversed"),
        ))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            "🔴 **ROJO**: Δ≥20% (p<0.05) ó Δ≥30% ó Δ≥10% por 3+ meses  \n"
            "🟡 **AMARILLO**: 10%≤Δ<20%  \n"
            "🟢 **VERDE**: Δ<10%"
        )
        st.caption(FOOTER)


# ================================================================
# TAB 5: DiD
# ================================================================
with tabs[4]:
    st.info(
        "📐 **Diferencias en Diferencias (DiD).** Compara el cambio pre→post entre "
        "localidades focalizadas y control. Un DiD positivo indica que focal empeoró "
        "más (o mejoró menos) que control. Se compara con el MDE para saber si es detectable."
    )

    st.markdown(f"#### 📐 Diferencias en Diferencias — {franja_label}")

    rows_did = []
    for tid in TIP_IDS:
        d = get_did(franja_sel, tid)
        if not d:
            continue
        prF, prC = d["prF"], d["prC"]
        poF, poC = d["poF"], d["poC"]

        n_pre_m = len([m_val for m_val in MESES if m_val < CORTE])
        n_post_m = len([m_val for m_val in MESES if m_val >= CORTE])

        avg_prF = prF / n_pre_m if n_pre_m else 0
        avg_poF = poF / n_post_m if n_post_m else 0
        avg_prC = prC / n_pre_m if n_pre_m else 0
        avg_poC = poC / n_post_m if n_post_m else 0

        dF = ((avg_poF - avg_prF) / avg_prF * 100) if avg_prF > 0 else 0
        dC = ((avg_poC - avg_prC) / avg_prC * 100) if avg_prC > 0 else 0
        did_val = dF - dC

        rows_did.append({
            "Tipología": TIP_MAP[tid],
            "Pre Focal": f"{prF:,}",
            "Post Focal": f"{poF:,}",
            "Δ% Focal": f"{dF:+.1f}%",
            "Pre Control": f"{prC:,}",
            "Post Control": f"{poC:,}",
            "Δ% Control": f"{dC:+.1f}%",
            "DiD (pp)": f"{did_val:+.1f}",
            "_did_num": did_val,
            "_tid": tid,
        })

    if rows_did:
        # Alcohol row
        d_all = get_did(franja_sel, "T0")
        if d_all:
            aprF = d_all.get("aprF", 0)
            apoF = d_all.get("apoF", 0)
            aprC = d_all.get("aprC", 0)
            apoC = d_all.get("apoC", 0)
            prF_t, poF_t = d_all["prF"], d_all["poF"]
            prC_t, poC_t = d_all["prC"], d_all["poC"]

            pct_aprF = (aprF / prF_t * 100) if prF_t else 0
            pct_apoF = (apoF / poF_t * 100) if poF_t else 0
            pct_aprC = (aprC / prC_t * 100) if prC_t else 0
            pct_apoC = (apoC / poC_t * 100) if poC_t else 0
            dF_alc = pct_apoF - pct_aprF
            dC_alc = pct_apoC - pct_aprC
            did_alc = dF_alc - dC_alc

            rows_did.append({
                "Tipología": "🍺 % Alcohol (todas)",
                "Pre Focal": f"{pct_aprF:.1f}%",
                "Post Focal": f"{pct_apoF:.1f}%",
                "Δ% Focal": f"{dF_alc:+.1f}pp",
                "Pre Control": f"{pct_aprC:.1f}%",
                "Post Control": f"{pct_apoC:.1f}%",
                "Δ% Control": f"{dC_alc:+.1f}pp",
                "DiD (pp)": f"{did_alc:+.1f}",
                "_did_num": did_alc,
                "_tid": "T0",
            })

        df_did = pd.DataFrame(rows_did)
        st.dataframe(
            df_did.drop(columns=["_did_num", "_tid"]),
            use_container_width=True, hide_index=True,
        )

        st.divider()

        for row in rows_did:
            tid = row["_tid"]
            did_num = row["_did_num"]
            p_did = get_poder(franja_sel, tid, "did")
            mde = p_did.get("mde")
            if mde is not None:
                if abs(did_num) < mde:
                    st.info(
                        f"**{row['Tipología']}**: DiD observado = {did_num:+.1f}pp. "
                        f"MDE = {mde:.1f}%. "
                        f"⚠️ No es estadísticamente detectable con el poder disponible."
                    )
                else:
                    st.success(
                        f"**{row['Tipología']}**: DiD observado = {did_num:+.1f}pp. "
                        f"MDE = {mde:.1f}%. "
                        f"✅ Supera el MDE. Merece investigación adicional."
                    )

        st.caption(FOOTER)


# ================================================================
# TAB 6: ALCOHOL POR HORA
# ================================================================
with tabs[5]:
    st.info(
        "🍺 **Proporción de eventos con alcohol por hora del día**, pre vs post decreto. "
        "Las horas de la franja seleccionada se resaltan en dorado. "
        "Hover para ver el N de cada barra."
    )

    st.markdown(f"#### 🍺 Alcohol por hora — {franja_label}")

    alc_data = D["alcohol"]
    horas_franja = next((f["horas"] for f in META["franjas"] if f["id"] == franja_sel), [])

    hora_labels = [f"{r['h']:02d}h" for r in alc_data]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=hora_labels,
        y=[r["prP"] for r in alc_data],
        name="Pre-decreto",
        marker_color=AZUL_PRE, opacity=0.8,
        hovertemplate="Hora %{x}<br>Pre: %{y:.1f}%<br>N=%{customdata:,}<extra></extra>",
        customdata=[r["prN"] for r in alc_data],
    ))
    fig.add_trace(go.Bar(
        x=hora_labels,
        y=[r["poP"] for r in alc_data],
        name="Post-decreto",
        marker_color=ROJO_POST, opacity=0.8,
        hovertemplate="Hora %{x}<br>Post: %{y:.1f}%<br>N=%{customdata:,}<extra></extra>",
        customdata=[r["poN"] for r in alc_data],
    ))

    for h in horas_franja:
        label = f"{h:02d}h"
        idx = hora_labels.index(label) if label in hora_labels else -1
        if idx >= 0:
            fig.add_vrect(
                x0=idx - 0.5, x1=idx + 0.5,
                fillcolor="gold", opacity=0.12,
                line=dict(color="gold", width=1.5),
            )

    fig.update_layout(**make_layout(
        title="Proporción de eventos con alcohol por hora del día",
        xaxis_title="Hora del evento",
        yaxis_title="% con alcohol",
        barmode="group",
        bargap=0.15,
        bargroupgap=0.05,
        xaxis=dict(
            type="category", categoryorder="array", categoryarray=hora_labels,
            gridcolor="rgba(255,255,255,0.08)",
        ),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
    ))
    st.plotly_chart(fig, use_container_width=True)

    alc_franja = [r for r in alc_data if r["h"] in horas_franja]
    if alc_franja:
        n_pre_fr = sum(r["prN"] for r in alc_franja)
        n_post_fr = sum(r["poN"] for r in alc_franja)
        pct_pre = sum(r["prP"] * r["prN"] for r in alc_franja) / n_pre_fr if n_pre_fr else 0
        pct_post = sum(r["poP"] * r["poN"] for r in alc_franja) / n_post_fr if n_post_fr else 0
        diff = pct_post - pct_pre

        if diff > 0:
            st.error(
                f"**Franja {franja_label}**: alcohol pasó de {pct_pre:.1f}% a "
                f"{pct_post:.1f}% (Δ {diff:+.1f}pp)  \n"
                f"N pre = {n_pre_fr:,} | N post = {n_post_fr:,}"
            )
        else:
            st.success(
                f"**Franja {franja_label}**: alcohol pasó de {pct_pre:.1f}% a "
                f"{pct_post:.1f}% (Δ {diff:+.1f}pp)  \n"
                f"N pre = {n_pre_fr:,} | N post = {n_post_fr:,}"
            )

    st.caption(FOOTER)


# ================================================================
# TAB 7: PODER ESTADÍSTICO
# ================================================================
with tabs[6]:
    st.info(
        "⚡ **Poder estadístico y MDE.** El Efecto Mínimo Detectable indica el cambio "
        "más pequeño que podemos identificar con 80% de confianza. "
        "Verde (<30%) = bueno, rojo (>50%) = solo detecta cambios muy grandes."
    )
    st.warning(
        "**Nota metodológica:** El MDE pre-post usa el N total de eventos y mide el poder "
        "para detectar un cambio global. El MDE DiD es una aproximación conservadora que "
        "refleja el poder para detectar diferencias entre grupos focal y control, usando "
        "N efectivo basado en la media por celda localidad×mes × min(clusters) × meses. "
        "Un cálculo preciso de poder para DiD requiere simulación Monte Carlo con la "
        "estructura de varianza observada. Los valores reportados son orientativos."
    )

    st.markdown(f"#### ⚡ Poder Estadístico — {franja_label}")

    rows_poder = []
    for tid in TIP_IDS:
        for diseno, dis_label in [("pp", "Pre-post agregado"), ("did", "DiD (aprox. conservador)")]:
            p = get_poder(franja_sel, tid, diseno)
            if not p:
                continue
            mde = p.get("mde")
            if mde is None:
                interp = "No viable"
                color_tag = "⬜"
            elif mde > 50:
                interp = "Solo efectos muy grandes (>50%)"
                color_tag = "🔴"
            elif mde > 30:
                interp = "Efectos grandes (>30%)"
                color_tag = "🟡"
            else:
                interp = "Efectos moderados detectables"
                color_tag = "🟢"

            rows_poder.append({
                "Tipología": TIP_MAP[tid],
                "Diseño": dis_label,
                "N pre": f"{p['nPr']:,}",
                "N post": f"{p['nPo']:,}",
                "Media/mes": p["mu"],
                "MDE (%)": mde if mde else "N/A",
                "Interpretación": f"{color_tag} {interp}",
                "_mde_num": mde if mde else 999,
                "_tid": tid,
                "_dis": diseno,
            })

    if rows_poder:
        df_poder = pd.DataFrame(rows_poder)
        st.dataframe(
            df_poder.drop(columns=["_mde_num", "_tid", "_dis"]),
            use_container_width=True, hide_index=True,
        )

        st.divider()

        plot_rows = [r for r in rows_poder if r["_mde_num"] < 999]
        if plot_rows:
            labels = [f"{r['Tipología']} ({r['Diseño'][:7]})" for r in plot_rows]
            mdes = [r["_mde_num"] for r in plot_rows]
            colors = [VERDE if mv <= 30 else AMARILLO if mv <= 50 else ROJO for mv in mdes]

            fig = go.Figure(go.Bar(
                y=labels, x=mdes, orientation="h",
                marker_color=colors, opacity=0.85,
                text=[f"{mv:.0f}%" for mv in mdes], textposition="outside",
                hovertemplate="%{y}<br>MDE: %{x:.1f}%<extra></extra>",
            ))
            fig.add_vline(x=30, line_dash="dot", line_color="#94A3B8",
                          annotation_text="Umbral deseable (30%)",
                          annotation_font_color="#94A3B8")
            fig.update_layout(**make_layout(
                title=f"Efecto Mínimo Detectable — {franja_label}",
                xaxis_title="MDE (%)", yaxis_title="",
                height=max(450, len(plot_rows) * 45),
                yaxis=dict(autorange="reversed"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            ))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.markdown(f"**Comparación de MDE entre franjas** — {tip_label}")
        comp_rows = []
        for fid in FRANJA_IDS:
            for diseno, dis_label in [("pp", "Pre-post"), ("did", "DiD")]:
                p = get_poder(fid, tip_sel, diseno)
                if p and p.get("mde"):
                    comp_rows.append({
                        "Franja": FRANJA_DISPLAY.get(fid, FRANJA_MAP[fid]),
                        "Diseño": dis_label,
                        "MDE (%)": p["mde"],
                        "N pre": f"{p['nPr']:,}",
                        "N post": f"{p['nPo']:,}",
                    })
        if comp_rows:
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

    st.caption(FOOTER)


# ================================================================
# TAB 8: METODOLOGÍA
# ================================================================
with tabs[7]:
    st.info(
        "📖 **Documentación técnica** del diseño, fuentes, variables y limitaciones "
        "del análisis. Referencia para interpretar correctamente los resultados."
    )

    st.markdown("## 📖 Metodología")

    st.divider()

    # Sección 1
    st.markdown("### 1. El Decreto")
    st.markdown("""
El **Decreto 293 de 2025** (compilado en el Decreto 644/2025) establece horarios
diferenciados de cierre nocturno para establecimientos de expendio y consumo
de bebidas alcohólicas en Bogotá:

- **Zonas focalizadas** (19 zonas en 9 localidades): horario extendido hasta las **5:00 AM**
- **Resto de la ciudad**: cierre a las **3:00 AM**

**Vigencia:** julio 2025 (decreto general) | Diciembre 2025 (resolución 19 zonas)
""")

    st.divider()

    # Sección 2
    st.markdown("### 2. Diseño del estudio")
    st.markdown("""
Diseño cuasiexperimental de tipo **Diferencias en Diferencias (DiD)**:

**GRUPO TRATAMIENTO (Focal):** 9 localidades que contienen las 19 zonas focalizadas
> Kennedy, Suba, Engativá, Chapinero, Bosa, Fontibón, Usaquén,
> Puente Aranda, Mártires

**GRUPO CONTROL:** 5 localidades sin zonas focalizadas con mayor volumen de eventos
> Ciudad Bolívar, San Cristóbal, Rafael Uribe Uribe, Barrios Unidos, Tunjuelito

| Período | Rango | Meses |
|---------|-------|-------|
| Pre-decreto | diciembre 2024 – junio 2025 | 7 meses |
| Post-decreto | julio 2025 – febrero 2026 | 8 meses |
""")

    st.divider()

    # Sección 3
    st.markdown("### 3. Fuente de datos")
    st.markdown(f"""
**SIVELCE**: Sistema de Vigilancia Epidemiológica de Lesiones de Causa Externa

- **{TOTAL:,} eventos** con fecha y hora válidos
- **Variables clave:** fecha/hora del evento, localidad, tipología derivada,
  presencia de alcohol
- **Limitación:** no tiene coordenadas lat/lon, la clasificación es a nivel
  de localidad (no de zona específica)
""")

    st.divider()

    # Sección 4
    st.markdown("### 4. Tipologías")
    st.markdown("""
Se construyó una variable de tipología **jerárquica** (un evento solo puede
pertenecer a una categoría, evaluadas en este orden):

| # | Tipología | Regla de clasificación |
|---|-----------|----------------------|
| 1 | Autolesión | `CausadaPor` = "Autoinfligida" |
| 2 | Violencia sexual | `Maltrato` = "Delito Sexual" |
| 3 | Violencia intrafamiliar | `Maltrato` = "V. Intrafamiliar" ó "V. Conyugal" |
| 4 | Violencia interpersonal | `CausadaPor` = "Terceros" + `Maltrato` = "V. Común" |
| 5 | Siniestros viales | `Accidente` = "Accidente de tránsito" |
| 6 | Intoxicación | `Alcohol` = "Sí" ó `SPA` = "Sí" (no capturado arriba) |
| 7 | No intencional otros | Todo lo demás |

La variable **"con alcohol"** es transversal e independiente de la tipología.
""")

    st.divider()

    # Sección 5
    st.markdown("### 5. Franjas horarias")
    st.markdown("""
Se pre-calcularon **6 ventanas de análisis** para explorar la sensibilidad
de los resultados:

| Franja | Horas | Justificación |
|--------|-------|---------------|
| 🔴 Crítica 03-04 | 3:00-4:59 AM | Ventana donde aplica la diferencia regulatoria |
| Ampliada 02-04 | 2:00-4:59 AM | +1 hora antes del cierre general |
| Ampliada 03-05 | 3:00-5:59 AM | Incluye hora post-cierre extendido |
| Extendida 01-05 | 1:00-5:59 AM | Madrugada amplia |
| 🔵 Nocturna 22-05 | 10:00 PM-5:59 AM | Nocturna completa (mayor poder estadístico) |
| Madrugada 00-05 | 12:00-5:59 AM | Medianoche a amanecer |

> **Tradeoff:** Ampliar la franja aumenta el N de eventos y reduce el MDE,
> pero diluye la especificidad del efecto del decreto.
""")

    st.divider()

    # Sección 6
    st.markdown("### 6. Indicadores y sistema semáforo")
    st.markdown("""
**IND-1:** Conteo absoluto mensual de eventos en la franja

**IND-5:** Cambio porcentual vs línea base pre-decreto (promedio dic 2024 – jun 2025)

#### Sistema semáforo

| Color | Criterio |
|-------|----------|
| 🔴 ROJO | Δ ≥ 20% con p<0.05, **O** Δ ≥ 30%, **O** Δ ≥ 10% por 3+ meses consecutivos |
| 🟡 AMARILLO | 10% ≤ Δ < 20%, **O** 0.05 ≤ p < 0.10 |
| 🟢 VERDE | Δ < 10% **y** p ≥ 0.10 |

- **p-valor:** test exacto de Poisson comparando conteo observado vs esperado bajo baseline
- **IC 95%:** aproximación log-normal del rate ratio
""")

    st.divider()

    # Sección 7
    st.markdown("### 7. Poder estadístico y limitaciones")
    st.markdown("""
**Efecto Mínimo Detectable (MDE):** el cambio más pequeño que podemos detectar
con 80% de probabilidad (α = 0.05).

**Fórmula:** `δ_MDE ≈ exp(2.80 × √(1/N_post + 1/N_pre)) - 1`

#### Limitaciones críticas

| # | Limitación | Impacto |
|---|-----------|---------|
| 1 | **Sin línea base histórica** | Solo 7 meses pre-decreto (el protocolo requiere datos 2022-2024) |
| 2 | **Sin coordenadas geográficas** | No es posible vincular eventos a las 19 zonas específicas, solo a las 9 localidades |
| 3 | **Alta sobredispersión** | Varianza/media ≈ 12.4 en franja crítica |
| 4 | **MDE elevado** | El más bajo es ~40% (DiD, nocturna, todas) — solo se detectarían efectos muy grandes |
""")

    st.divider()

    # Sección 8
    st.markdown("### 8. Cómo leer el dashboard")
    st.markdown("""
| Pestaña | Qué muestra | Cómo interpretar |
|---------|-------------|-----------------|
| 📊 **General** | Evolución mensual de eventos | Si hay efecto, la línea verde (focal) debería separarse de la gris (control) después de jul-25 |
| 🗺️ **Mapa** | Ubicación geográfica de las 19 zonas | Los colores reflejan el semáforo de la localidad contenedora |
| 📍 **Localidades** | Serie individual de cada localidad | Comparar con la media pre-decreto (línea gris horizontal) |
| 🚦 **Semáforo** | Alerta rápida por localidad y mes | Rojo = alerta, amarillo = precaución, verde = normal |
| 📐 **DiD** | Comparación formal entre grupos | DiD positivo = focal empeoró más que control |
| 🍺 **Alcohol** | % eventos con alcohol por hora | Las horas resaltadas en dorado son la franja seleccionada |
| ⚡ **Poder** | MDE por diseño y tipología | Verde (<30%) = bueno, rojo (>50%) = limitado |
""")

    st.divider()
    st.caption(FOOTER)
