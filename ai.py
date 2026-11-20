"""Integrasi Gemini API: data hasil olahan aplikasi dikirim sebagai konteks."""
import requests

MODEL_BAWAAN = "gemini-flash-latest"


class GagalAI(Exception):
    pass


def susun_prompt(aktivitas, rencana_per_kota, peringkat):
    baris = [
        "Kamu adalah asisten perencana perjalanan dan aktivitas berbasis cuaca.",
        f"Aktivitas yang diminati pengguna: {', '.join(aktivitas)}.",
        "Berikut data hasil olahan aplikasi (skor 0-100, makin tinggi makin cocok):",
    ]
    for kota, rencana in rencana_per_kota.items():
        baris.append(f"\nKota: {kota}")
        for r in rencana:
            baris.append(f"- {r['tanggal']}: {r['kondisi']}, aktivitas terbaik {r['aktivitas']} "
                         f"(skor {r['skor']}), perlengkapan: {r['perlengkapan']}")
    if len(peringkat) > 1:
        baris.append("\nPeringkat destinasi:")
        for i, p in enumerate(peringkat, 1):
            baris.append(f"{i}. {p['kota']} - skor rata-rata {p['skor_rata']}, "
                         f"hujan total {p['hujan_total_mm']} mm, hari terbaik {p['hari_terbaik']}")
    baris.append(
        "\nTugasmu, dalam bahasa Indonesia yang sederhana dan ringkas:\n"
        "1. Ringkasan cuaca secara umum.\n"
        "2. Rekomendasi rencana perjalanan/aktivitas terbaik (sebutkan hari dan alasannya)"
        + (", termasuk destinasi terbaik dari perbandingan kota.\n" if len(peringkat) > 1 else ".\n")
        + "3. Saran pakaian dan barang bawaan.\n"
        "4. Peringatan cuaca atau risiko yang perlu diwaspadai.\n"
        "Gunakan hanya data di atas, jangan mengarang angka."
    )
    return "\n".join(baris)


def minta_saran(prompt, kunci_api, model=MODEL_BAWAAN):
    if not kunci_api:
        raise GagalAI("API key Gemini belum diatur.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        respons = requests.post(
            url,
            headers={"x-goog-api-key": kunci_api, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60,
        )
    except requests.exceptions.RequestException:
        raise GagalAI("Tidak dapat terhubung ke Gemini API.")
    if respons.status_code == 429:
        raise GagalAI("Batas permintaan Gemini tercapai. Coba lagi beberapa saat.")
    if respons.status_code in (400, 401, 403):
        raise GagalAI("API key Gemini tidak valid atau tidak punya akses.")
    if respons.status_code != 200:
        raise GagalAI(f"Gemini mengembalikan kesalahan {respons.status_code}.")
    try:
        return respons.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, ValueError):
        raise GagalAI("Respons Gemini kosong atau tidak dapat dibaca.")
