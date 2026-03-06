"""
Decreto Rumba — Panel Analítico SIVELCE
Dashboard interactivo para medición de impacto del Decreto 293/2025
Secretaría Distrital de Salud de Bogotá
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json

# ── Configuración ──────────────────────────────────────────────
st.set_page_config(
    page_title="Decreto Rumba — Panel Analítico",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Colores
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
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E2E8F0", size=12),
    margin=dict(l=60, r=30, t=60, b=60),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

FUENTE = "Fuente: SIVELCE | dic 2024 – feb 2026"


# ── Carga de datos ─────────────────────────────────────────────
@st.cache_data
def load_data():
    with open("dashboard_data.json", encoding="utf-8") as f:
        return json.load(f)


D = load_data()
META = D["meta"]

FRANJA_MAP = {f["id"]: f["nombre"] for f in META["franjas"]}
FRANJA_IDS = list(FRANJA_MAP.keys())
TIP_MAP = {t["id"]: t["nombre"] for t in META["tipologias"]}
TIP_IDS = list(TIP_MAP.keys())
MESES = META["meses"]
CORTE = META["corte"]
TOTAL = META["total"]
LOC_FOCAL = META["locFocal"]
LOC_CONTROL = META["locControl"]


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


def decreto_vline(fig):
    """Agrega línea vertical del decreto en julio 2025."""
    if CORTE in MESES:
        idx = MESES.index(CORTE)
        fig.add_vline(
            x=idx, line_dash="dash", line_color=DECRETO, line_width=2,
            annotation_text="Decreto 293", annotation_position="top left",
            annotation_font_color=DECRETO, annotation_font_size=11,
        )


def fmt_delta(val):
    if val > 0:
        return f"+{val:.1f}%"
    return f"{val:.1f}%"


# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏛️ DECRETO RUMBA")
    st.caption("Medición de Impacto")
    st.divider()

    st.markdown("**Franja horaria**")
    franja_sel = st.radio(
        "Franja", FRANJA_IDS,
        format_func=lambda x: FRANJA_MAP[x],
        label_visibility="collapsed",
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

franja_label = FRANJA_MAP[franja_sel]
tip_label = TIP_MAP[tip_sel]

# ── Título ─────────────────────────────────────────────────────
st.markdown(
    "<h2 style='margin-bottom:0'>Decreto Rumba — Panel Analítico SIVELCE</h2>"
    "<p style='color:#94A3B8;margin-top:0'>"
    f"Secretaría Distrital de Salud de Bogotá | {TOTAL:,} eventos | dic 2024 – feb 2026"
    "</p>",
    unsafe_allow_html=True,
)

# ── Tabs ───────────────────────────────────────────────────────
tabs = st.tabs([
    "📊 General", "📍 Localidades", "🚦 Semáforo",
    "📐 Diferencias en Diferencias", "🍺 Alcohol por hora",
    "⚡ Poder", "📋 Resumen",
])

# ================================================================
# TAB 1: GENERAL
# ================================================================
with tabs[0]:
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

        delta_F = ((sum_poF / max(len(post), 1)) / (sum_prF / max(len(pre), 1)) - 1) * 100 if sum_prF > 0 else 0
        delta_C = ((sum_poC / max(len(post), 1)) / (sum_prC / max(len(pre), 1)) - 1) * 100 if sum_prC > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pre Focal (7m)", f"{sum_prF:,}", f"{delta_F:+.1f}% prom/mes")
        c2.metric("Post Focal (8m)", f"{sum_poF:,}")
        c3.metric("Pre Control (7m)", f"{sum_prC:,}", f"{delta_C:+.1f}% prom/mes")
        c4.metric("Post Control (8m)", f"{sum_poC:,}")

        # Serie temporal
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=MESES, y=[r["F"] for r in s], name="Focal",
            line=dict(color=FOCAL, width=2.5), mode="lines+markers",
            marker=dict(size=6),
            hovertemplate="Mes: %{x}<br>Focal: %{y}<br>Alcohol: %{customdata}<extra></extra>",
            customdata=[r["aF"] for r in s],
        ))
        fig.add_trace(go.Scatter(
            x=MESES, y=[r["C"] for r in s], name="Control",
            line=dict(color=CONTROL, width=2.5), mode="lines+markers",
            marker=dict(size=6),
            hovertemplate="Mes: %{x}<br>Control: %{y}<br>Alcohol: %{customdata}<extra></extra>",
            customdata=[r["aC"] for r in s],
        ))
        fig.update_layout(
            **PLOTLY_LAYOUT,
            title=f"Serie temporal — {franja_label} | {tip_label}",
            xaxis_title="Mes", yaxis_title="Eventos",
            xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        )
        decreto_vline(fig)
        st.plotly_chart(fig, use_container_width=True)

        # % Alcohol
        pct_alc_F = [(r["aF"] / r["F"] * 100) if r["F"] > 0 else 0 for r in s]
        pct_alc_C = [(r["aC"] / r["C"] * 100) if r["C"] > 0 else 0 for r in s]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=MESES, y=pct_alc_F, name="% Alcohol Focal",
            line=dict(color=FOCAL, width=2), mode="lines+markers", marker=dict(size=5),
        ))
        fig2.add_trace(go.Scatter(
            x=MESES, y=pct_alc_C, name="% Alcohol Control",
            line=dict(color=CONTROL, width=2), mode="lines+markers", marker=dict(size=5),
        ))
        fig2.update_layout(
            **PLOTLY_LAYOUT,
            title=f"% eventos con presencia de alcohol — {franja_label} | {tip_label}",
            xaxis_title="Mes", yaxis_title="% con alcohol",
            xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        )
        decreto_vline(fig2)
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(FUENTE)


# ================================================================
# TAB 2: LOCALIDADES
# ================================================================
with tabs[1]:
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
            x=MESES, y=als, name="Con alcohol",
            marker_color=AMARILLO, opacity=0.5,
            hovertemplate="Mes: %{x}<br>Con alcohol: %{y}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=MESES, y=ns, name="Total eventos",
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
        fig.update_layout(
            **PLOTLY_LAYOUT,
            title=f"{sel_loc} — {franja_label} | Eventos mensuales",
            xaxis_title="Mes", yaxis_title="Eventos",
            barmode="overlay",
            xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        )
        decreto_vline(fig)
        st.plotly_chart(fig, use_container_width=True)

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
                    "Mes": r["m"], "Conteo": obs,
                    "Media pre": f"{media_pre:.1f}",
                    "Δ%": f"{delta:+.1f}%",
                    "Interpretación": interp,
                })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(FUENTE)


# ================================================================
# TAB 3: SEMÁFORO
# ================================================================
with tabs[2]:
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
        locs = LOC_FOCAL

        color_map_sem = {"R": ROJO, "A": AMARILLO, "V": VERDE, "G": "#475569"}

        z_colors = []
        z_text = []
        hover_text = []

        for loc in locs:
            row_colors = []
            row_text = []
            row_hover = []
            for m in post_meses:
                entry = next((r for r in sem_data if r["l"] == loc and r["m"] == m), None)
                if entry:
                    s_code = entry["s"]
                    row_colors.append({"R": 0, "A": 0.5, "V": 1, "G": 0.25}.get(s_code, 0.25))
                    row_text.append(f"{entry['d']:+.0f}%<br>({entry['c']})")
                    row_hover.append(
                        f"<b>{loc}</b> | {m}<br>"
                        f"Conteo: {entry['c']}<br>"
                        f"Baseline: {entry['b']}<br>"
                        f"Δ: {entry['d']:+.1f}%<br>"
                        f"Estado: {'ROJO' if s_code == 'R' else 'AMARILLO' if s_code == 'A' else 'VERDE'}"
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
            z=z_colors, x=post_meses, y=locs,
            text=z_text, texttemplate="%{text}",
            textfont=dict(size=10),
            hovertext=hover_text, hoverinfo="text",
            colorscale=colorscale, showscale=False,
            xgap=2, ygap=2,
        ))
        fig.update_layout(
            **PLOTLY_LAYOUT,
            title=f"Semáforo — {franja_label} | {TIP_MAP[sem_tip]}",
            xaxis_title="Mes", yaxis_title="",
            height=450,
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            "🔴 **ROJO**: Δ≥20% (p<0.05) ó Δ≥30% ó Δ≥10% por 3+ meses  \n"
            "🟡 **AMARILLO**: 10%≤Δ<20%  \n"
            "🟢 **VERDE**: Δ<10%"
        )
        st.caption(FUENTE)


# ================================================================
# TAB 4: DiD
# ================================================================
with tabs[3]:
    st.markdown(f"#### 📐 Diferencias en Diferencias — {franja_label}")

    rows_did = []
    for tid in TIP_IDS:
        d = get_did(franja_sel, tid)
        if not d:
            continue
        prF, prC = d["prF"], d["prC"]
        poF, poC = d["poF"], d["poC"]

        n_pre_m = len([m for m in MESES if m < CORTE])
        n_post_m = len([m for m in MESES if m >= CORTE])

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
            prF_t = d_all["prF"]
            poF_t = d_all["poF"]
            prC_t = d_all["prC"]
            poC_t = d_all["poC"]

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

        # Interpretación con MDE
        for row in rows_did:
            tid = row["_tid"]
            did_num = row["_did_num"]
            p_did = get_poder(franja_sel, tid, "did")
            mde = p_did.get("mde")
            if mde is not None and tid != "T0_alc":
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

        st.caption(FUENTE)


# ================================================================
# TAB 5: ALCOHOL POR HORA
# ================================================================
with tabs[4]:
    st.markdown(f"#### 🍺 Alcohol por hora — {franja_label}")

    alc_data = D["alcohol"]
    horas_franja = next((f["horas"] for f in META["franjas"] if f["id"] == franja_sel), [])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[r["h"] for r in alc_data],
        y=[r["prP"] for r in alc_data],
        name=f"Pre-decreto",
        marker_color=AZUL_PRE, opacity=0.8,
        hovertemplate="Hora %{x}h<br>Pre: %{y:.1f}%<br>N=%{customdata}<extra></extra>",
        customdata=[r["prN"] for r in alc_data],
    ))
    fig.add_trace(go.Bar(
        x=[r["h"] for r in alc_data],
        y=[r["poP"] for r in alc_data],
        name=f"Post-decreto",
        marker_color=ROJO_POST, opacity=0.8,
        hovertemplate="Hora %{x}h<br>Post: %{y:.1f}%<br>N=%{customdata}<extra></extra>",
        customdata=[r["poN"] for r in alc_data],
    ))

    # Resaltar franja seleccionada
    for h in horas_franja:
        fig.add_vrect(
            x0=h - 0.5, x1=h + 0.5,
            fillcolor="gold", opacity=0.1,
            line=dict(color="gold", width=1.5),
        )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Proporción de eventos con alcohol por hora del día",
        xaxis_title="Hora del evento",
        yaxis_title="% con alcohol",
        barmode="group",
        xaxis=dict(
            tickmode="linear", dtick=1,
            gridcolor="rgba(255,255,255,0.08)",
        ),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Hallazgo destacado
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

    st.caption(FUENTE)


# ================================================================
# TAB 6: PODER ESTADÍSTICO
# ================================================================
with tabs[5]:
    st.markdown(f"#### ⚡ Poder Estadístico — {franja_label}")

    rows_poder = []
    for tid in TIP_IDS:
        for diseno, dis_label in [("pp", "Pre-post agregado"), ("did", "DiD localidad×mes")]:
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

        # Gráfica de barras horizontales
        plot_rows = [r for r in rows_poder if r["_mde_num"] < 999]
        if plot_rows:
            labels = [f"{r['Tipología']} ({r['Diseño'][:7]})" for r in plot_rows]
            mdes = [r["_mde_num"] for r in plot_rows]
            colors = [VERDE if m <= 30 else AMARILLO if m <= 50 else ROJO for m in mdes]

            fig = go.Figure(go.Bar(
                y=labels, x=mdes, orientation="h",
                marker_color=colors, opacity=0.85,
                text=[f"{m:.0f}%" for m in mdes], textposition="outside",
                hovertemplate="%{y}<br>MDE: %{x:.1f}%<extra></extra>",
            ))
            fig.add_vline(x=30, line_dash="dot", line_color="#94A3B8",
                          annotation_text="Umbral deseable (30%)",
                          annotation_font_color="#94A3B8")
            fig.update_layout(
                **PLOTLY_LAYOUT,
                title=f"Efecto Mínimo Detectable — {franja_label}",
                xaxis_title="MDE (%)", yaxis_title="",
                height=max(350, len(plot_rows) * 45),
                yaxis=dict(autorange="reversed"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            )
            st.plotly_chart(fig, use_container_width=True)

    # Comparación entre franjas
    st.markdown(f"**Comparación de MDE entre franjas** — {tip_label}")
    comp_rows = []
    for fid in FRANJA_IDS:
        for diseno, dis_label in [("pp", "Pre-post"), ("did", "DiD")]:
            p = get_poder(fid, tip_sel, diseno)
            if p and p.get("mde"):
                comp_rows.append({
                    "Franja": FRANJA_MAP[fid],
                    "Diseño": dis_label,
                    "MDE (%)": p["mde"],
                    "N pre": f"{p['nPr']:,}",
                    "N post": f"{p['nPo']:,}",
                })
    if comp_rows:
        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

    st.caption(FUENTE)


# ================================================================
# TAB 7: RESUMEN EJECUTIVO
# ================================================================
with tabs[6]:
    st.markdown("#### 📋 Resumen Ejecutivo")

    st.markdown("""
**Decreto 293/2025** (compilado en Decreto 644/2025): horarios diferenciados
de cierre nocturno — 5:00 AM en 19 zonas focalizadas (9 localidades) vs.
3:00 AM en el resto de Bogotá. Vigente desde julio 2025.

---

##### Hallazgos principales

**1. Alcohol en franja crítica (03-04h)**
La proporción de eventos con presencia de alcohol en la franja 03:00-04:59
muestra un incremento post-decreto en localidades focalizadas.
Esto es consistente con mayor actividad nocturna en las zonas con horario
extendido.

**2. Siniestros viales**
En varias localidades focalizadas, los siniestros viales en franja nocturna
muestran incrementos persistentes (semáforo ROJO en múltiples meses).
Kennedy y Suba requieren atención especial.

**3. Poder estadístico limitado**
El MDE mínimo obtenido es ~40% (DiD, franja nocturna ampliada, todas las
tipologías). Solo se pueden detectar efectos muy grandes. La franja
nocturna 22-05 ofrece mejor poder que la franja estricta 03-04.

---

##### Limitaciones críticas

| Limitación | Impacto |
|-----------|---------|
| **Sin línea base histórica** | Solo 7 meses pre-decreto (dic 2024 - jun 2025). El protocolo contemplaba datos desde 2022. |
| **Sin coordenadas de eventos** | SIVELCE no tiene lat/lon. La clasificación es por localidad (9 focal vs. 11+ control), no por zona exacta. |
| **Sobredispersión** | Varianza/media > 12 en franja crítica. Requiere modelos Binomial Negativo. |

---

##### Recomendaciones

1. **Solicitar datos SIVELCE 2022-2024** para construir línea base robusta
   y reducir el MDE sustancialmente.
2. **Solicitar coordenadas geocodificadas** (o UPZ) para spatial join con
   los polígonos de las 19 zonas aprobadas.
3. **Considerar fuentes complementarias**: CRUE, INMLCF, datos de movilidad.
4. **Ampliar ventana post-decreto** — cada mes adicional mejora el poder.
5. **Explorar modelos Binomial Negativo** con efectos fijos de localidad y
   tendencia temporal.

---
""")
    st.caption(
        "Documento generado a partir de SIVELCE (depurado). "
        "177,088 eventos | dic 2024 – feb 2026. "
        "Scripts reproducibles en `_dashboard/`."
    )
