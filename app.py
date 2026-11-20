"""Perencana Perjalanan & Aktivitas Berbasis Cuaca - Streamlit."""
import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ai
import cuaca
import ekspor
import logika

st.set_page_config(page_title="Perencana Cuaca", page_icon="🌤️", layout="wide")

# ---------- State ----------
if "riwayat" not in st.session_state:
    st.session_state.riwayat = logika.Tumpukan()   # Stack riwayat pencarian
if "hasil" not in st.session_state:
    st.session_state.hasil = None
if "saran_ai" not in st.session_state:
    st.session_state.saran_ai = None
if "input_kota" not in st.session_state:
    st.session_state.input_kota = "Yogyakarta"


def ambil_kunci_api():
    try:
        kunci = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        kunci = None
    return kunci or os.environ.get("GEMINI_API_KEY") or st.session_state.get("kunci_manual")


def ambil_model():
    try:
        model = st.secrets.get("GEMINI_MODEL")
    except Exception:
        model = None
    return model or os.environ.get("GEMINI_MODEL") or ai.MODEL_BAWAAN


def kembali():
    """Callback tombol Kembali: pop pencarian saat ini lalu muat pencarian sebelumnya."""
    riwayat = st.session_state.riwayat
    riwayat.keluarkan()
    sebelumnya = riwayat.intip()
    if sebelumnya:
        st.session_state.input_kota = "\n".join(sebelumnya["kota"])
        st.session_state.muat_ulang = sebelumnya


def jalankan_pencarian(daftar_kota, jumlah_hari, aktivitas, dorong=True):
    hasil_prakiraan, lokasi_kota, kesalahan = {}, {}, []
    for nama in daftar_kota:
        try:
            lokasi = cuaca.cari_koordinat(nama)
            label = f"{lokasi['nama']}" + (f", {lokasi['negara']}" if lokasi["negara"] else "")
            hasil_prakiraan[label] = cuaca.ambil_prakiraan(lokasi, jumlah_hari)
            lokasi_kota[label] = lokasi
        except cuaca.GagalAmbilData as e:
            kesalahan.append(f"{nama}: {e}")
    for pesan in kesalahan:
        st.warning(pesan)
    if not hasil_prakiraan:
        st.session_state.hasil = None
        return
    rencana = {k: logika.buat_rencana(p, aktivitas) for k, p in hasil_prakiraan.items()}
    peringkat = logika.peringkat_kota(hasil_prakiraan, aktivitas) if len(hasil_prakiraan) > 1 else []
    st.session_state.hasil = {
        "prakiraan": hasil_prakiraan, "rencana": rencana, "peringkat": peringkat,
        "aktivitas": aktivitas, "hari": jumlah_hari,
    }
    st.session_state.saran_ai = None
    if dorong:
        st.session_state.riwayat.dorong({"kota": list(daftar_kota), "hari": jumlah_hari, "aktivitas": aktivitas})


# ---------- Sidebar ----------
with st.sidebar:
    st.header("Pengaturan")
    aktivitas = st.multiselect("Aktivitas yang diminati", list(logika.PROFIL_AKTIVITAS),
                               default=["Olahraga luar ruang", "Wisata kota & kuliner"])
    jumlah_hari = st.slider("Jumlah hari prakiraan", 3, 14, 7)

    st.subheader("Riwayat pencarian")
    semua = st.session_state.riwayat.semua()
    if semua:
        for item in reversed(semua):
            st.caption("• " + ", ".join(item["kota"]))
        st.button("⬅ Kembali ke pencarian sebelumnya", on_click=kembali,
                  disabled=st.session_state.riwayat.ukuran() < 2)
    else:
        st.caption("Belum ada riwayat.")

    if not ambil_kunci_api():
        st.subheader("API key Gemini")
        st.text_input("Masukkan API key (hanya untuk sesi ini)", type="password", key="kunci_manual")

# ---------- Input ----------
st.title("🌤️ Perencana Perjalanan & Aktivitas Berbasis Cuaca")
st.write("Masukkan satu kota untuk rencana harian, atau beberapa kota untuk membandingkan destinasi terbaik.")

kolom_kiri, kolom_kanan = st.columns([2, 1])
with kolom_kiri:
    st.text_area("Nama kota (satu kota per baris)", key="input_kota", height=110)
with kolom_kanan:
    berkas = st.file_uploader("Atau unggah CSV daftar kota (kolom: kota)", type="csv")

daftar_kota = [k.strip() for k in st.session_state.input_kota.splitlines() if k.strip()]
if berkas is not None:
    try:
        tabel = pd.read_csv(berkas)
        kolom = next((c for c in tabel.columns if c.strip().lower() == "kota"), None)
        if kolom is None:
            st.error("File CSV harus memiliki kolom bernama 'kota'.")
        else:
            kota_csv = [str(k).strip() for k in tabel[kolom].dropna()]
            kata = st.text_input("Cari kota di daftar CSV (opsional)")
            terfilter = logika.cari_linear(kota_csv, kata)    # Linear search
            terpilih = st.multiselect("Pilih kota dari CSV", terfilter, default=terfilter[:3])
            daftar_kota = list(dict.fromkeys(daftar_kota + terpilih))
    except Exception:
        st.error("File CSV tidak dapat dibaca.")

if st.button("Lihat Rencana", type="primary"):
    if not daftar_kota:
        st.error("Masukkan minimal satu kota.")
    elif not aktivitas:
        st.error("Pilih minimal satu aktivitas di sidebar.")
    elif len(daftar_kota) > 5:
        st.error("Maksimal 5 kota agar tidak melebihi batas permintaan API.")
    else:
        with st.spinner("Mengambil data cuaca..."):
            jalankan_pencarian(daftar_kota, jumlah_hari, aktivitas)

if "muat_ulang" in st.session_state:
    pilihan = st.session_state.pop("muat_ulang")
    with st.spinner("Memuat pencarian sebelumnya..."):
        jalankan_pencarian(pilihan["kota"], pilihan["hari"], pilihan["aktivitas"], dorong=False)

# ---------- Hasil ----------
hasil = st.session_state.hasil
if not hasil:
    st.info("Hasil akan tampil di sini setelah Anda menekan Lihat Rencana.")
    st.stop()

prakiraan, rencana, peringkat = hasil["prakiraan"], hasil["rencana"], hasil["peringkat"]
nama_tab = ["Prakiraan & Grafik", "Rencana Perjalanan"]
if peringkat:
    nama_tab.append("Perbandingan Kota")
nama_tab += ["Saran AI", "Ekspor"]
tab = st.tabs(nama_tab)

with tab[0]:
    kota_dipilih = st.selectbox("Kota", list(prakiraan), key="kota_grafik")
    data = prakiraan[kota_dipilih]
    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True, width="stretch")
    k1, k2 = st.columns(2)
    with k1:   # Visualisasi 1: grafik garis suhu
        g1 = go.Figure()
        g1.add_trace(go.Scatter(x=df["tanggal"], y=df["suhu_maks"], name="Suhu maks (°C)", mode="lines+markers"))
        g1.add_trace(go.Scatter(x=df["tanggal"], y=df["suhu_min"], name="Suhu min (°C)", mode="lines+markers"))
        g1.update_layout(title="Suhu harian", yaxis_title="°C", margin=dict(t=40, b=10))
        st.plotly_chart(g1, width="stretch")
    with k2:   # Visualisasi 2: grafik batang curah hujan
        g2 = go.Figure(go.Bar(x=df["tanggal"], y=df["hujan_mm"], name="Curah hujan (mm)"))
        g2.update_layout(title="Curah hujan harian", yaxis_title="mm", margin=dict(t=40, b=10))
        st.plotly_chart(g2, width="stretch")
    frek = logika.hitung_frekuensi(data)      # Dictionary counter
    st.caption("Jumlah hari per kondisi: " + ", ".join(f"{k} = {v}" for k, v in frek.items()))

with tab[1]:
    kota_r = st.selectbox("Kota", list(rencana), key="kota_rencana")
    df_r = pd.DataFrame(rencana[kota_r])
    st.dataframe(df_r, hide_index=True, width="stretch")
    terurut = logika.urut_gabung(rencana[kota_r], "skor", menurun=True)   # Merge sort
    st.subheader("Hari terbaik")
    for r in terurut[:3]:
        st.write(f"**{r['tanggal']}**: {r['aktivitas']} (skor {r['skor']}) – bawa: {r['perlengkapan']}")

idx = 2
if peringkat:
    with tab[idx]:
        df_p = pd.DataFrame(peringkat)
        st.dataframe(df_p, hide_index=True, width="stretch")
        # Visualisasi 3: batang horizontal peringkat kota
        urut = df_p.sort_values("skor_rata")
        g3 = go.Figure(go.Bar(x=urut["skor_rata"], y=urut["kota"], orientation="h"))
        g3.update_layout(title="Skor rata-rata kecocokan per kota", xaxis_title="Skor (0-100)", margin=dict(t=40, b=10))
        st.plotly_chart(g3, width="stretch")
        st.success(f"Destinasi terbaik: {peringkat[0]['kota']} (skor {peringkat[0]['skor_rata']}).")
    idx += 1

with tab[idx]:
    st.write("AI menerima data hasil olahan aplikasi (skor, rencana, peringkat) sebagai konteks.")
    if st.button("Minta Saran AI"):
        with st.spinner("Gemini menyusun saran..."):
            try:
                prompt = ai.susun_prompt(hasil["aktivitas"], rencana, peringkat)
                st.session_state.saran_ai = ai.minta_saran(prompt, ambil_kunci_api(), ambil_model())
            except ai.GagalAI as e:
                st.error(str(e))
    if st.session_state.saran_ai:
        st.markdown(st.session_state.saran_ai)
idx += 1

with tab[idx]:
    paket = {
        "dibuat": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "parameter": {
            "kota": ", ".join(prakiraan),
            "aktivitas": ", ".join(hasil["aktivitas"]),
            "jumlah_hari": hasil["hari"],
            "sumber_data": "Open-Meteo",
        },
        "prakiraan": prakiraan,
        "rencana": rencana,
        "peringkat_kota": peringkat,
        "saran_ai": st.session_state.saran_ai,
    }
    if not st.session_state.saran_ai:
        st.caption("Tip: buat Saran AI dulu agar masuk ke laporan.")
    e1, e2, e3 = st.columns(3)
    e1.download_button("Unduh PDF", ekspor.ke_pdf(paket), "laporan_cuaca.pdf", "application/pdf")
    e2.download_button("Unduh Excel", ekspor.ke_excel(paket), "laporan_cuaca.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    e3.download_button("Unduh JSON", ekspor.ke_json(paket), "laporan_cuaca.json", "application/json")
