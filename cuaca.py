"""Pengambilan data eksternal dari Open-Meteo (geocoding + prakiraan) dengan cache dictionary."""
import time
import requests

URL_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
URL_PRAKIRAAN = "https://api.open-meteo.com/v1/forecast"
BATAS_WAKTU = 15          # detik, timeout request
MASA_CACHE = 30 * 60      # detik, cache berlaku 30 menit

# Dictionary (hash table) sebagai cache: kunci -> (waktu_simpan, nilai)
_cache = {}


class GagalAmbilData(Exception):
    """Dilempar jika data dari API gagal diambil."""


def _ambil_cache(kunci):
    isi = _cache.get(kunci)
    if isi and time.time() - isi[0] < MASA_CACHE:
        return isi[1]
    return None


def _simpan_cache(kunci, nilai):
    _cache[kunci] = (time.time(), nilai)
    return nilai


def _get_json(url, parameter):
    try:
        respons = requests.get(url, params=parameter, timeout=BATAS_WAKTU)
    except requests.exceptions.Timeout:
        raise GagalAmbilData("Koneksi ke Open-Meteo melebihi batas waktu. Coba lagi.")
    except requests.exceptions.RequestException:
        raise GagalAmbilData("Tidak dapat terhubung ke Open-Meteo. Periksa koneksi internet.")
    if respons.status_code == 429:
        raise GagalAmbilData("Batas permintaan Open-Meteo tercapai. Tunggu beberapa saat.")
    if respons.status_code != 200:
        raise GagalAmbilData(f"Open-Meteo mengembalikan kesalahan {respons.status_code}.")
    return respons.json()


def cari_koordinat(nama_kota):
    """Mengubah nama kota menjadi koordinat (geocoding). Hasil disimpan di cache."""
    kunci = ("geo", nama_kota.strip().lower())
    tersimpan = _ambil_cache(kunci)
    if tersimpan:
        return tersimpan
    data = _get_json(URL_GEOCODING, {"name": nama_kota, "count": 1, "language": "id"})
    hasil = data.get("results")
    if not hasil:
        raise GagalAmbilData(f"Kota '{nama_kota}' tidak ditemukan.")
    h = hasil[0]
    lokasi = {
        "nama": h.get("name", nama_kota),
        "wilayah": h.get("admin1", ""),
        "negara": h.get("country", ""),
        "lat": h["latitude"],
        "lon": h["longitude"],
    }
    return _simpan_cache(kunci, lokasi)


def kode_ke_kondisi(kode):
    """Mengubah kode cuaca WMO menjadi (teks kondisi, kategori)."""
    if kode in (0, 1):
        return "Cerah", "Cerah"
    if kode in (2, 3):
        return "Berawan", "Berawan"
    if kode in (45, 48):
        return "Berkabut", "Berkabut"
    if kode in (51, 53, 55, 56, 57):
        return "Gerimis", "Hujan"
    if kode in (61, 63, 65, 66, 67, 80, 81, 82):
        return "Hujan", "Hujan"
    if kode in (95, 96, 99):
        return "Badai petir", "Badai"
    if kode in (71, 73, 75, 77, 85, 86):
        return "Salju", "Salju"
    return "Tidak diketahui", "Lainnya"


def ambil_prakiraan(lokasi, jumlah_hari):
    """Mengambil prakiraan harian. Mengembalikan list of dictionary (satu dict per hari)."""
    kunci = ("cuaca", round(lokasi["lat"], 2), round(lokasi["lon"], 2), jumlah_hari)
    tersimpan = _ambil_cache(kunci)
    if tersimpan:
        return tersimpan
    data = _get_json(URL_PRAKIRAAN, {
        "latitude": lokasi["lat"],
        "longitude": lokasi["lon"],
        "daily": ",".join([
            "weather_code", "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "precipitation_probability_max",
            "wind_speed_10m_max", "uv_index_max",
        ]),
        "timezone": "auto",
        "forecast_days": jumlah_hari,
    })
    harian = data.get("daily")
    if not harian or not harian.get("time"):
        raise GagalAmbilData("Data prakiraan kosong untuk lokasi ini.")
    daftar = []
    for i, tanggal in enumerate(harian["time"]):
        kode = harian["weather_code"][i]
        kondisi, kategori = kode_ke_kondisi(kode)
        daftar.append({
            "tanggal": tanggal,
            "kondisi": kondisi,
            "kategori": kategori,
            "suhu_maks": harian["temperature_2m_max"][i],
            "suhu_min": harian["temperature_2m_min"][i],
            "hujan_mm": harian["precipitation_sum"][i] or 0,
            "peluang_hujan": harian["precipitation_probability_max"][i] or 0,
            "angin_kmj": harian["wind_speed_10m_max"][i] or 0,
            "uv": harian["uv_index_max"][i] or 0,
        })
    return _simpan_cache(kunci, daftar)
