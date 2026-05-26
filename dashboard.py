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

# ─────────────────────────────────────────────
# KONFIGURASI HALAMAN
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="BMKG Fatmawati — Dashboard Cuaca",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS CUSTOM — TAMPILAN PROFESIONAL
# ─────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Header utama */
.main-header {
    background: linear-gradient(135deg, #1a6b9a 0%, #0d4f75 100%);
    color: white;
    padding: 24px 32px;
    border-radius: 12px;
    margin-bottom: 24px;
}
.main-header h1 {
    margin: 0 0 4px;
    font-size: 22px;
    font-weight: 600;
    letter-spacing: -0.3px;
}
.main-header p {
    margin: 0;
    font-size: 13px;
    opacity: 0.75;
    font-weight: 300;
}
.header-meta {
    display: flex;
    gap: 24px;
    margin-top: 14px;
}
.header-meta span {
    font-size: 12px;
    opacity: 0.65;
    font-family: 'DM Mono', monospace;
}

/* Metric cards */
.metric-card {
    background: white;
    border: 1px solid #e8ecf0;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.metric-label {
    font-size: 11px;
    color: #6b7280;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 28px;
    font-weight: 600;
    color: #1a1f2e;
    line-height: 1;
    font-family: 'DM Mono', monospace;
}
.metric-unit {
    font-size: 13px;
    color: #9ca3af;
    margin-left: 3px;
    font-weight: 400;
}
.metric-delta {
    font-size: 11px;
    margin-top: 4px;
}
.metric-delta.up   { color: #ef4444; }
.metric-delta.down { color: #3b82f6; }
.metric-delta.same { color: #9ca3af; }

/* Section headers */
.section-title {
    font-size: 14px;
    font-weight: 600;
    color: #374151;
    margin: 0 0 2px;
    letter-spacing: -0.1px;
}
.section-sub {
    font-size: 12px;
    color: #9ca3af;
    margin: 0 0 14px;
}

/* Status badge */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
}
.badge-green  { background:#dcfce7; color:#166534; }
.badge-yellow { background:#fef9c3; color:#854d0e; }
.badge-red    { background:#fee2e2; color:#991b1b; }
.badge-blue   { background:#dbeafe; color:#1e40af; }

/* Tabs custom */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #f5f7fa;
    padding: 4px;
    border-radius: 10px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 500;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #f9fafb;
    border-right: 1px solid #e8ecf0;
}

/* Hide Streamlit default branding */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# KONEKSI DATABASE
# ─────────────────────────────────────────────

@st.cache_resource
def get_engine():
    """Membuat koneksi ke Supabase PostgreSQL."""
    try:
        # Prioritas: Streamlit Secrets (cloud) → .env (lokal)
        if "database" in st.secrets:
            db = st.secrets["database"]
            host, port, name = db["host"], db["port"], db["name"]
            user, pw = db["user"], db["password"]
        else:
            host = os.getenv("DB_HOST")
            port = os.getenv("DB_PORT", "5432")
            name = os.getenv("DB_NAME", "postgres")
            user = os.getenv("DB_USER", "postgres")
            pw   = os.getenv("DB_PASSWORD")

        url = f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{name}"
        engine = create_engine(url, pool_pre_ping=True)
        # Test koneksi
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.error(f"❌ Gagal konek ke database: {e}")
        return None


# ─────────────────────────────────────────────
# FUNGSI LOAD DATA (dengan cache 1 jam)
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_daily(date_from: str, date_to: str) -> pd.DataFrame:
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()
    q = f"""
        SELECT * FROM clean_daily
        WHERE date BETWEEN '{date_from}' AND '{date_to}'
        ORDER BY date
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def load_hourly(date_from: str, date_to: str) -> pd.DataFrame:
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()
    q = f"""
        SELECT * FROM clean_hourly
        WHERE timestamp BETWEEN '{date_from}' AND '{date_to} 23:59:59'
        ORDER BY timestamp
    """
    df = pd.read_sql(q, engine)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def load_latest() -> pd.Series:
    """Ambil observasi terakhir untuk monitoring real-time."""
    engine = get_engine()
    if engine is None:
        return pd.Series()
    q = "SELECT * FROM clean_hourly ORDER BY timestamp DESC LIMIT 1"
    df = pd.read_sql(q, engine)
    return df.iloc[0] if len(df) > 0 else pd.Series()


@st.cache_data(ttl=3600, show_spinner=False)
def load_date_range():
    engine = get_engine()
    if engine is None:
        return None, None
    q = "SELECT MIN(date)::date as mn, MAX(date)::date as mx FROM clean_daily"
    row = pd.read_sql(q, engine).iloc[0]
    return pd.to_datetime(row["mn"]), pd.to_datetime(row["mx"])


# ─────────────────────────────────────────────
# HELPER & FORMATTER
# ─────────────────────────────────────────────

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
    dirs = ["U", "UTL", "TL", "TTL", "T", "TTG", "TG", "BTG",
            "B", "BBD", "BD", "SBD", "S", "SBT", "BT", "UBT"]
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


def metric_html(label, value, unit="", delta=None, delta_label=""):
    delta_html = ""
    if delta is not None:
        cls = "up" if delta > 0 else ("down" if delta < 0 else "same")
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
        delta_html = f'<div class="metric-delta {cls}">{arrow} {abs(delta):.1f} {delta_label}</div>'
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
        {delta_html}
    </div>"""


# ─────────────────────────────────────────────
# FUNGSI CHART
# ─────────────────────────────────────────────

def chart_timeseries_suhu(df_daily):
    fig = go.Figure()
    # Range area Tmin–Tmax
    fig.add_trace(go.Scatter(
        x=pd.concat([df_daily["date"], df_daily["date"][::-1]]),
        y=pd.concat([df_daily["suhu_max_tercatat_c"], df_daily["suhu_min_tercatat_c"][::-1]]),
        fill="toself", fillcolor="rgba(26,107,154,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Rentang Tmax–Tmin", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily["suhu_max_tercatat_c"],
        line=dict(color=COLOR_DANGER, width=1.5, dash="dot"),
        name="Suhu Max", mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=df_daily["date"], y=df_daily["suhu_min_tercatat_c"],
        line=dict(color="#3b82f6", width=1.5, dash="dot"),
        name="Suhu Min", mode="lines",
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

    # Binning arah ke 16 sektor
    bins = np.arange(-11.25, 371.25, 22.5)
    labels = ["U","UTL","TL","TTL","T","TTG","TG","BTG",
              "B","BBD","BD","SBD","S","SBT","BT","UBT"]
    df["dir_bin"] = pd.cut(df["wind_dir_deg"] % 360, bins=bins, labels=labels)

    # Binning kecepatan
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
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Tutupan Awan & Visibilitas",
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
    monthly = df.groupby("bulan").agg(
        suhu_rerata=("suhu_rerata_c", "mean"),
        hujan_total=("curah_hujan_24h_mm", "mean"),
        rh_rerata=("kelembaban_rerata_pct", "mean"),
        sunshine=("lama_penyinaran_jam", "mean"),
    ).reset_index()
    monthly["bulan_str"] = monthly["bulan"].apply(lambda x: BULAN[x-1])

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Suhu Rata-rata (°C)", "Rerata Curah Hujan Harian (mm)",
            "Kelembaban Relatif (%)", "Lama Penyinaran (jam)"
        ],
        vertical_spacing=0.18, horizontal_spacing=0.12,
    )
    clr = [COLOR_PRIMARY, "#2563eb", "#0ea5e9", "#fbbf24"]
    data_cols = ["suhu_rerata", "hujan_total", "rh_rerata", "sunshine"]
    positions = [(1,1), (1,2), (2,1), (2,2)]

    for (r, c), col, color in zip(positions, data_cols, clr):
        fig.add_trace(go.Bar(
            x=monthly["bulan_str"], y=monthly[col].round(1),
            marker_color=color, showlegend=False,
            hovertemplate="%{x}: %{y}<extra></extra>",
        ), row=r, col=c)

    fig.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        font_family="DM Sans", height=500,
        title_text="Klimatologi Bulanan — Rata-rata Seluruh Periode Data",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    for i in range(1, 5):
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="#f0f2f5")
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


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:12px 0 16px">
        <div style="font-size:28px">🌤️</div>
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
        tgl_mulai = st.date_input("Dari", value=date_max - timedelta(days=90),
                                   min_value=date_min, max_value=date_max)
    with col_b:
        tgl_akhir = st.date_input("Hingga", value=date_max,
                                   min_value=date_min, max_value=date_max)

    # Shortcut periode
    st.markdown("<div style='font-size:11px;color:#9ca3af;margin-bottom:6px'>Shortcut</div>",
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("30H",  use_container_width=True):
        tgl_mulai = date_max - timedelta(days=30)
        tgl_akhir = date_max
    if c2.button("90H",  use_container_width=True):
        tgl_mulai = date_max - timedelta(days=90)
        tgl_akhir = date_max
    if c3.button("Semua", use_container_width=True):
        tgl_mulai = date_min
        tgl_akhir = date_max

    st.divider()

    # Status koneksi
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


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────

date_from_str = str(tgl_mulai)
date_to_str   = str(tgl_akhir)

with st.spinner("Memuat data..."):
    df_daily  = load_daily(date_from_str, date_to_str)
    df_hourly = load_hourly(date_from_str, date_to_str)
    latest    = load_latest()

has_daily  = len(df_daily)  > 0
has_hourly = len(df_hourly) > 0


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

ts_latest = latest.get("timestamp", "—") if not latest.empty else "—"
ts_str    = pd.to_datetime(ts_latest).strftime("%d %b %Y, %H:%M UTC") if ts_latest != "—" else "—"

st.markdown(f"""
<div class="main-header">
    <h1>Dashboard Pemantauan Cuaca</h1>
    <p>Stasiun Meteorologi Kelas I Fatmawati Bengkulu · Analisis Data Sinoptik</p>
    <div class="header-meta">
        <span>📅 {date_from_str} – {date_to_str}</span>
        <span>🕐 Observasi terakhir: {ts_str}</span>
        <span>📊 {len(df_daily)} hari · {len(df_hourly):,} jam data</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# METRIC CARDS — KONDISI TERKINI
# ─────────────────────────────────────────────

if not latest.empty:
    st.markdown('<p class="section-title">Kondisi Terkini</p>'
                '<p class="section-sub">Observasi per jam terakhir yang tersimpan di database</p>',
                unsafe_allow_html=True)

    cols = st.columns(6)
    metrics = [
        ("Suhu Udara",      f'{latest.get("suhu_bola_kering_c","—"):.1f}',  "°C"),
        ("Kelembaban",       f'{latest.get("kelembaban_relatif_pct","—"):.0f}', "%"),
        ("Tekanan QFF",      f'{latest.get("tekanan_qff_mb","—"):.1f}',      "mb"),
        ("Kec. Angin",       f'{latest.get("wind_speed_ms","—"):.1f}',       "m/s"),
        ("Arah Angin",
         wind_dir_label(latest.get("wind_dir_deg", 0))
         if pd.notna(latest.get("wind_dir_deg")) else "—", ""),
        ("Cuaca",
         cuaca_label(latest.get("cuaca_sekarang_ww")), ""),
    ]
    for col, (label, val, unit) in zip(cols, metrics):
        col.markdown(metric_html(label, val, unit), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABS UTAMA
# ─────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🌡️  Suhu & Kelembaban",
    "🌧️  Curah Hujan",
    "💨  Angin",
    "☁️  Awan & Visibilitas",
    "🔵  Tekanan Udara",
    "📊  Klimatologi",
])


# ── TAB 1: SUHU & KELEMBABAN ──────────────────
with tab1:
    if not has_daily:
        st.warning("Tidak ada data untuk periode yang dipilih.")
    else:
        # KPI ringkasan periode
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Suhu Rata-rata",
                  f'{df_daily["suhu_rerata_c"].mean():.1f} °C')
        c2.metric("Suhu Tertinggi",
                  f'{df_daily["suhu_max_tercatat_c"].max():.1f} °C',
                  delta=None)
        c3.metric("Suhu Terendah",
                  f'{df_daily["suhu_min_tercatat_c"].min():.1f} °C')
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


# ── TAB 2: CURAH HUJAN ───────────────────────
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

        # Tabel hari hujan terbesar
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


# ── TAB 3: ANGIN ─────────────────────────────
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


# ── TAB 4: AWAN & VISIBILITAS ─────────────────
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


# ── TAB 5: TEKANAN ────────────────────────────
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


# ── TAB 6: KLIMATOLOGI ────────────────────────
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
