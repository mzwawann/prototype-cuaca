"""Struktur data dan algoritma: Stack, Merge Sort, Linear Search, Dictionary (counter), skor aktivitas."""

# Profil kenyamanan tiap aktivitas
PROFIL_AKTIVITAS = {
    "Olahraga luar ruang":     {"suhu_ideal": (22, 30), "angin_maks": 30, "uv_maks": 8, "bobot_hujan": 1.0},
    "Wisata alam / hiking":    {"suhu_ideal": (20, 28), "angin_maks": 25, "uv_maks": 9, "bobot_hujan": 1.2},
    "Piknik / santai di taman": {"suhu_ideal": (24, 31), "angin_maks": 20, "uv_maks": 8, "bobot_hujan": 1.1},
    "Wisata kota & kuliner":   {"suhu_ideal": (22, 34), "angin_maks": 40, "uv_maks": 10, "bobot_hujan": 0.5},
    "Fotografi outdoor":       {"suhu_ideal": (20, 32), "angin_maks": 30, "uv_maks": 10, "bobot_hujan": 0.8},
}
BATAS_ALTERNATIF = 45  # di bawah skor ini, sarankan aktivitas dalam ruangan


# ---------- Stack (riwayat pencarian) ----------
class Tumpukan:
    """Stack: LIFO. Dipakai untuk riwayat pencarian dan tombol Kembali."""

    def __init__(self):
        self._isi = []

    def dorong(self, item):
        self._isi.append(item)

    def keluarkan(self):
        return self._isi.pop() if self._isi else None

    def intip(self):
        return self._isi[-1] if self._isi else None

    def ukuran(self):
        return len(self._isi)

    def semua(self):
        return list(self._isi)


# ---------- Sorting: Merge Sort ----------
def urut_gabung(daftar, kunci, menurun=True):
    """Merge sort pada list of dictionary berdasarkan nilai dari `kunci`."""
    if len(daftar) <= 1:
        return list(daftar)
    tengah = len(daftar) // 2
    kiri = urut_gabung(daftar[:tengah], kunci, menurun)
    kanan = urut_gabung(daftar[tengah:], kunci, menurun)
    hasil, i, j = [], 0, 0
    while i < len(kiri) and j < len(kanan):
        a, b = kiri[i][kunci], kanan[j][kunci]
        ambil_kiri = a >= b if menurun else a <= b
        if ambil_kiri:
            hasil.append(kiri[i]); i += 1
        else:
            hasil.append(kanan[j]); j += 1
    hasil.extend(kiri[i:])
    hasil.extend(kanan[j:])
    return hasil


# ---------- Searching: Linear Search ----------
def cari_linear(daftar_teks, kata_kunci):
    """Mengembalikan semua item yang mengandung kata kunci (tidak peka huruf besar/kecil)."""
    kata = kata_kunci.strip().lower()
    if not kata:
        return list(daftar_teks)
    hasil = []
    for item in daftar_teks:
        if kata in item.lower():
            hasil.append(item)
    return hasil


# ---------- Dictionary sebagai counter ----------
def hitung_frekuensi(prakiraan, kunci="kategori"):
    frekuensi = {}
    for hari in prakiraan:
        frekuensi[hari[kunci]] = frekuensi.get(hari[kunci], 0) + 1
    return frekuensi


# ---------- Skor kecocokan ----------
def hitung_skor(hari, profil):
    """Skor 0-100: semakin tinggi semakin cocok untuk aktivitas tersebut."""
    skor = 100.0
    rendah, tinggi = profil["suhu_ideal"]
    if hari["suhu_maks"] > tinggi:
        skor -= (hari["suhu_maks"] - tinggi) * 4
    if hari["suhu_min"] < rendah - 5:
        skor -= (rendah - 5 - hari["suhu_min"]) * 3
    skor -= profil["bobot_hujan"] * (0.45 * hari["peluang_hujan"] + 2.5 * min(hari["hujan_mm"], 20))
    if hari["angin_kmj"] > profil["angin_maks"]:
        skor -= (hari["angin_kmj"] - profil["angin_maks"]) * 1.2
    if hari["uv"] > profil["uv_maks"]:
        skor -= (hari["uv"] - profil["uv_maks"]) * 5
    if hari.get("kategori") == "Badai":
        skor -= 40   # cuaca ekstrem
    return round(max(0.0, min(100.0, skor)), 1)


def label_skor(skor):
    if skor >= 75:
        return "Sangat cocok"
    if skor >= 55:
        return "Cukup cocok"
    if skor >= BATAS_ALTERNATIF:
        return "Kurang cocok"
    return "Tidak disarankan"


def daftar_perlengkapan(hari):
    barang = []
    if hari["peluang_hujan"] >= 50 or hari["hujan_mm"] >= 5:
        barang.append("payung/jas hujan")
    if hari["uv"] >= 6:
        barang.append("tabir surya & topi")
    if hari["suhu_maks"] >= 33:
        barang.append("air minum ekstra")
    if hari["suhu_min"] <= 18:
        barang.append("jaket")
    if hari["angin_kmj"] >= 30:
        barang.append("jaket tahan angin")
    return barang or ["perlengkapan standar"]


def buat_rencana(prakiraan, aktivitas_terpilih):
    """Rencana harian: pilih aktivitas dengan skor tertinggi pada tiap hari."""
    rencana = []
    for hari in prakiraan:
        skor_tiap = {nama: hitung_skor(hari, PROFIL_AKTIVITAS[nama]) for nama in aktivitas_terpilih}
        terbaik, skor_terbaik = None, -1
        for nama, skor in skor_tiap.items():
            if skor > skor_terbaik:
                terbaik, skor_terbaik = nama, skor
        if skor_terbaik < BATAS_ALTERNATIF:
            aktivitas = "Aktivitas dalam ruangan (museum, kafe, pusat belanja)"
            catatan = "Cuaca kurang mendukung kegiatan luar ruang."
        else:
            aktivitas = terbaik
            catatan = label_skor(skor_terbaik)
        rencana.append({
            "tanggal": hari["tanggal"],
            "kondisi": hari["kondisi"],
            "aktivitas": aktivitas,
            "skor": skor_terbaik,
            "catatan": catatan,
            "perlengkapan": ", ".join(daftar_perlengkapan(hari)),
        })
    return rencana


def peringkat_kota(hasil_prakiraan, aktivitas_terpilih):
    """Peringkat destinasi: rata-rata skor terbaik harian tiap kota, diurutkan dengan merge sort."""
    daftar = []
    for kota, prakiraan in hasil_prakiraan.items():
        skor_harian = []
        for hari in prakiraan:
            skor_harian.append(max(hitung_skor(hari, PROFIL_AKTIVITAS[a]) for a in aktivitas_terpilih))
        rata = sum(skor_harian) / len(skor_harian)
        hari_terbaik = prakiraan[skor_harian.index(max(skor_harian))]["tanggal"]
        daftar.append({
            "kota": kota,
            "skor_rata": round(rata, 1),
            "hari_terbaik": hari_terbaik,
            "hujan_total_mm": round(sum(h["hujan_mm"] for h in prakiraan), 1),
            "suhu_rata": round(sum((h["suhu_maks"] + h["suhu_min"]) / 2 for h in prakiraan) / len(prakiraan), 1),
        })
    return urut_gabung(daftar, "skor_rata", menurun=True)
