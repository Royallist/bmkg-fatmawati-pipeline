<div align="center">

# Automated Weather Data Pipeline
### BMKG Stasiun Meteorologi Kelas I Fatmawati Bengkulu

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=flat-square&logo=pandas&logoColor=white)
![WMO Standard](https://img.shields.io/badge/Standard-WMO--No.306-0068A8?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Google%20Colab-F9AB00?style=flat-square&logo=google-colab&logoColor=white)

</div>

---

## Latar Belakang

Stasiun Meteorologi Kelas I Fatmawati Bengkulu (WMO ID: 96253) melaksanakan pengamatan sinoptik permukaan (*surface synoptic observation*) secara rutin setiap jam, menghasilkan data dalam format laporan SYNOP sesuai standar **WMO-No. 306 Manual on Codes**. Data ini mencakup lebih dari 22.000 rekaman observasi per jam dengan 57 variabel meteorologi, mulai dari suhu dan kelembaban hingga jenis awan dan kode cuaca sekarang.

Namun, data mentah SYNOP memiliki karakteristik pengkodean yang kompleks dan tidak dapat langsung digunakan untuk analisis atau visualisasi. Beberapa di antaranya adalah: nilai curah hujan yang bergantung pada indikator IR, kode *trace* (8888) yang bukan merupakan nilai nol, dan variabel harian yang hanya dicatat sekali per hari namun tampak seperti *missing data* sebesar 95,8%. Tanpa penanganan yang tepat, kesalahan interpretasi pada variabel-variabel ini dapat menghasilkan analisis yang tidak valid secara ilmiah.

Proyek ini membangun sebuah **pipeline data cleaning otomatis** yang mengubah data SYNOP mentah menjadi dua tabel terstruktur yang siap digunakan untuk analisis klimatologi dan *dashboard* pemantauan cuaca.

## Tujuan

Pipeline ini dirancang untuk memenuhi kebutuhan analisis cuaca operasional di Stasiun Fatmawati Bengkulu dengan menghasilkan:

1. **`clean_hourly.csv`** — Dataset per jam yang telah didekode, divalidasi secara fisika, dan diberi nama variabel yang deskriptif; digunakan untuk analisis pola harian dan time-series cuaca.
2. **`clean_daily.csv`** — Agregasi harian yang menggabungkan statistik per jam dengan variabel instrumen harian (suhu maksimum/minimum termometer, lama penyinaran, dan curah hujan ombrometer); digunakan untuk analisis klimatologi jangka panjang dan visualisasi tren musiman.

## Pengguna

| Pengguna | Penggunaan |
|---|---|
| **Prakirawan / Analis BMKG** | Sumber data untuk analisis klimatologi dan pembuatan laporan cuaca berkala |
| **Peneliti meteorologi** | Dataset terstruktur untuk penelitian iklim wilayah Bengkulu |
| **Dashboard operator** | Input otomatis untuk *dashboard* pemantauan kondisi cuaca stasiun |

## Alur Pipeline

```
RAW_SYNOP_REPORT.csv  (22.144 baris × 57 kolom)
        │
        ├─ Parse timestamp (UTC string → datetime object)
        ├─ Dekode curah hujan  (IR indicator + kode 8888 → mm / NaN)
        ├─ Interpolasi angin   (metode sirkular — Mardia & Jupp, 2000)
        ├─ Interpolasi linear  (visibility, cloud base — missing < 2%)
        ├─ Quality Control     (gross error check — WMO, Zahumenský 2004)
        ├─ Seleksi & rename kolom
        │
        ├──► clean_hourly.csv  (~22.144 baris × 27 kolom)
        └──► clean_daily.csv   (~923 baris   × 22 kolom)
```

## Struktur Repositori

```
├── BMKG_Fatmawati_Cleaning.ipynb   # Pipeline utama (Google Colab)
├── data/
│   ├── raw/
│   │   └── RAW_SYNOP_REPORT.csv    # Data mentah SYNOP (tidak di-commit jika besar)
│   └── output/
│       ├── clean_hourly.csv
│       └── clean_daily.csv
└── README.md
```

## Cara Penggunaan

1. Upload `RAW_SYNOP_REPORT.csv` ke Google Drive, misalnya di `MyDrive/BMKG/`
2. Buka `BMKG_Fatmawati_Cleaning.ipynb` di Google Colab
3. Sesuaikan variabel `RAW_FILE_PATH` dan `OUTPUT_DIR` pada **§2 Konfigurasi Lingkungan**
4. Jalankan seluruh notebook: **Runtime → Run all**

Output tersimpan otomatis ke folder yang dikonfigurasi di Google Drive.

## Dependensi

| Library | Versi minimum | Keterangan |
|---|---|---|
| Python | 3.10 | — |
| pandas | 2.0 | Manipulasi data tabular |
| numpy | 1.24 | Komputasi numerik dan trigonometri |
| openpyxl | 3.1 | Opsional — ekspor ke Excel |

Seluruh dependensi tersedia secara default di lingkungan Google Colab.

## Referensi Standar

- WMO. (2019). *Manual on codes — Volume I.1* (WMO-No. 306). World Meteorological Organization.
- WMO. (2018). *Guide to meteorological instruments and methods of observation* (WMO-No. 8). World Meteorological Organization.
- Mardia, K. V., & Jupp, P. E. (2000). *Directional statistics*. John Wiley & Sons.
- Zahumenský, I. (2004). *Guidelines on quality control procedures for data from automatic weather stations*. WMO-CIMO.

---

<div align="center">
<sub>Data: BMKG Stasiun Meteorologi Kelas I Fatmawati Bengkulu · Periode: Januari 2022 – Juli 2024</sub>
</div>
