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

## Tentang Proyek

Proyek ini membangun sistem pemantauan dan analisis cuaca berbasis web untuk Stasiun Meteorologi Kelas I Fatmawati Bengkulu (WMO ID: 96253). Sistem bekerja secara penuh otomatis: data pengamatan sinoptik (*SYNOP*) yang dientri oleh observer diproses setiap tengah malam, disimpan ke basis data cloud, dan ditampilkan secara langsung melalui dashboard interaktif yang dapat diakses dari peramban tanpa instalasi perangkat lunak apapun.

Seluruh pipeline mengacu pada standar internasional **WMO-No. 306 Manual on Codes** (WMO, 2019) dan **WMO-No. 8 Guide to Meteorological Instruments and Methods of Observation** (WMO, 2018), memastikan bahwa setiap tahap pengolahan data dapat dipertanggungjawabkan secara ilmiah.

---

## Arsitektur Sistem

```
RAW_SYNOP_REPORT.csv
        │
        ├─ BMKG_Fatmawati_Cleaning.ipynb   (eksplorasi & dokumentasi)
        │
        ├─ pipeline_db.py                  (dijalankan otomatis 00:00 WIB)
        │     ├─ Parsing timestamp UTC
        │     ├─ Dekode curah hujan (IR indicator + kode 8888)
        │     ├─ Interpolasi sirkular arah angin (Mardia & Jupp, 2000)
        │     ├─ Quality control — gross error check (Zahumenský, 2004)
        │     └─ Upload ke Supabase PostgreSQL
        │
        ├─ Supabase PostgreSQL
        │     ├─ Tabel: clean_hourly  (~22.000 baris)
        │     └─ Tabel: clean_daily   (~923 baris)
        │
        └─ dashboard.py                    (Streamlit — akses publik)
              ├─ Monitoring kondisi terkini
              ├─ Analisis time-series suhu, kelembaban, tekanan
              ├─ Curah hujan harian & bulanan
              ├─ Wind rose 16 sektor
              ├─ Tutupan awan & visibilitas
              └─ Klimatologi bulanan
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

Di panel sebelah kiri (*sidebar*), terdapat dua kolom tanggal — **Dari** dan **Hingga** — yang dapat diatur secara bebas sesuai kebutuhan analisis. Klik pada kolom tanggal untuk menampilkan kalender, pilih tanggal yang diinginkan, lalu dashboard akan memperbarui seluruh grafik secara otomatis.

Cakupan data yang tersedia: **Januari 2022 – Juli 2024** (923 hari pengamatan, resolusi per jam).

### Navigasi Antar Tab

Gunakan tab di bagian atas konten utama untuk berpindah antar topik analisis. Setiap tab menampilkan ringkasan statistik di baris atas, diikuti oleh grafik interaktif di bawahnya.

### Interaksi dengan Grafik

Seluruh grafik bersifat interaktif:

- **Zoom** — klik dan seret pada area grafik untuk memperbesar rentang waktu tertentu
- **Pan** — tahan *shift* lalu seret untuk menggeser tampilan
- **Tooltip** — arahkan kursor ke titik data untuk melihat nilai tepat pada tanggal dan jam tersebut
- **Sembunyikan/tampilkan seri** — klik nama variabel pada legenda grafik
- **Unduh gambar** — klik ikon kamera di pojok kanan atas grafik

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
<sub>Data: BMKG Stasiun Meteorologi Kelas I Fatmawati Bengkulu &nbsp;·&nbsp; Periode: Januari 2022 – Juli 2024 &nbsp;·&nbsp; Resolusi: Per Jam</sub>
</div>
