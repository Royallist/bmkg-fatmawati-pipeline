<div align="center">

# Automated Weather Monitoring & Analysis Dashboard
### BMKG Stasiun Meteorologi Kelas I Fatmawati Bengkulu

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white)
![WMO Standard](https://img.shields.io/badge/Standard-WMO--No.306-0068A8?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-gray?style=flat-square)

**Live Dashboard →** [bmkg-fatmawati.streamlit.app](https://bmkg-fatmawati-pipeline-miiineeqwfes3vh6xgz3mk.streamlit.app)

</div>

---

## Ringkasan Proyek

Repositori ini berisi *end-to-end data pipeline* dan *dashboard* analitik untuk mengotomatisasi pengolahan data observasi cuaca sinoptik (SYNOP) di BMKG Stasiun Meteorologi Kelas I Fatmawati Bengkulu (WMO ID: 96253). 

Proyek ini dirancang untuk menggantikan proses rekapitulasi data manual, memastikan kualitas data (*Quality Control*) secara sistematis, dan mendemokratisasi akses data cuaca historis (observasi per jam) melalui antarmuka web interaktif. Seluruh logika pemrosesan data, termasuk penanganan anomali, mengacu pada standar instrumen dan observasi WMO (World Meteorological Organization).

---

## Technical Highlights & Metodologi

Pemrosesan data mentah observasi menjadi data siap analisis (*clean data*) melibatkan beberapa penanganan metrik cuaca yang kompleks:

* **Circular Interpolation untuk Arah Angin:** Menghindari bias matematis pada data sirkular (0°-360°) menggunakan metode Mardia & Jupp (2000) saat melakukan imputasi *missing values* pada data arah angin.
* **WMO Rainfall Decoding:** Mendekode indikator curah hujan berdasarkan *Manual on Codes* WMO-No. 306 (menerjemahkan IR indicator dan *omitted codes* seperti `8888` menjadi data numerik valid atau *NaN*).
* **Automated Quality Control (QC):** Mengimplementasikan *Gross Error Check* (Zahumenský, 2004) dengan batasan threshold logis untuk 11 variabel meteorologi. Nilai di luar kewajaran secara otomatis di-flag sebagai `SUSPECT` dan dipisahkan dari perhitungan *daily aggregation*.
* **Pipeline Automation:** Skrip ETL (`pipeline_db.py`) diorkestrasi menggunakan GitHub Actions untuk berjalan setiap pukul 00:00 WIB, memproses data harian terbaru, dan melakukan upsert ke database PostgreSQL.

---

## Arsitektur Sistem

```
[Data Source] RAW_SYNOP_REPORT.csv 
      │
      ├─► [ETL Script] pipeline_db.py (GitHub Actions - Cron 00:00)
      │      ├─ Data Parsing & Imputation
      │      ├─ Rainfall Decoding & Circular Interpolation
      │      └─ Gross Error Check (QC)
      │
      ├─► [Data Warehouse] Supabase PostgreSQL
      │      ├─ clean_hourly  (observasi per jam)
      │      └─ clean_daily   (Agregasi harian)
      │
      └─► [Frontend] dashboard.py (Streamlit)
             └─ Visualisasi data historis, klimatologi bulanan, & wind rose
```

---

## Fitur Dashboard

| Tab | Konten |
|---|---|
| Suhu & Kelembaban | Time series Tmax/Tmin/Tavg, kelembaban relatif, heatmap per jam |
| Curah Hujan | Intensitas harian, akumulasi bulanan, tabel kejadian ekstrem |
| Angin | Wind rose 16 sektor × 5 kelas kecepatan, tren kecepatan harian |
| Awan & Visibilitas | Tutupan awan (oktas), jarak pandang, lama penyinaran matahari |
| Tekanan Udara | QFF vs QFE, heatmap tekanan per jam |
| Klimatologi | Rata-rata bulanan multi-variabel, statistik deskriptif periode |

---

## Panduan Penggunaan Dashboard

Dashboard dapat diakses langsung melalui tautan berikut tanpa memerlukan akun atau instalasi:

**[bmkg-fatmawati-pipeline-miiineeqwfes3vh6xgz3mk.streamlit.app](https://bmkg-fatmawati-pipeline-miiineeqwfes3vh6xgz3mk.streamlit.app)**

### Memilih Periode Analisis

Di panel sebelah kiri (*sidebar*), terdapat dua kolom tanggal **Dari** dan **Hingga** yang dapat diatur secara bebas sesuai kebutuhan analisis. Klik pada kolom tanggal untuk menampilkan kalender, pilih tanggal yang diinginkan, lalu dashboard akan memperbarui seluruh grafik secara otomatis.

Cakupan data yang tersedia: **Januari 2022 – Juli 2024** (923 hari pengamatan, observasi per jam).

### Navigasi Antar Tab

Gunakan tab di bagian atas konten utama untuk berpindah antar topik analisis. Setiap tab menampilkan ringkasan statistik di baris atas, diikuti oleh grafik interaktif di bawahnya.

### Interaksi dengan Grafik

Seluruh grafik bersifat interaktif:

- **Zoom**: klik dan seret pada area grafik untuk memperbesar rentang waktu tertentu
- **Pan**: tahan *shift* lalu seret untuk menggeser tampilan
- **Tooltip**: arahkan kursor ke titik data untuk melihat nilai tepat pada tanggal dan jam tersebut
- **Sembunyikan/tampilkan seri**: klik nama variabel pada legenda grafik
- **Unduh gambar**: klik ikon kamera di pojok kanan atas grafik

### Pembaruan Data

Data diperbarui secara otomatis setiap pukul **00:00 WIB**. Tombol **Refresh data** di sidebar dapat digunakan untuk memuat ulang data terbaru tanpa harus me-*reload* halaman secara manual.

---

## Struktur Repositori

```
bmkg-fatmawati-pipeline/
├── BMKG_Fatmawati_Cleaning.ipynb   Notebook eksplorasi & dokumentasi ilmiah
├── pipeline_db.py                  Script pipeline otomasi
├── dashboard.py                    Aplikasi Streamlit
├── requirements.txt                Dependensi Python
├── .env.example                    Template konfigurasi lokal
├── .gitignore
├── README.md
└── .github/
    └── workflows/
        └── nightly_pipeline.yml    GitHub Actions — jadwal 00:00 WIB
```

---

## Dependensi

| Library | Versi | Fungsi |
|---|---|---|
| Python | ≥ 3.10 | — |
| pandas | ≥ 2.0 | Manipulasi data tabular |
| numpy | ≥ 1.24 | Komputasi numerik |
| plotly | ≥ 5.18 | Visualisasi interaktif |
| streamlit | ≥ 1.35 | Framework dashboard |
| sqlalchemy | ≥ 2.0 | Abstraksi koneksi database |
| psycopg2-binary | ≥ 2.9 | Driver PostgreSQL |
| python-dotenv | ≥ 1.0 | Manajemen environment variables |

---

## Referensi

Mardia, K. V., & Jupp, P. E. (2000). *Directional statistics*. John Wiley & Sons. https://doi.org/10.1002/9780470316979

Moritz, S., & Bartz-Beielstein, T. (2017). imputeTS: Time series missing value imputation in R. *The R Journal*, *9*(1), 207–218. https://doi.org/10.32614/RJ-2017-009

Wickham, H. (2014). Tidy data. *Journal of Statistical Software*, *59*(10), 1–23. https://doi.org/10.18637/jss.v059.i10

WMO. (2018). *Guide to meteorological instruments and methods of observation* (WMO-No. 8). World Meteorological Organization.

WMO. (2019). *Manual on codes — Volume I.1* (WMO-No. 306). World Meteorological Organization.

Zahumenský, I. (2004). *Guidelines on quality control procedures for data from automatic weather stations*. WMO-CIMO.

---

<div align="center">
<sub>Data: BMKG Stasiun Meteorologi Kelas I Fatmawati Bengkulu &nbsp;·&nbsp; Periode: Januari 2022 – Juli 2024 &nbsp;·&nbsp; observasi: Per Jam</sub>
</div>
