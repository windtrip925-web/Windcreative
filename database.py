import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "data", "windcreat.db")


def jalankan(sql, parameter=(), ambil=False):
    """Buka database, jalankan perintah SQL, lalu tutup lagi."""
    koneksi = sqlite3.connect(DB_PATH)
    koneksi.row_factory = sqlite3.Row
    try:
        hasil = koneksi.execute(sql, parameter)
        data = [dict(baris) for baris in hasil.fetchall()] if ambil else None
        koneksi.commit()
        return data
    finally:
        koneksi.close()


def siapkan_db():
    jalankan("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teks TEXT NOT NULL,
            tokoh TEXT NOT NULL,
            sumber TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'belum diverifikasi',
            dibuat TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)


def boleh_tayang(quote):
    """Aturan utama: harus ada sumber DAN sudah terverifikasi."""
    return quote["sumber"].strip() != "" and quote["status"] == "terverifikasi"


def tambah_quote(teks, tokoh, sumber):
    jalankan(
        "INSERT INTO quotes (teks, tokoh, sumber) VALUES (?, ?, ?)",
        (teks.strip(), tokoh.strip(), sumber.strip()),
    )


def daftar_quote():
    data = jalankan("SELECT * FROM quotes ORDER BY id DESC", ambil=True)
    for q in data:
        q["tayang"] = boleh_tayang(q)
    return data


def verifikasi(id):
    data = jalankan("SELECT * FROM quotes WHERE id = ?", (id,), ambil=True)
    if not data:
        return False, "Quote tidak ditemukan"
    if data[0]["sumber"].strip() == "":
        return False, "Tidak bisa diverifikasi: sumber masih kosong"
    jalankan("UPDATE quotes SET status = 'terverifikasi' WHERE id = ?", (id,))
    return True, "Terverifikasi"


def cabut_verifikasi(id):
    jalankan("UPDATE quotes SET status = 'belum diverifikasi' WHERE id = ?", (id,))


def hapus_quote(id):
    jalankan("DELETE FROM quotes WHERE id = ?", (id,))