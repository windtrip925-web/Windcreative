import os
from PIL import Image, ImageDraw, ImageFont

LEBAR, TINGGI = 1080, 1350
LATAR = (15, 23, 42)
TEKS = (241, 245, 249)
AKSEN = (212, 175, 55)
REDUP = (148, 163, 184)

FONT = {
    "serif": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    ],
    "tebal": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "biasa": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
}


def muat_font(jenis, ukuran):
    for path in FONT[jenis]:
        if os.path.exists(path):
            return ImageFont.truetype(path, ukuran)
    return ImageFont.load_default(size=ukuran)


def bungkus(draw, teks, font, lebar_maks):
    baris, sekarang = [], ""
    for kata in teks.split():
        coba = (sekarang + " " + kata).strip()
        if draw.textlength(coba, font=font) <= lebar_maks:
            sekarang = coba
        else:
            if sekarang:
                baris.append(sekarang)
            sekarang = kata
    if sekarang:
        baris.append(sekarang)
    return baris


def pas_teks(draw, teks, jenis, maks, minim, lebar_maks, tinggi_maks):
    """Cari ukuran huruf terbesar yang masih muat."""
    for ukuran in range(maks, minim - 1, -4):
        font = muat_font(jenis, ukuran)
        baris = bungkus(draw, teks, font, lebar_maks)
        if len(baris) * int(ukuran * 1.35) <= tinggi_maks:
            break
    return font, baris, ukuran


def tulis_tengah(draw, baris, font, ukuran, y, warna):
    for b in baris:
        lebar = draw.textlength(b, font=font)
        draw.text(((LEBAR - lebar) / 2, y), b, font=font, fill=warna)
        y += int(ukuran * 1.35)
    return y


def kanvas(no, total):
    img = Image.new("RGB", (LEBAR, TINGGI), LATAR)
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, LEBAR - 40, TINGGI - 40], outline=AKSEN, width=3)
    tulis_tengah(d, ["W I N D C R E A T"], muat_font("tebal", 30), 30, 90, AKSEN)
    tulis_tengah(d, [f"{no} / {total}"], muat_font("biasa", 28), 28, TINGGI - 110, REDUP)
    return img, d


def slide_quote(quote, total):
    img, d = kanvas(1, total)
    tulis_tengah(d, ["“"], muat_font("serif", 220), 220, 190, AKSEN)
    font, baris, ukuran = pas_teks(d, quote["teks"], "serif", 76, 36, LEBAR - 240, 620)
    tinggi = len(baris) * int(ukuran * 1.35)
    y = 420 + (620 - tinggi) / 2
    tulis_tengah(d, baris, font, ukuran, y, TEKS)
    return img


def slide_tokoh(quote, total):
    img, d = kanvas(2, total)
    tulis_tengah(d, ["DIKATAKAN OLEH"], muat_font("biasa", 32), 32, 400, REDUP)
    font, baris, ukuran = pas_teks(d, quote["tokoh"], "tebal", 84, 44, LEBAR - 240, 260)
    y = tulis_tengah(d, baris, font, ukuran, 470, TEKS)
    d.line([(LEBAR / 2 - 80, y + 30), (LEBAR / 2 + 80, y + 30)], fill=AKSEN, width=4)
    tulis_tengah(d, ["SUMBER ASLI"], muat_font("biasa", 32), 32, y + 90, REDUP)
    font2, baris2, ukuran2 = pas_teks(d, quote["sumber"], "biasa", 42, 26, LEBAR - 240, 260)
    tulis_tengah(d, baris2, font2, ukuran2, y + 150, TEKS)
    return img


def slide_penutup(total):
    img, d = kanvas(total, total)
    f1 = muat_font("serif", 64)
    y = tulis_tengah(d, ["Simpan untuk", "dibaca lagi"], f1, 64, 480, TEKS)
    d.line([(LEBAR / 2 - 80, y + 30), (LEBAR / 2 + 80, y + 30)], fill=AKSEN, width=4)
    f2 = muat_font("biasa", 40)
    tulis_tengah(d, ["Bagikan ke seseorang", "yang membutuhkannya"], f2, 40, y + 90, REDUP)
    tulis_tengah(d, ["Ikuti Windcreat"], muat_font("tebal", 44), 44, y + 260, AKSEN)
    return img


def buat_carousel(quote, folder):
    total = 3
    slide = [slide_quote(quote, total), slide_tokoh(quote, total), slide_penutup(total)]
    nama = []
    for i, img in enumerate(slide, start=1):
        berkas = f"slide{i}.png"
        img.save(os.path.join(folder, berkas))
        nama.append(berkas)
    return nama