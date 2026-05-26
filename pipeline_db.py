"""
pipeline_db.py
==============
BMKG Stasiun Fatmawati Bengkulu — Automated Data Pipeline
----------------------------------------------------------
Fungsi : Membaca data SYNOP raw, melakukan cleaning, lalu
         mengupload hasilnya ke Supabase PostgreSQL.

Dijalankan otomatis oleh GitHub Actions setiap tengah malam (00:00 WIB).
Bisa juga dijalankan manual:
    python pipeline_db.py

Dependensi:
    pip install pandas numpy psycopg2-binary sqlalchemy python-dotenv

Environment variables (simpan di .env lokal, atau GitHub Secrets):
    DB_HOST       = db.xxxxxxxxxxxx.supabase.co
    DB_PORT       = 5432
    DB_NAME       = postgres
    DB_USER       = postgres
    DB_PASSWORD   = your_supabase_password
    RAW_FILE_PATH = path/ke/RAW_SYNOP_REPORT.csv
"""

import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 1. KONFIGURASI
# ─────────────────────────────────────────────

RAW_FILE_PATH = os.getenv("RAW_FILE_PATH", "RAW_SYNOP_REPORT.csv")

DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "postgres")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

QC_BOUNDS = {
    "suhu_bola_kering_c"    : (15.0,  42.0),
    "suhu_titik_embun_c"    : (10.0,  32.0),
    "suhu_bola_basah_c"     : (15.0,  35.0),
    "kelembaban_relatif_pct": (20.0, 100.0),
    "tekanan_qff_mb"        : (990.0, 1030.0),
    "tekanan_qfe_mb"        : (990.0, 1020.0),
    "wind_speed_ms"         : (0.0,   50.0),
    "wind_dir_deg"          : (0.0,  360.0),
    "rainfall_mm"           : (0.0,  300.0),
    "visibility_km"         : (0.0,   80.0),
    "tutupan_awan_oktas"    : (0.0,    9.0),
}


# ─────────────────────────────────────────────
# 2. KONEKSI DATABASE
# ─────────────────────────────────────────────

def get_engine():
    """
    Membuat SQLAlchemy engine untuk koneksi ke Supabase PostgreSQL.
    Connection string dibaca dari environment variables.
    """
    if not all([DB_HOST, DB_PASSWORD]):
        raise EnvironmentError(
            "Variabel DB_HOST dan DB_PASSWORD belum diset. "
            "Periksa file .env atau GitHub Secrets."
        )
    url = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = create_engine(url, pool_pre_ping=True)
    log.info("Koneksi ke database berhasil dibuat.")
    return engine


# ─────────────────────────────────────────────
# 3. FUNGSI CLEANING
# ─────────────────────────────────────────────

def decode_rainfall(row):
    """
    Mendekode nilai curah hujan dari kolom RAINFALL LAST MM
    berdasarkan indikator IR (WMO-No. 306).

    IR = 4        → tidak hujan, return 0.0
    nilai = 8888  → trace/omitted, return NaN
    IR = 3        → pengukuran per jam, return nilai
    IR = 0,1,2    → akumulasi multi-jam, return nilai jika ada
    """
    ir  = row["RAINFALL INDICATOR IR"]
    val = row["RAINFALL LAST MM"]

    if ir == 4:
        return 0.0
    if pd.notna(val) and val == 8888:
        return np.nan
    if ir == 3:
        return val if pd.notna(val) else 0.0
    if ir in [0, 1, 2]:
        return val if pd.notna(val) else np.nan
    return np.nan


def circular_interpolate(series):
    """
    Interpolasi sirkular untuk arah angin (Mardia & Jupp, 2000).
    Menghindari error rata-rata linear pada variabel periodik (0°–360°).
    """
    rad   = np.deg2rad(series)
    sin_i = pd.Series(np.sin(rad)).interpolate(method="linear", limit_direction="both")
    cos_i = pd.Series(np.cos(rad)).interpolate(method="linear", limit_direction="both")
    return np.rad2deg(np.arctan2(sin_i, cos_i)) % 360


def run_cleaning(raw_path: str):
    """
    Membaca data SYNOP raw, melakukan seluruh tahapan cleaning,
    dan mengembalikan dua DataFrame: hourly dan daily.

    Parameters
    ----------
    raw_path : str
        Path ke file RAW_SYNOP_REPORT.csv

    Returns
    -------
    df_hourly : pd.DataFrame
    df_daily  : pd.DataFrame
    """
    log.info(f"Membaca data raw dari: {raw_path}")
    df = pd.read_csv(raw_path, low_memory=False)
    log.info(f"Data dimuat: {df.shape[0]:,} baris × {df.shape[1]} kolom")

    # ── Parse timestamp ──
    df["timestamp"] = pd.to_datetime(
        df["DATA TIMESTAMP"].str.replace(r"\s+\+.*", "", regex=True)
    )
    df["date"]  = df["timestamp"].dt.date
    df["hour"]  = df["timestamp"].dt.hour
    df["year"]  = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month
    df["day"]   = df["timestamp"].dt.day
    df = df.sort_values("timestamp").reset_index(drop=True)

    # ── Decode curah hujan ──
    df["rainfall_mm"] = df.apply(decode_rainfall, axis=1)

    # ── Interpolasi angin (sirkular) ──
    df["wind_dir_deg"]  = circular_interpolate(df["WIND DIR DEG DD"])
    df["wind_speed_ms"] = df["WIND SPEED FF"].interpolate(
        method="linear", limit_direction="both"
    )

    # ── Interpolasi linear — missing < 2% ──
    df["visibility_km"] = df["VISIBILITY VV"].interpolate(
        method="linear", limit_direction="both"
    )
    df["cloud_base_m"] = df["CLOUD BASE M H"].interpolate(
        method="linear", limit_direction="both"
    )

    # ── Rename kolom ──
    rename_map = {
        "TEMP DRYBULB C TTTTTT"      : "suhu_bola_kering_c",
        "TEMP DEWPOINT C TDTDTD"     : "suhu_titik_embun_c",
        "TEMP WETBULB C"             : "suhu_bola_basah_c",
        "RELATIVE HUMIDITY PC"       : "kelembaban_relatif_pct",
        "PRESSURE QFF MB DERIVED"    : "tekanan_qff_mb",
        "PRESSURE QFE MB DERIVED"    : "tekanan_qfe_mb",
        "PRESSURE TEND 3H MB PPP"    : "tendensi_tekanan_3h_mb",
        "CLOUD COVER OKTAS M"        : "tutupan_awan_oktas",
        "CLOUD LOW TYPE CL"          : "tipe_awan_rendah",
        "CLOUD MED TYPE CM"          : "tipe_awan_menengah",
        "CLOUD HIGH TYPE CH"         : "tipe_awan_tinggi",
        "CLOUD LAYER 2 HEIGHT M HSHS": "lapisan_awan2_tinggi_m",
        "CLOUD LAYER 2 AMT OKTAS NS" : "lapisan_awan2_oktas",
        "PRESENT WEATHER WW"         : "cuaca_sekarang_ww",
        "PAST WEATHER W1"            : "cuaca_lalu_w1",
    }
    df = df.rename(columns=rename_map)

    # ── Pilih kolom final (per jam) ──
    HOURLY_COLS = [
        "timestamp", "year", "month", "day", "hour",
        "suhu_bola_kering_c", "suhu_titik_embun_c", "suhu_bola_basah_c",
        "kelembaban_relatif_pct", "tekanan_qff_mb", "tekanan_qfe_mb",
        "tendensi_tekanan_3h_mb",
        "wind_dir_deg", "wind_speed_ms",
        "rainfall_mm",
        "visibility_km", "cloud_base_m", "tutupan_awan_oktas",
        "tipe_awan_rendah", "tipe_awan_menengah", "tipe_awan_tinggi",
        "lapisan_awan2_tinggi_m", "lapisan_awan2_oktas",
        "cuaca_sekarang_ww", "cuaca_lalu_w1",
    ]
    df_hourly = df[HOURLY_COLS].copy()

    # ── Quality Control ──
    df_hourly["qc_flag"] = "OK"
    n_suspect = 0
    for col, (lo, hi) in QC_BOUNDS.items():
        mask = df_hourly[col].notna() & (
            (df_hourly[col] < lo) | (df_hourly[col] > hi)
        )
        if mask.sum() > 0:
            df_hourly.loc[mask, "qc_flag"] = "SUSPECT"
            df_hourly.loc[mask, col] = np.nan
            n_suspect += mask.sum()
    log.info(f"QC selesai — {n_suspect} nilai di luar batas → NaN + flag SUSPECT")

    # ── Bangun tabel harian ──
    daily_agg = df_hourly.groupby(
        df_hourly["timestamp"].dt.date
    ).agg(
        year                  = ("year",                   "first"),
        month                 = ("month",                  "first"),
        day                   = ("day",                    "first"),
        suhu_rerata_c         = ("suhu_bola_kering_c",     "mean"),
        suhu_max_obs_c        = ("suhu_bola_kering_c",     "max"),
        suhu_min_obs_c        = ("suhu_bola_kering_c",     "min"),
        titik_embun_rerata_c  = ("suhu_titik_embun_c",     "mean"),
        kelembaban_rerata_pct = ("kelembaban_relatif_pct", "mean"),
        tekanan_qff_rerata_mb = ("tekanan_qff_mb",         "mean"),
        tekanan_qfe_rerata_mb = ("tekanan_qfe_mb",         "mean"),
        curah_hujan_total_mm  = ("rainfall_mm",            "sum"),
        jam_hujan             = ("rainfall_mm",            lambda x: (x > 0).sum()),
        visibility_rerata_km  = ("visibility_km",          "mean"),
        tutupan_awan_rerata   = ("tutupan_awan_oktas",     "mean"),
        kec_angin_max_ms      = ("wind_speed_ms",          "max"),
        kec_angin_rerata_ms   = ("wind_speed_ms",          "mean"),
        n_observasi           = ("suhu_bola_kering_c",     "count"),
    ).reset_index().rename(columns={"timestamp": "date"})

    daily_agg["date"] = pd.to_datetime(daily_agg["date"])

    df_12 = df[df["hour"] == 12][
        ["date", "TEMP MAX C TXTXTX", "TEMP MIN C TNTNTN"]
    ].copy()
    df_12["date"] = pd.to_datetime(df_12["date"])
    df_12 = df_12.rename(columns={
        "TEMP MAX C TXTXTX": "suhu_max_tercatat_c",
        "TEMP MIN C TNTNTN": "suhu_min_tercatat_c",
    })

    df_00 = df[df["hour"] == 0][
        ["date", "SUNSHINE H SSS", "RAINFALL 24H RRRR"]
    ].copy()
    df_00["date"] = pd.to_datetime(df_00["date"])
    df_00["RAINFALL 24H RRRR"] = df_00["RAINFALL 24H RRRR"].replace(8888, np.nan)
    df_00 = df_00.rename(columns={
        "SUNSHINE H SSS"   : "lama_penyinaran_jam",
        "RAINFALL 24H RRRR": "curah_hujan_24h_mm",
    })

    df_daily = daily_agg.merge(df_12, on="date", how="left")
    df_daily = df_daily.merge(df_00, on="date", how="left")

    numeric_cols = df_daily.select_dtypes(include=[np.number]).columns
    df_daily[numeric_cols] = df_daily[numeric_cols].round(2)

    log.info(
        f"Cleaning selesai — "
        f"hourly: {df_hourly.shape[0]:,} baris | "
        f"daily: {df_daily.shape[0]:,} baris"
    )
    return df_hourly, df_daily


# ─────────────────────────────────────────────
# 4. FUNGSI UPLOAD KE DATABASE
# ─────────────────────────────────────────────

def upload_to_db(df_hourly: pd.DataFrame, df_daily: pd.DataFrame, engine):
    """
    Mengupload kedua DataFrame ke tabel PostgreSQL di Supabase.

    Strategi: 'append' dengan deduplication — data yang sudah ada
    tidak akan diduplikat karena menggunakan INSERT ON CONFLICT DO NOTHING
    via primary key (timestamp untuk hourly, date untuk daily).

    Untuk kemudahan setup awal, kita pakai if_exists='replace' yang
    mengganti seluruh tabel. Ganti ke mode incremental setelah tabel
    stabil (lihat komentar di bawah).
    """

    # ── Mode: replace (untuk pertama kali / full refresh) ──
    # Ganti ke mode incremental setelah struktur tabel stabil.

    log.info("Mengupload tabel hourly ke Supabase...")
    df_hourly.to_sql(
        name      = "clean_hourly",
        con       = engine,
        if_exists = "replace",   # ganti ke "append" setelah pakai mode incremental
        index     = False,
        chunksize = 1000,
        method    = "multi",
    )
    log.info(f"  → clean_hourly: {len(df_hourly):,} baris berhasil diupload")

    log.info("Mengupload tabel daily ke Supabase...")
    df_daily.to_sql(
        name      = "clean_daily",
        con       = engine,
        if_exists = "replace",
        index     = False,
        chunksize = 500,
        method    = "multi",
    )
    log.info(f"  → clean_daily: {len(df_daily):,} baris berhasil diupload")


def upload_incremental(df_hourly: pd.DataFrame, df_daily: pd.DataFrame, engine):
    """
    Mode upload incremental — hanya menambah data baru yang belum ada di DB.
    Gunakan fungsi ini setelah tabel sudah terbentuk dan primary key sudah diset
    di Supabase (lihat panduan di README).

    Cara kerja:
    1. Query timestamp/date terbaru yang ada di DB
    2. Filter hanya baris yang lebih baru
    3. Append ke tabel yang sudah ada
    """
    with engine.connect() as conn:
        # Cek data terbaru di tabel hourly
        result = conn.execute(text("SELECT MAX(timestamp) FROM clean_hourly"))
        last_hourly = result.scalar()

        result = conn.execute(text("SELECT MAX(date) FROM clean_daily"))
        last_daily = result.scalar()

    if last_hourly:
        new_hourly = df_hourly[df_hourly["timestamp"] > pd.Timestamp(last_hourly)]
        log.info(f"Incremental hourly — {len(new_hourly)} baris baru sejak {last_hourly}")
    else:
        new_hourly = df_hourly
        log.info("Tabel hourly masih kosong, upload semua data.")

    if last_daily:
        new_daily = df_daily[df_daily["date"] > pd.Timestamp(last_daily)]
        log.info(f"Incremental daily — {len(new_daily)} baris baru sejak {last_daily}")
    else:
        new_daily = df_daily
        log.info("Tabel daily masih kosong, upload semua data.")

    if not new_hourly.empty:
        new_hourly.to_sql(
            name="clean_hourly", con=engine, if_exists="append",
            index=False, chunksize=1000, method="multi"
        )
    if not new_daily.empty:
        new_daily.to_sql(
            name="clean_daily", con=engine, if_exists="append",
            index=False, chunksize=500, method="multi"
        )


# ─────────────────────────────────────────────
# 5. MAIN
# ─────────────────────────────────────────────

def main():
    log.info("=" * 55)
    log.info("BMKG Fatmawati — Pipeline dimulai")
    log.info(f"Waktu eksekusi : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 55)

    try:
        # Cleaning
        df_hourly, df_daily = run_cleaning(RAW_FILE_PATH)

        # Koneksi DB
        engine = get_engine()

        upload_incremental(df_hourly, df_daily, engine)

        log.info("=" * 55)
        log.info("Pipeline selesai — semua data berhasil diupload.")
        log.info("=" * 55)

    except FileNotFoundError:
        log.error(f"File tidak ditemukan: {RAW_FILE_PATH}")
        raise
    except EnvironmentError as e:
        log.error(str(e))
        raise
    except Exception as e:
        log.error(f"Pipeline gagal: {e}")
        raise


if __name__ == "__main__":
    main()
