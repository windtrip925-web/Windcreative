import json
import os
import time
from flask import Flask, render_template, jsonify, request

import database
import desainer
import editor
import penulis

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
app = Flask(__name__)
database.siapkan_db()


def baca(nama):
    with open(os.path.join(DATA, nama), encoding="utf-8") as f:
        return json.load(f)


def simpan(nama, isi):
    with open(os.path.join(DATA, nama), "w", encoding="utf-8") as f:
        json.dump(isi, f, ensure_ascii=False, indent=2)


def cari_quote(quote_id):
    return next((q for q in database.daftar_quote() if q["id"] == quote_id), None)


def folder_hasil(quote_id):
    nama = "q%d-%s" % (quote_id, time.strftime("%Y%m%d-%H%M%S"))
    return nama, os.path.join(BASE, "static", "hasil", nama)


def tambah_antrean(item):
    antrean = baca("antrean.json")
    item["id"] = max([t["id"] for t in antrean], default=0) + 1
    item["status"] = "menunggu"
    antrean.append(item)
    simpan("antrean.json", antrean)
    return item


# ---------- Halaman ----------
@app.route("/")
def beranda():
    return render_template("index.html")


@app.route("/perekap")
def halaman_perekap():
    return render_template("perekap.html")


@app.route("/studio")
def halaman_studio():
    return render_template("studio.html")


# ---------- Kantor: karyawan & antrean ----------
@app.route("/api/karyawan")
def api_karyawan():
    return jsonify(baca("karyawan.json"))


@app.route("/api/antrean")
def api_antrean():
    return jsonify(baca("antrean.json"))


@app.route("/api/antrean/<int:id>/<aksi>", methods=["POST"])
def ubah_antrean(id, aksi):
    if aksi not in ("setujui", "tolak"):
        return jsonify({"error": "aksi tidak dikenal"}), 400
    antrean = baca("antrean.json")
    for tugas in antrean:
        if tugas["id"] == id:
            tugas["status"] = "disetujui" if aksi == "setujui" else "ditolak"
    simpan("antrean.json", antrean)
    return jsonify({"ok": True})


# ---------- Perekap: quotes ----------
@app.route("/api/quotes", methods=["GET"])
def api_daftar_quote():
    return jsonify(database.daftar_quote())


@app.route("/api/quotes", methods=["POST"])
def api_tambah_quote():
    data = request.get_json()
    teks = data.get("teks", "").strip()
    tokoh = data.get("tokoh", "").strip()
    sumber = data.get("sumber", "").strip()
    if not teks or not tokoh:
        return jsonify({"pesan": "Quote dan nama tokoh wajib diisi"}), 400
    database.tambah_quote(teks, tokoh, sumber)
    return jsonify({"pesan": "Quote tersimpan"})


@app.route("/api/quotes/<int:id>/verifikasi", methods=["POST"])
def api_verifikasi(id):
    berhasil, pesan = database.verifikasi(id)
    return jsonify({"pesan": pesan}), (200 if berhasil else 400)


@app.route("/api/quotes/<int:id>/cabut", methods=["POST"])
def api_cabut(id):
    database.cabut_verifikasi(id)
    return jsonify({"pesan": "Verifikasi dicabut"})


@app.route("/api/quotes/<int:id>/hapus", methods=["POST"])
def api_hapus(id):
    database.hapus_quote(id)
    return jsonify({"pesan": "Quote dihapus"})


# ---------- Studio: Penulis, Desainer, Editor Video ----------
@app.route("/api/studio/layak")
def api_studio_layak():
    return jsonify([q for q in database.daftar_quote() if q["tayang"]])


@app.route("/api/studio/buat", methods=["POST"])
def api_studio_buat():
    quote = cari_quote((request.get_json() or {}).get("quote_id"))
    if quote is None:
        return jsonify({"pesan": "Quote tidak ditemukan"}), 404
    if not quote["tayang"]:
        return jsonify({"pesan": "Ditolak: quote belum terverifikasi atau sumber kosong"}), 400

    konten = penulis.buat_konten(quote)
    nama, folder = folder_hasil(quote["id"])
    os.makedirs(folder, exist_ok=True)
    berkas = desainer.buat_carousel(quote, folder)
    item = tambah_antrean({
        "judul": konten["judul"],
        "jenis": "Carousel",
        "quote_id": quote["id"],
        "caption": konten["caption"],
        "hashtag": konten["hashtag"],
        "slides": ["/static/hasil/%s/%s" % (nama, b) for b in berkas],
    })
    return jsonify({"pesan": "Carousel dibuat dan masuk antrean persetujuan", "item": item})


@app.route("/api/studio/video", methods=["POST"])
def api_studio_video():
    data = request.get_json() or {}
    quote = cari_quote(data.get("quote_id"))
    if quote is None:
        return jsonify({"pesan": "Quote tidak ditemukan"}), 404
    if not quote["tayang"]:
        return jsonify({"pesan": "Ditolak: quote belum terverifikasi atau sumber kosong"}), 400

    konten = penulis.buat_konten(quote)
    nama, folder = folder_hasil(quote["id"])
    try:
        berkas, catatan = editor.buat_reels(quote, folder, bool(data.get("voice")))
    except RuntimeError as e:
        return jsonify({"pesan": "Gagal membuat video: %s" % e}), 500

    item = tambah_antrean({
        "judul": konten["judul"],
        "jenis": "Reels",
        "quote_id": quote["id"],
        "caption": konten["caption"],
        "hashtag": konten["hashtag"],
        "video": "/static/hasil/%s/%s" % (nama, berkas),
    })
    pesan = "Video dibuat dan masuk antrean persetujuan"
    if catatan:
        pesan += " (" + " ".join(catatan) + ")"
    return jsonify({"pesan": pesan, "item": item})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)