"""
dashboard.py
============
BMKG Stasiun Meteorologi Fatmawati Bengkulu
Dashboard Pemantauan & Analisis Cuaca Interaktif

Jalankan lokal  : streamlit run dashboard.py
Deploy          : Streamlit Community Cloud (gratis)
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="BMKG Fatmawati — Dashboard Cuaca",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* ── Weather background animations ── */
.weather-bg {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    z-index: 0; pointer-events: none; overflow: hidden;
}
.rain-drop {
    position: absolute; width: 2px; border-radius: 2px;
    background: linear-gradient(transparent, rgba(130,180,255,0.7));
    animation: fall linear infinite;
}
@keyframes fall {
    0%   { transform: translateY(-120px); opacity: 0; }
    10%  { opacity: 1; }
    90%  { opacity: 1; }
    100% { transform: translateY(110vh); opacity: 0; }
}
.cloud-puff {
    position: absolute; border-radius: 50%;
    background: rgba(180,200,220,0.18);
    animation: drift linear infinite;
}
@keyframes drift {
    0%   { transform: translateX(-200px); }
    100% { transform: translateX(110vw); }
}
.fog-layer {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: repeating-linear-gradient(
        0deg, rgba(200,215,230,0.07) 0px, rgba(200,215,230,0.12) 60px,
        rgba(200,215,230,0.04) 120px);
    animation: fogdrift 18s ease-in-out infinite alternate;
    pointer-events: none; z-index: 0;
}
@keyframes fogdrift {
    0%   { background-position: 0 0; opacity: 0.6; }
    100% { background-position: 0 40px; opacity: 1; }
}
@keyframes lightning {
    0%, 92%, 94%, 96%, 100% { opacity: 0; }
    93%, 95% { opacity: 1; }
}

/* ── Glassmorphism panels ── */
.glass-panel {
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(14px) saturate(160%);
    -webkit-backdrop-filter: blur(14px) saturate(160%);
    border: 1px solid rgba(255,255,255,0.55);
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(26,107,154,0.08), 0 1px 4px rgba(0,0,0,0.04);
    padding: 20px 24px;
    margin-bottom: 18px;
}
.glass-section {
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(10px) saturate(140%);
    -webkit-backdrop-filter: blur(10px) saturate(140%);
    border: 1px solid rgba(255,255,255,0.5);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 14px;
}

/* ── Header ── */
.main-header {
    background: linear-gradient(135deg, rgba(26,107,154,0.92) 0%, rgba(13,79,117,0.95) 100%);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    color: white;
    padding: 24px 32px;
    border-radius: 16px;
    margin-bottom: 20px;
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 8px 32px rgba(26,107,154,0.25);
    position: relative; overflow: hidden;
}
.main-header::before {
    content: ''; position: absolute;
    top: -40%; left: -10%; width: 60%; height: 200%;
    background: radial-gradient(ellipse, rgba(255,255,255,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.main-header h1 { margin: 0 0 4px; font-size: 22px; font-weight: 600; letter-spacing: -0.3px; }
.main-header p  { margin: 0; font-size: 13px; opacity: 0.75; font-weight: 300; }
.header-meta    { display: flex; gap: 24px; margin-top: 14px; }
.header-meta span { font-size: 12px; opacity: 0.65; font-family: 'DM Mono', monospace; }

/* ── Metric cards ── */
.metrics-wrapper {
    background: rgba(240,246,252,0.5);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(26,107,154,0.12);
    border-radius: 14px;
    padding: 18px 20px 14px;
    margin-bottom: 20px;
}
.metrics-label {
    font-size: 11px; font-weight: 600; color: #1a6b9a;
    text-transform: uppercase; letter-spacing: .08em;
    margin-bottom: 14px;
}
.metrics-divider {
    height: 1px; background: rgba(26,107,154,0.1); margin: 10px 0 14px;
}
.metric-card {
    background: rgba(255,255,255,0.8);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.7);
    border-radius: 12px; padding: 14px 16px; text-align: center;
    box-shadow: 0 2px 8px rgba(26,107,154,0.07);
    transition: transform .15s, box-shadow .15s;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(26,107,154,0.12);
}
.metric-label   { font-size: 10px; color: #6b7280; font-weight: 600;
                  text-transform: uppercase; letter-spacing: .07em; margin-bottom: 6px; }
.metric-value   { font-size: 26px; font-weight: 600; color: #1a1f2e;
                  line-height: 1; font-family: 'DM Mono', monospace; }
.metric-unit    { font-size: 12px; color: #9ca3af; margin-left: 3px; font-weight: 400; }
.metric-delta   { font-size: 11px; margin-top: 4px; }
.metric-delta.up   { color: #ef4444; }
.metric-delta.down { color: #3b82f6; }
.metric-delta.same { color: #9ca3af; }

/* ── Section headers ── */
.section-title { font-size: 14px; font-weight: 600; color: #374151;
                 margin: 0 0 2px; letter-spacing: -0.1px; }
.section-sub   { font-size: 12px; color: #9ca3af; margin: 0 0 14px; }

/* ── Status badge ── */
.badge { display:inline-block; padding:2px 10px; border-radius:20px;
         font-size:11px; font-weight:500; }
.badge-green  { background:#dcfce7; color:#166534; }
.badge-yellow { background:#fef9c3; color:#854d0e; }
.badge-red    { background:#fee2e2; color:#991b1b; }
.badge-blue   { background:#dbeafe; color:#1e40af; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: rgba(245,247,250,0.8);
    backdrop-filter: blur(6px); padding: 4px; border-radius: 10px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px; padding: 6px 16px; font-size: 13px; font-weight: 500;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: rgba(249,250,251,0.9);
    backdrop-filter: blur(8px);
    border-right: 1px solid rgba(232,236,240,0.8);
}

[data-testid="stToolbar"], footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_engine():
    """
    Membuat koneksi ke Supabase PostgreSQL.
    Prioritas: Streamlit Secrets (cloud) → file .env (lokal)
    """
    host = port = name = user = pw = None

    try:
        if "database" in st.secrets:
            db   = st.secrets["database"]
            host = db.get("host")
            port = db.get("port", 5432)
            name = db.get("name", "postgres")
            user = db.get("user", "postgres")
            pw   = db.get("password")
    except Exception:
        pass

    if not host or not pw:
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "postgres")
        user = os.getenv("DB_USER", "postgres")
        pw   = os.getenv("DB_PASSWORD")

    if not host or not pw:
        st.error(
            "❌ Konfigurasi database belum lengkap.\n\n"
            "**Jika dijalankan lokal:** pastikan file `.env` ada "
            "di folder yang sama dengan `dashboard.py` dan sudah berisi "
            "`DB_HOST` serta `DB_PASSWORD`.\n\n"
            "**Jika di Streamlit Cloud:** buka App Settings → Secrets, "
            "pastikan isinya sudah disimpan dengan benar lalu klik Reboot."
        )
        return None

    try:
        url = f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{name}"
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.error(f"❌ Gagal konek ke database: {e}")
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def load_daily(date_from: str, date_to: str) -> pd.DataFrame:
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()
    q = text(f"""
        SELECT * FROM clean_daily
        WHERE date BETWEEN '{date_from}' AND '{date_to}'
        ORDER BY date
    """)
    try:
        with engine.connect() as conn:
            df = pd.read_sql(q, conn)
        df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as e:
        st.error(f"❌ Gagal memuat data harian: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def load_hourly(date_from: str, date_to: str) -> pd.DataFrame:
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()
    q = text(f"""
        SELECT * FROM clean_hourly
        WHERE timestamp BETWEEN '{date_from}' AND '{date_to} 23:59:59'
        ORDER BY timestamp
    """)
    try:
        with engine.connect() as conn:
            df = pd.read_sql(q, conn)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        st.error(f"❌ Gagal memuat data per jam: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def load_latest() -> pd.Series:
    """Ambil observasi terakhir untuk monitoring real-time."""
    engine = get_engine()
    if engine is None:
        return pd.Series()
    q = text("SELECT * FROM clean_hourly ORDER BY timestamp DESC LIMIT 1")
    try:
        with engine.connect() as conn:
            df = pd.read_sql(q, conn)
        return df.iloc[0] if len(df) > 0 else pd.Series()
    except Exception:
        return pd.Series()

@st.cache_data(ttl=3600, show_spinner=False)
def load_date_range():
    engine = get_engine()
    if engine is None:
        return None, None
    q = text("SELECT MIN(date)::date as mn, MAX(date)::date as mx FROM clean_daily")
    try:
        with engine.connect() as conn:
            row = pd.read_sql(q, conn).iloc[0]
        return pd.to_datetime(row["mn"]), pd.to_datetime(row["mx"])
    except Exception:
        return None, None

PLOTLY_LAYOUT = dict(
    font_family="DM Sans",
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02,
        xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"
    ),
    xaxis=dict(
        showgrid=True, gridcolor="#f0f2f5", zeroline=False,
        showline=True, linecolor="#e5e7eb",
    ),
    yaxis=dict(
        showgrid=True, gridcolor="#f0f2f5", zeroline=False,
        showline=False,
    ),
)

COLOR_PRIMARY   = "#1a6b9a"
COLOR_SECONDARY = "#e85d26"
COLOR_SUCCESS   = "#16a34a"
COLOR_WARNING   = "#d97706"
COLOR_DANGER    = "#dc2626"
COLOR_NEUTRAL   = "#6b7280"

def wind_dir_label(deg):
    """Konversi derajat ke label arah mata angin."""
    dirs = ["U", "UTL", "TL", "TTL", "T", "TTG", "TG", "STG",
            "S", "SBD", "BD", "BBD", "B", "BBL", "BL", "UBL"]
    ix = int((deg + 11.25) / 22.5) % 16
    return dirs[ix]

def cuaca_label(ww):
    """Konversi kode WW ke label ringkas."""
    if pd.isna(ww):
        return "—"
    ww = int(ww)
    if ww <= 19:   return "Cerah / Berawan"
    if ww <= 29:   return "Bekas Presipitasi"
    if ww <= 39:   return "Badai Debu/Pasir"
    if ww <= 49:   return "Kabut"
    if ww <= 59:   return "Gerimis"
    if ww <= 69:   return "Hujan"
    if ww <= 79:   return "Salju/Es"
    if ww <= 90:   return "Hujan Lebat"
    return "Badai Petir"


def get_weather_category(ww) -> str:
    """Kelompokkan kode WW menjadi kategori animasi."""
    if pd.isna(ww):
        return "clear"
    ww = int(ww)
    if ww in range(95, 100):  return "storm"
    if ww in range(80, 95):   return "heavy_rain"
    if ww in range(50, 80):   return "rain"
    if ww in range(40, 50):   return "fog"
    if ww in range(1, 10):    return "cloudy"
    return "clear"


def weather_bg_html(ww) -> str:
    """
    Render CSS-animated background sesuai kondisi cuaca.
    Tidak menggunakan gambar atau GIF — murni CSS + HTML divs.
    """
    cat = get_weather_category(ww)

    if cat in ("rain", "heavy_rain", "storm"):
        n_drops = 60 if cat == "heavy_rain" else (90 if cat == "storm" else 35)
        drops   = ""
        for i in range(n_drops):
            left   = (i * 17 + i * i * 3) % 100
            delay  = round((i * 0.23) % 4, 2)
            dur    = round(0.55 + (i % 7) * 0.12, 2)
            height = 14 + (i % 5) * 6
            opacity= 0.45 + (i % 3) * 0.15
            drops += (f'<div class="rain-drop" style="left:{left}%;'
                      f'animation-delay:{delay}s;animation-duration:{dur}s;'
                      f'height:{height}px;opacity:{opacity}"></div>')
        overlay_color = ("rgba(20,30,60,0.18)" if cat == "storm"
                         else "rgba(30,60,120,0.10)")
        lightning = ('<div style="position:fixed;top:0;left:0;width:100%;height:100%;'
                     'background:rgba(220,240,255,0.9);pointer-events:none;z-index:0;'
                     'animation:lightning 6s ease-in-out infinite;"></div>'
                     if cat == "storm" else "")
        return (f'<div class="weather-bg" style="background:{overlay_color};">'
                f'{drops}{lightning}</div>')

    if cat == "fog":
        return ('<div class="fog-layer"></div>'
                '<div class="fog-layer" style="animation-delay:-9s;opacity:0.5;'
                'background:repeating-linear-gradient(0deg,rgba(210,225,235,0.09) 0px,'
                'rgba(210,225,235,0.13) 80px,rgba(210,225,235,0.05) 160px);"></div>')

    if cat == "cloudy":
        puffs = ""
        params = [(5,18,280,12,22), (20,30,380,8,18), (55,10,260,14,20),
                  (70,22,320,10,16), (40,35,420,9,15), (85,15,290,11,19)]
        for left, top, dur, w, h in params:
            delay = round((left * 0.15) % 6, 1)
            puffs += (f'<div class="cloud-puff" style="left:{left}%;top:{top}%;'
                      f'width:{w}vw;height:{h}vh;animation-duration:{dur}s;'
                      f'animation-delay:{delay}s;"></div>')
        return f'<div class="weather-bg">{puffs}</div>'

    return ""


def metric_html(label, value, unit="", delta=None, delta_label=""):
    delta_html = ""
    if delta is not None:
        cls   = "up" if delta > 0 else ("down" if delta < 0 else "same")
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
        delta_html = (f'<div class="metric-delta {cls}">'
                      f'{arrow} {abs(delta):.1f} {delta_label}</div>')
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
        {delta_html}
    </div>"""

def chart_timeseries_suhu(df_daily):
    fig = go.Figure()

    col_max = ("suhu_max_tercatat_c"
               if df_daily["suhu_max_tercatat_c"].notna().sum() > 0
               else "suhu_max_obs_c")
    col_min = ("suhu_min_tercatat_c"
               if df_daily["suhu_min_tercatat_c"].notna().sum() > 0
               else "suhu_min_obs_c")

    label_max = "Suhu Max (termometer)" if "tercatat" in col_max else "Suhu Max (obs)"
    label_min = "Suhu Min (termometer)" if "tercatat" in col_min else "Suhu Min (obs)"

    fig.add_trace(go.Scatter(
        x=pd.concat([df_daily["date"], df_daily["date"][::-1]]),
        y=pd.concat([df_daily[col_max], df_daily[col_min][::-1]]),
        fill="toself", fillcolor="rgba(26,107,154,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Rentang Tmax–Tmin", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily[col_max],
        line=dict(color=COLOR_DANGER, width=1.5, dash="dot"),
        name=label_max, mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily[col_min],
        line=dict(color="#3b82f6", width=1.5, dash="dot"),
        name=label_min, mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily["suhu_rerata_c"],
        line=dict(color=COLOR_PRIMARY, width=2.5),
        name="Suhu Rata-rata", mode="lines",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Suhu Udara Harian (°C)",
        yaxis_title="Suhu (°C)", height=320,
    )
    return fig

def chart_kelembaban(df_daily):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily["kelembaban_rerata_pct"],
        line=dict(color="#0ea5e9", width=2.5),
        fill="tozeroy", fillcolor="rgba(14,165,233,0.07)",
        name="Kelembaban Rata-rata",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Kelembaban Relatif Harian (%)",
        yaxis_title="RH (%)", yaxis_range=[40, 105], height=280,
    )
    return fig

def chart_curah_hujan(df_daily):
    farbe = ["#bfdbfe" if r < 5 else "#60a5fa" if r < 20
             else "#2563eb" if r < 50 else "#1d4ed8"
             for r in df_daily["curah_hujan_24h_mm"].fillna(0)]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_daily["date"],
        y=df_daily["curah_hujan_24h_mm"].fillna(0),
        marker_color=farbe,
        name="Curah Hujan 24H",
        hovertemplate="%{x|%d %b %Y}<br>%{y:.1f} mm<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Curah Hujan Harian (mm)",
        yaxis_title="Curah Hujan (mm)", height=280, bargap=0.15,
    )
    return fig

def chart_curah_hujan_monthly(df_daily):
    df = df_daily.copy()
    df["bulan"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("bulan")["curah_hujan_24h_mm"].sum().reset_index()
    fig = go.Figure(go.Bar(
        x=monthly["bulan"], y=monthly["curah_hujan_24h_mm"],
        marker_color=COLOR_PRIMARY,
        hovertemplate="%{x}<br>Total: %{y:.1f} mm<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Total Curah Hujan per Bulan (mm)",
        yaxis_title="mm", height=300, bargap=0.2,
    )
    return fig

def chart_wind_rose(df_hourly):
    """Wind rose chart menggunakan Plotly bar_polar."""
    df = df_hourly[df_hourly["wind_speed_ms"].notna() &
                   df_hourly["wind_dir_deg"].notna()].copy()

    bins = np.arange(-11.25, 371.25, 22.5)
    labels = ["U","UTL","TL","TTL","T","TTG","TG","STG",
              "S","SBD","BD","BBD","B","BBL","BL","UBL"]
    df["dir_bin"] = pd.cut(df["wind_dir_deg"] % 360, bins=bins, labels=labels)

    speed_bins   = [0, 2, 5, 10, 20, 999]
    speed_labels = ["0–2 m/s", "2–5 m/s", "5–10 m/s", "10–20 m/s", ">20 m/s"]
    speed_colors = ["#bfdbfe", "#60a5fa", "#2563eb", "#1d4ed8", "#1e3a8a"]
    df["speed_bin"] = pd.cut(df["wind_speed_ms"], bins=speed_bins, labels=speed_labels)

    fig = go.Figure()
    for label, color in zip(speed_labels, speed_colors):
        sub = df[df["speed_bin"] == label]
        counts = sub["dir_bin"].value_counts().reindex(labels, fill_value=0)
        fig.add_trace(go.Barpolar(
            r=counts.values,
            theta=labels,
            name=label,
            marker_color=color,
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(showticklabels=True, tickfont_size=9, gridcolor="#e5e7eb"),
            angularaxis=dict(direction="clockwise", rotation=90),
            bgcolor="white",
        ),
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center", font_size=11),
        paper_bgcolor="white", font_family="DM Sans",
        title="Wind Rose — Distribusi Arah & Kecepatan Angin",
        height=400, margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig

def chart_wind_speed(df_daily):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily["kec_angin_max_ms"],
        line=dict(color=COLOR_SECONDARY, width=1.5, dash="dot"),
        name="Kec. Angin Max", mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily["kec_angin_rerata_ms"],
        line=dict(color=COLOR_PRIMARY, width=2.5),
        fill="tozeroy", fillcolor="rgba(26,107,154,0.07)",
        name="Kec. Angin Rata-rata",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Kecepatan Angin Harian (m/s)",
        yaxis_title="m/s", height=280,
    )
    return fig

def chart_tekanan(df_daily):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily["tekanan_qff_rerata_mb"],
        line=dict(color="#7c3aed", width=2),
        name="Tekanan QFF (muka laut)",
    ))
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily["tekanan_qfe_rerata_mb"],
        line=dict(color="#a78bfa", width=1.5, dash="dot"),
        name="Tekanan QFE (stasiun)",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Tekanan Udara Harian (mb/hPa)",
        yaxis_title="mb", height=300,
    )
    return fig

def chart_penyinaran(df_daily):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_daily["date"], y=df_daily["lama_penyinaran_jam"],
        marker_color="#fbbf24", name="Lama Penyinaran",
        hovertemplate="%{x|%d %b}<br>%{y:.1f} jam<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Lama Penyinaran Matahari Harian (jam)",
        yaxis_title="Jam", yaxis_range=[0, 13], height=260, bargap=0.1,
    )
    return fig

def chart_cloud_visibility(df_daily):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily["tutupan_awan_rerata"],
        line=dict(color="#94a3b8", width=2),
        fill="tozeroy", fillcolor="rgba(148,163,184,0.15)",
        name="Tutupan Awan (oktas)",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily["visibility_rerata_km"],
        line=dict(color="#0ea5e9", width=2),
        name="Visibilitas (km)",
    ), secondary_y=True)
    base = {k: v for k, v in PLOTLY_LAYOUT.items() if k != "legend"}
    fig.update_layout(
        **base,
        title="Tutupan Awan & Visibilitas",
        height=290,
        legend=dict(orientation="h", y=1.08, x=0, bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_yaxes(title_text="Oktas (0–9)", secondary_y=False, range=[0, 10])
    fig.update_yaxes(title_text="Visibilitas (km)", secondary_y=True)
    return fig

def chart_monthly_klimat(df_daily):
    df = df_daily.copy()
    df["bulan"] = df["date"].dt.month
    BULAN = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"]
    col_max = ("suhu_max_tercatat_c"
               if df_daily["suhu_max_tercatat_c"].notna().sum() > 0
               else "suhu_max_obs_c")
    col_min = ("suhu_min_tercatat_c"
               if df_daily["suhu_min_tercatat_c"].notna().sum() > 0
               else "suhu_min_obs_c")

    monthly = df.groupby("bulan").agg(
        suhu_rerata=("suhu_rerata_c",         "mean"),
        suhu_max   =(col_max,                 "mean"),
        suhu_min   =(col_min,                 "mean"),
        hujan_total=("curah_hujan_24h_mm",    "mean"),
        rh_rerata  =("kelembaban_rerata_pct", "mean"),
        sunshine   =("lama_penyinaran_jam",   "mean"),
    ).reset_index()
    monthly["bulan_str"] = monthly["bulan"].apply(lambda x: BULAN[x-1])

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Suhu Udara (°C) — Rata-rata, Max & Min",
            "Rerata Curah Hujan Harian (mm)",
            "Kelembaban Relatif (%)",
            "Lama Penyinaran Matahari (jam)",
        ],
        vertical_spacing=0.22, horizontal_spacing=0.12,
    )

    t_min_val = monthly["suhu_min"].min()
    t_max_val = monthly["suhu_max"].max()
    t_pad     = max((t_max_val - t_min_val) * 0.3, 0.5)

    fig.add_trace(go.Scatter(
        x=pd.concat([monthly["bulan_str"], monthly["bulan_str"][::-1]]),
        y=pd.concat([monthly["suhu_max"], monthly["suhu_min"][::-1]]),
        fill="toself", fillcolor="rgba(26,107,154,0.10)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Rentang Max-Min", showlegend=False, hoverinfo="skip",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=monthly["bulan_str"], y=monthly["suhu_max"].round(2),
        line=dict(color="#ef4444", width=1.5, dash="dot"),
        mode="lines+markers", marker_size=5,
        name="Max", showlegend=False,
        hovertemplate="%{x}<br>Max: %{y:.2f}°C<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=monthly["bulan_str"], y=monthly["suhu_min"].round(2),
        line=dict(color="#3b82f6", width=1.5, dash="dot"),
        mode="lines+markers", marker_size=5,
        name="Min", showlegend=False,
        hovertemplate="%{x}<br>Min: %{y:.2f}°C<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=monthly["bulan_str"], y=monthly["suhu_rerata"].round(2),
        line=dict(color=COLOR_PRIMARY, width=2.5),
        mode="lines+markers", marker_size=7,
        showlegend=False,
        hovertemplate="%{x}<br>Rata-rata: %{y:.2f}°C<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=monthly["bulan_str"], y=monthly["hujan_total"].round(1),
        marker_color="#2563eb", showlegend=False,
        hovertemplate="%{x}: %{y:.1f} mm<extra></extra>",
    ), row=1, col=2)

    rh_min = monthly["rh_rerata"].min()
    rh_max = monthly["rh_rerata"].max()
    rh_pad = max((rh_max - rh_min) * 0.4, 1.0)
    fig.add_trace(go.Scatter(
        x=monthly["bulan_str"], y=monthly["rh_rerata"].round(2),
        line=dict(color="#0ea5e9", width=2.5),
        fill="tozeroy", fillcolor="rgba(14,165,233,0.08)",
        mode="lines+markers", marker_size=6, showlegend=False,
        hovertemplate="%{x}: %{y:.2f}%<extra></extra>",
    ), row=2, col=1)

    fig.add_trace(go.Bar(
        x=monthly["bulan_str"], y=monthly["sunshine"].round(1),
        marker_color="#fbbf24", showlegend=False,
        hovertemplate="%{x}: %{y:.1f} jam<extra></extra>",
    ), row=2, col=2)

    fig.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        font_family="DM Sans", height=580,
        title_text="Klimatologi Bulanan — Rata-rata Seluruh Periode Data",
        margin=dict(l=20, r=20, t=70, b=20),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#f0f2f5")
    fig.update_yaxes(range=[t_min_val - t_pad, t_max_val + t_pad], row=1, col=1)
    fig.update_yaxes(range=[rh_min - rh_pad, rh_max + rh_pad], row=2, col=1)
    return fig

def chart_hourly_heatmap(df_hourly, kolom="suhu_bola_kering_c", judul="Suhu (°C)"):
    df = df_hourly.copy()
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    pivot = df.pivot_table(index="date", columns="hour", values=kolom, aggfunc="mean")

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}:00" for h in pivot.columns],
        y=[str(d) for d in pivot.index],
        colorscale="RdYlBu_r" if "suhu" in kolom else "Blues",
        hovertemplate="Jam %{x}<br>%{y}<br>%{z:.1f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="white", font_family="DM Sans",
        title=f"Heatmap Per Jam — {judul}",
        xaxis_title="Jam (UTC)", height=380,
        margin=dict(l=10, r=10, t=50, b=10),
        yaxis=dict(autorange="reversed"),
    )
    return fig

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:12px 0 16px">
        <svg width="42" height="42" viewBox="0 0 36 36" fill="none" xmlns="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEi3zT4nNl9s-3YqjTJI0i2Cx2cjNCjPwIyr_i9l3AiG_I4AIbMfRND_geWovxI-p6x3tqRcaLeHk3iBQjnQhiQ57dXLGZNxvUKeEV8ktb79Dbu3cW_zmAVyjFFt1M3N99UqwcnfM-gajpDaoZRgXYWNU5WLK-keWUWsrZJL2SnVOFYIw_chbHwwGAE-/s320/GKL29_BMKG%20-%20Koleksilogo.com.jpg" style="margin-bottom:6px">
          <circle cx="18" cy="18" r="17" fill="#e0f0fa" stroke="#1a6b9a" stroke-width="1.2"/>
          <circle cx="18" cy="18" r="10" fill="none" stroke="#1a6b9a" stroke-width="1.5"/>
          <circle cx="18" cy="18" r="3.5" fill="#1a6b9a"/>
          <line x1="18" y1="3" x2="18" y2="8"   stroke="#1a6b9a" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="18" y1="28" x2="18" y2="33" stroke="#1a6b9a" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="3"  y1="18" x2="8"  y2="18" stroke="#1a6b9a" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="28" y1="18" x2="33" y2="18" stroke="#1a6b9a" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="7.5"  y1="7.5"  x2="11"   y2="11"   stroke="#1a6b9a" stroke-width="1.2" stroke-linecap="round"/>
          <line x1="25"   y1="25"   x2="28.5" y2="28.5" stroke="#1a6b9a" stroke-width="1.2" stroke-linecap="round"/>
          <line x1="28.5" y1="7.5"  x2="25"   y2="11"   stroke="#1a6b9a" stroke-width="1.2" stroke-linecap="round"/>
          <line x1="11"   y1="25"   x2="7.5"  y2="28.5" stroke="#1a6b9a" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        <div style="font-size:13px;font-weight:600;color:#1a1f2e">BMKG Fatmawati</div>
        <div style="font-size:11px;color:#9ca3af;margin-top:2px">WMO ID: 96253 · Bengkulu</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("**Filter Periode**")

    date_min, date_max = load_date_range()
    if date_min is None:
        date_min = datetime(2022, 1, 1)
        date_max = datetime.today()

    col_a, col_b = st.columns(2)
    with col_a:
        tgl_mulai = st.date_input("Dari",
                                   value=date_max - timedelta(days=90),
                                   min_value=date_min, max_value=date_max)
    with col_b:
        tgl_akhir = st.date_input("Hingga",
                                   value=date_max,
                                   min_value=date_min, max_value=date_max)

    st.divider()

    engine = get_engine()
    if engine:
        st.markdown('<span class="badge badge-green">● Database terhubung</span>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-red">● Koneksi gagal</span>',
                    unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-size:11px;color:#9ca3af;margin-top:12px">
        Data di-refresh otomatis setiap 1 jam.<br>
        Update terakhir pipeline: <b>00:00 WIB</b>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄  Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

date_from_str = str(tgl_mulai)
date_to_str   = str(tgl_akhir)

with st.spinner("Memuat data..."):
    df_daily  = load_daily(date_from_str, date_to_str)
    df_hourly = load_hourly(date_from_str, date_to_str)
    latest    = load_latest()

has_daily  = len(df_daily)  > 0
has_hourly = len(df_hourly) > 0

ts_latest = latest.get("timestamp", "—") if not latest.empty else "—"
ts_str    = pd.to_datetime(ts_latest).strftime("%d %b %Y, %H:%M UTC") if ts_latest != "—" else "—"

ww_val = latest.get("cuaca_sekarang_ww") if not latest.empty else None
st.markdown(weather_bg_html(ww_val), unsafe_allow_html=True)

BMKG_LOGO = """
<img src="https://www.bmkg.go.id/images/profil/logo-bmkg.png"
     width="48" height="48"
     style="object-fit:contain;filter:brightness(0) invert(1);opacity:0.92;"
     alt="Logo BMKG">"""

st.markdown(f"""
<div class="main-header">
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:12px;">
        {BMKG_LOGO}
        <div>
            <h1>Dashboard Pemantauan Cuaca</h1>
            <p>Stasiun Meteorologi Kelas I Fatmawati Bengkulu · Analisis Data Sinoptik</p>
        </div>
    </div>
    <div class="header-meta">
        <span>📅 {date_from_str} – {date_to_str}</span>
        <span>🕐 Observasi terakhir: {ts_str}</span>
        <span>📊 {len(df_daily)} hari · {len(df_hourly):,} jam data</span>
    </div>
</div>
""", unsafe_allow_html=True)

if not latest.empty:
    ww_label = cuaca_label(ww_val)
    st.markdown(f"""
    <div class="metrics-wrapper">
        <div class="metrics-label">🔴&nbsp; Kondisi Terkini — Observasi per jam terakhir</div>
    """, unsafe_allow_html=True)

    cols = st.columns(6)
    metrics = [
        ("Suhu Udara",  f'{latest.get("suhu_bola_kering_c","—"):.1f}',  "°C"),
        ("Kelembaban",  f'{latest.get("kelembaban_relatif_pct","—"):.0f}', "%"),
        ("Tekanan QFF", f'{latest.get("tekanan_qff_mb","—"):.1f}',       "mb"),
        ("Kec. Angin",  f'{latest.get("wind_speed_ms","—"):.1f}',        "m/s"),
        ("Arah Angin",
         wind_dir_label(latest.get("wind_dir_deg", 0))
         if pd.notna(latest.get("wind_dir_deg")) else "—", ""),
        ("Cuaca", ww_label, ""),
    ]
    for col, (label, val, unit) in zip(cols, metrics):
        col.markdown(metric_html(label, val, unit), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🌡️  Suhu & Kelembaban",
    "🌧️  Curah Hujan",
    "💨  Angin",
    "☁️  Awan & Visibilitas",
    "🔵  Tekanan Udara",
    "📊  Klimatologi",
])

with tab1:
    if not has_daily:
        st.warning("Tidak ada data untuk periode yang dipilih.")
    else:
        c1, c2, c3, c4 = st.columns(4)

        suhu_max_val = df_daily["suhu_max_tercatat_c"].dropna()
        suhu_min_val = df_daily["suhu_min_tercatat_c"].dropna()
        suhu_max_str = (f'{suhu_max_val.max():.1f} °C' if len(suhu_max_val) > 0
                        else f'{df_daily["suhu_max_obs_c"].max():.1f} °C*')
        suhu_min_str = (f'{suhu_min_val.min():.1f} °C' if len(suhu_min_val) > 0
                        else f'{df_daily["suhu_min_obs_c"].min():.1f} °C*')

        c1.metric("Suhu Rata-rata",
                  f'{df_daily["suhu_rerata_c"].mean():.1f} °C')
        c2.metric("Suhu Tertinggi", suhu_max_str, delta=None)
        c3.metric("Suhu Terendah",  suhu_min_str)
        c4.metric("RH Rata-rata",
                  f'{df_daily["kelembaban_rerata_pct"].mean():.0f} %')

        st.plotly_chart(chart_timeseries_suhu(df_daily),
                        use_container_width=True)
        st.plotly_chart(chart_kelembaban(df_daily),
                        use_container_width=True)

        if has_hourly:
            st.markdown("---")
            col_heat = st.selectbox("Variabel heatmap per jam",
                ["suhu_bola_kering_c", "kelembaban_relatif_pct",
                 "suhu_titik_embun_c"],
                format_func=lambda x: {
                    "suhu_bola_kering_c"    : "Suhu Bola Kering (°C)",
                    "kelembaban_relatif_pct": "Kelembaban Relatif (%)",
                    "suhu_titik_embun_c"    : "Suhu Titik Embun (°C)",
                }[x])
            judul_map = {
                "suhu_bola_kering_c"    : "Suhu Bola Kering (°C)",
                "kelembaban_relatif_pct": "Kelembaban Relatif (%)",
                "suhu_titik_embun_c"    : "Suhu Titik Embun (°C)",
            }
            st.plotly_chart(chart_hourly_heatmap(df_hourly, col_heat,
                                                  judul_map[col_heat]),
                            use_container_width=True)

with tab2:
    if not has_daily:
        st.warning("Tidak ada data untuk periode yang dipilih.")
    else:
        total_hujan  = df_daily["curah_hujan_24h_mm"].sum()
        hari_hujan   = (df_daily["curah_hujan_24h_mm"] > 0).sum()
        max_hujan    = df_daily["curah_hujan_24h_mm"].max()
        hari_ekstrem = (df_daily["curah_hujan_24h_mm"] >= 50).sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Curah Hujan", f'{total_hujan:.0f} mm')
        c2.metric("Hari Hujan", f'{hari_hujan} hari')
        c3.metric("Curah Hujan Max", f'{max_hujan:.1f} mm')
        c4.metric("Hari Ekstrem (≥50mm)", f'{hari_ekstrem} hari')

        st.plotly_chart(chart_curah_hujan(df_daily),
                        use_container_width=True)
        st.plotly_chart(chart_curah_hujan_monthly(df_daily),
                        use_container_width=True)

        st.markdown("---")
        st.markdown('<p class="section-title">10 Hari dengan Curah Hujan Tertinggi</p>',
                    unsafe_allow_html=True)
        top10 = (df_daily[["date","curah_hujan_24h_mm","jam_hujan"]]
                 .sort_values("curah_hujan_24h_mm", ascending=False)
                 .head(10)
                 .rename(columns={
                     "date"              : "Tanggal",
                     "curah_hujan_24h_mm": "Curah Hujan (mm)",
                     "jam_hujan"         : "Jam Hujan",
                 }))
        top10["Tanggal"] = top10["Tanggal"].dt.strftime("%d %B %Y")
        st.dataframe(top10, hide_index=True, use_container_width=True)

with tab3:
    if not has_hourly or not has_daily:
        st.warning("Tidak ada data untuk periode yang dipilih.")
    else:
        avg_speed = df_hourly["wind_speed_ms"].mean()
        max_speed = df_hourly["wind_speed_ms"].max()
        calm_pct  = (df_hourly["wind_speed_ms"] < 0.5).mean() * 100
        dom_dir   = wind_dir_label(
            df_hourly["wind_dir_deg"].dropna().apply(
                lambda x: np.rad2deg(np.arctan2(
                    np.sin(np.deg2rad(x)), np.cos(np.deg2rad(x))
                )) % 360
            ).mean()
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Kec. Rata-rata", f'{avg_speed:.1f} m/s')
        c2.metric("Kec. Maksimum",  f'{max_speed:.1f} m/s')
        c3.metric("Arah Dominan",   dom_dir)
        c4.metric("Kondisi Tenang (< 0.5 m/s)", f'{calm_pct:.1f}%')

        col_l, col_r = st.columns([1, 1])
        with col_l:
            st.plotly_chart(chart_wind_rose(df_hourly),
                            use_container_width=True)
        with col_r:
            st.plotly_chart(chart_wind_speed(df_daily),
                            use_container_width=True)

with tab4:
    if not has_daily:
        st.warning("Tidak ada data untuk periode yang dipilih.")
    else:
        avg_cloud = df_daily["tutupan_awan_rerata"].mean()
        avg_vis   = df_daily["visibility_rerata_km"].mean()
        avg_sun   = df_daily["lama_penyinaran_jam"].mean()
        kabut_pct = (df_daily["visibility_rerata_km"] < 1).mean() * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tutupan Awan Rata-rata", f'{avg_cloud:.1f} oktas')
        c2.metric("Visibilitas Rata-rata",  f'{avg_vis:.1f} km')
        c3.metric("Penyinaran Rata-rata",   f'{avg_sun:.1f} jam/hari')
        c4.metric("Hari Berkabut (<1km)",   f'{kabut_pct:.1f}%')

        st.plotly_chart(chart_cloud_visibility(df_daily),
                        use_container_width=True)
        st.plotly_chart(chart_penyinaran(df_daily),
                        use_container_width=True)

with tab5:
    if not has_daily:
        st.warning("Tidak ada data untuk periode yang dipilih.")
    else:
        avg_qff = df_daily["tekanan_qff_rerata_mb"].mean()
        avg_qfe = df_daily["tekanan_qfe_rerata_mb"].mean()
        max_qff = df_daily["tekanan_qff_rerata_mb"].max()
        min_qff = df_daily["tekanan_qff_rerata_mb"].min()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("QFF Rata-rata", f'{avg_qff:.1f} mb')
        c2.metric("QFE Rata-rata", f'{avg_qfe:.1f} mb')
        c3.metric("QFF Tertinggi", f'{max_qff:.1f} mb')
        c4.metric("QFF Terendah",  f'{min_qff:.1f} mb')

        st.plotly_chart(chart_tekanan(df_daily),
                        use_container_width=True)

        if has_hourly:
            st.markdown("---")
            st.plotly_chart(chart_hourly_heatmap(
                df_hourly, "tekanan_qff_mb", "Tekanan QFF (mb)"
            ), use_container_width=True)

with tab6:
    if not has_daily:
        st.warning("Tidak ada data untuk periode yang dipilih.")
    elif len(df_daily) < 30:
        st.info("Pilih periode minimal 30 hari untuk analisis klimatologi.")
    else:
        st.plotly_chart(chart_monthly_klimat(df_daily),
                        use_container_width=True)

        st.markdown("---")
        st.markdown('<p class="section-title">Statistik Deskriptif Periode Terpilih</p>',
                    unsafe_allow_html=True)
        stats_cols = {
            "suhu_rerata_c"         : "Suhu Rata-rata (°C)",
            "suhu_max_tercatat_c"   : "Suhu Max (°C)",
            "suhu_min_tercatat_c"   : "Suhu Min (°C)",
            "kelembaban_rerata_pct" : "Kelembaban (%)",
            "curah_hujan_24h_mm"    : "Curah Hujan (mm)",
            "lama_penyinaran_jam"   : "Penyinaran (jam)",
            "kec_angin_rerata_ms"   : "Kec. Angin (m/s)",
        }
        stat_df = (df_daily[[c for c in stats_cols if c in df_daily.columns]]
                   .rename(columns=stats_cols)
                   .describe().T
                   .round(2)
                   [["mean","std","min","25%","50%","75%","max"]])
        stat_df.columns = ["Rata-rata","Std. Dev","Min","Q25","Median","Q75","Max"]
        st.dataframe(stat_df, use_container_width=True)
