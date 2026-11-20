# Perencana Perjalanan & Aktivitas Berbasis Cuaca

Aplikasi Streamlit untuk Project Besar Praktikum Struktur Data. Pengguna memasukkan kota (satu untuk rencana harian, beberapa untuk perbandingan destinasi), aplikasi mengambil prakiraan cuaca, memberi skor dan peringkat, menampilkan grafik, lalu Gemini menyusun saran dari data hasil olahan.

## Menjalankan
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # isi GEMINI_API_KEY
streamlit run app.py
```
API key juga bisa lewat environment variable `GEMINI_API_KEY` atau diketik di sidebar. Jangan commit `secrets.toml`.

## Pemenuhan requirements
| Requirement | Penerapan |
|---|---|
| Data input | Teks nama kota, unggah CSV (`kota_contoh.csv`), pilihan aktivitas dan jumlah hari |
| Data eksternal | Open-Meteo Geocoding dan Forecast API (`cuaca.py`) |
| Struktur data | Dictionary (cache TTL, counter kondisi), Stack (riwayat + tombol Kembali), list of dict |
| Algoritma | Merge sort (`urut_gabung`), linear search (`cari_linear`), skor kecocokan |
| Visualisasi | Garis suhu, batang curah hujan, batang horizontal peringkat kota (Plotly) |
| Ekspor | PDF, Excel, JSON (`ekspor.py`) |
| AI | Gemini API (`ai.py`) menerima skor, rencana, dan peringkat sebagai konteks |

## Struktur
`app.py` (UI) · `cuaca.py` (API + cache) · `logika.py` (struktur data/algoritma) · `ai.py` · `ekspor.py`
