import json
import os
from flask import Flask, render_template, jsonify, request

import database

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


# ---------- Halaman ----------
@app.route("/")
def beranda():
    return render_template("index.html")


@app.route("/perekap")
def halaman_perekap():
    return render_template("perekap.html")


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
    