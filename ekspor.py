"""Ekspor laporan ke JSON, Excel, dan PDF."""
import io
import json
import re
import pandas as pd
from fpdf import FPDF


def ke_json(paket):
    return json.dumps(paket, indent=2, ensure_ascii=False)


def ke_excel(paket):
    penyangga = io.BytesIO()
    with pd.ExcelWriter(penyangga, engine="openpyxl") as penulis:
        pd.DataFrame(list(paket["parameter"].items()), columns=["Parameter", "Nilai"]).to_excel(
            penulis, sheet_name="Parameter", index=False)
        for kota, data in paket["prakiraan"].items():
            pd.DataFrame(data).to_excel(penulis, sheet_name=f"Cuaca {kota}"[:31], index=False)
            pd.DataFrame(paket["rencana"][kota]).to_excel(penulis, sheet_name=f"Rencana {kota}"[:31], index=False)
        if paket["peringkat_kota"]:
            pd.DataFrame(paket["peringkat_kota"]).to_excel(penulis, sheet_name="Peringkat Kota", index=False)
        pd.DataFrame({"Saran AI": [paket.get("saran_ai") or "(belum dibuat)"]}).to_excel(
            penulis, sheet_name="Saran AI", index=False)
    return penyangga.getvalue()


def _bersihkan(teks):
    teks = re.sub(r"[*#`]", "", str(teks))
    return teks.encode("latin-1", "replace").decode("latin-1")


def ke_pdf(paket):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Laporan Perencana Perjalanan & Aktivitas Berbasis Cuaca", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    for k, v in paket["parameter"].items():
        pdf.multi_cell(0, 6, _bersihkan(f"{k}: {v}"), new_x="LMARGIN", new_y="NEXT")

    for kota, rencana in paket["rencana"].items():
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _bersihkan(f"Rencana - {kota}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=9)
        for r in rencana:
            pdf.multi_cell(0, 5, _bersihkan(
                f"{r['tanggal']} | {r['kondisi']} | {r['aktivitas']} (skor {r['skor']}) | Bawa: {r['perlengkapan']}"),
                new_x="LMARGIN", new_y="NEXT")

    if paket["peringkat_kota"]:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Peringkat Destinasi", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=9)
        for i, p in enumerate(paket["peringkat_kota"], 1):
            pdf.multi_cell(0, 5, _bersihkan(
                f"{i}. {p['kota']} - skor {p['skor_rata']}, hujan {p['hujan_total_mm']} mm, hari terbaik {p['hari_terbaik']}"),
                new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Saran AI (Gemini)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(0, 6, _bersihkan(paket.get("saran_ai") or "(belum dibuat)"), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
