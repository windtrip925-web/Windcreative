import asyncio
import os
import random
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw

from desainer import muat_font, pas_teks

BASE = os.path.dirname(os.path.abspath(__file__))
MUSIK_DIR = os.path.join(BASE, "musik")

W, H, FPS = 1080, 1920, 24
LATAR = (15, 23, 42)
TEKS = (241, 245, 249)
AKSEN = (212, 175, 55)
JEDA_AWAL = 0.8


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def tulis_tengah(d, teks, font, y, warna):
    lebar = d.textlength(teks, font=font)
    d.text(((W - lebar) / 2, y), teks, font=font, fill=warna)


def font_muat(d, teks, jenis, ukuran, lebar_maks, minim=22):
    while ukuran > minim:
        font = muat_font(jenis, ukuran)
        if d.textlength(teks, font=font) <= lebar_maks:
            return font
        ukuran -= 2
    return muat_font(jenis, minim)


def lapisan(teks, font, warna, tinggi):
    """Satu baris teks sebagai gambar kecil + mask transparansi."""
    img = Image.new("RGBA", (W, tinggi), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lebar = d.textlength(teks, font=font)
    d.text(((W - lebar) / 2, 8), teks, font=font, fill=warna + (255,))
    return img.convert("RGB"), img.split()[3]


def cari_musik():
    if not os.path.isdir(MUSIK_DIR):
        return None
    berkas = [f for f in os.listdir(MUSIK_DIR)
              if f.lower().endswith((".mp3", ".wav", ".m4a"))]
    return os.path.join(MUSIK_DIR, random.choice(berkas)) if berkas else None


def buat_voice(teks, jalur):
    import edge_tts

    async def kerja():
        await edge_tts.Communicate(teks, "id-ID-ArdiNeural").save(jalur)

    asyncio.run(kerja())


def durasi_audio(jalur):
    hasil = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", jalur],
        capture_output=True, text=True)
    return float(hasil.stdout.strip())


def buat_reels(quote, folder, dengan_voice=False):
    os.makedirs(folder, exist_ok=True)
    catatan = []

    # 1. Voice over (opsional)
    file_voice, durasi_vo = None, 0
    if dengan_voice:
        try:
            file_voice = os.path.join(folder, "voice.mp3")
            buat_voice("%s. Kata %s." % (quote["teks"], quote["tokoh"]), file_voice)
            durasi_vo = durasi_audio(file_voice)
        except Exception:
            file_voice = None
            catatan.append("Voice over gagal dibuat, video dibuat tanpa narasi.")

    # 2. Latar tetap
    bg = Image.new("RGB", (W, H), LATAR)
    d = ImageDraw.Draw(bg)
    d.rectangle([50, 50, W - 50, H - 50], outline=AKSEN, width=3)
    tulis_tengah(d, "W I N D C R E A T", muat_font("tebal", 34), 130, AKSEN)
    tulis_tengah(d, "“", muat_font("serif", 260), 400, AKSEN)

    # 3. Adegan teks
    font, baris, ukuran = pas_teks(d, quote["teks"], "serif", 80, 40, W - 240, 800)
    tinggi_baris = int(ukuran * 1.35)
    y = 680 + (800 - len(baris) * tinggi_baris) // 2

    adegan = []
    mulai = JEDA_AWAL
    for b in baris:
        rgb, alpha = lapisan(b, font, TEKS, int(ukuran * 1.5))
        adegan.append((rgb, alpha, y, mulai))
        y += tinggi_baris
        mulai += 0.5

    y += 50
    tokoh_teks = "— " + quote["tokoh"]
    f_tokoh = font_muat(d, tokoh_teks, "tebal", 56, W - 200)
    rgb, alpha = lapisan(tokoh_teks, f_tokoh, AKSEN, 90)
    tokoh_mulai = mulai + 0.3
    adegan.append((rgb, alpha, y, tokoh_mulai))

    sumber_teks = "Sumber: " + quote["sumber"]
    if len(sumber_teks) > 80:
        sumber_teks = sumber_teks[:77] + "…"
    f_sumber = font_muat(d, sumber_teks, "biasa", 34, W - 200)
    rgb, alpha = lapisan(sumber_teks, f_sumber, (148, 163, 184), 70)
    sumber_mulai = tokoh_mulai + 0.5
    adegan.append((rgb, alpha, y + 90, sumber_mulai))

    total = max(8.0, sumber_mulai + 3.5)
    if file_voice:
        total = max(total, JEDA_AWAL + durasi_vo + 1.5)

    # 4. Gambar semua frame
    tmp = tempfile.mkdtemp()
    try:
        for i in range(int(total * FPS)):
            t = i / FPS
            frame = bg.copy()
            g = 1.0 if t < total - 0.8 else max(0.0, (total - t) / 0.8)
            for rgb, alpha, y_asli, m in adegan:
                p = ease((t - m) / 0.6)
                a = p * g
                if a <= 0.01:
                    continue
                y_gambar = y_asli + int((1 - p) * 40)
                frame.paste(rgb, (0, y_gambar), alpha.point(lambda v: int(v * a)))
            dd = ImageDraw.Draw(frame)
            dd.rectangle([100, H - 130, W - 100, H - 124], fill=(51, 65, 85))
            dd.rectangle([100, H - 130, 100 + int((W - 200) * t / total), H - 124], fill=AKSEN)
            frame.save(os.path.join(tmp, "%05d.jpg" % (i + 1)), quality=92)

        # 5. Susun video dengan FFmpeg
        musik = cari_musik()
        if musik is None:
            catatan.append("Folder musik/ kosong, video dibuat tanpa musik latar.")

        keluar = os.path.join(folder, "reels.mp4")
        cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.jpg")]
        idx, idx_musik, idx_voice = 1, None, None
        if musik:
            cmd += ["-stream_loop", "-1", "-i", musik]
            idx_musik = idx
            idx += 1
        if file_voice:
            cmd += ["-i", file_voice]
            idx_voice = idx

        fade = "afade=t=out:st=%.2f:d=1.5" % (total - 1.5)
        filt = None
        if idx_musik and idx_voice:
            filt = ("[%d:a]volume=0.15,%s[m];[%d:a]adelay=800|800,apad[v];"
                    "[m][v]amix=inputs=2:duration=longest,volume=2[a]"
                    % (idx_musik, fade, idx_voice))
        elif idx_musik:
            filt = "[%d:a]volume=0.35,%s[a]" % (idx_musik, fade)
        elif idx_voice:
            filt = "[%d:a]adelay=800|800[a]" % idx_voice

        if filt:
            cmd += ["-filter_complex", filt, "-map", "0:v", "-map", "[a]"]
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-pix_fmt", "yuv420p", "-r", str(FPS)]
        if filt:
            cmd += ["-c:a", "aac", "-b:a", "160k"]
        cmd += ["-t", "%.2f" % total, "-movflags", "+faststart", keluar]

        try:
            hasil = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            raise RuntimeError("FFmpeg belum terpasang")
        if hasil.returncode != 0:
            raise RuntimeError(hasil.stderr[-300:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return "reels.mp4", catatan