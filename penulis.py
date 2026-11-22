import random

JUDUL = [
    "Kata-kata {tokoh} yang layak direnungkan",
    "Renungan hari ini dari {tokoh}",
    "{tokoh}: satu kalimat, seribu makna",
    "Pesan abadi dari {tokoh}",
]

REFLEKSI = [
    "Apa yang kalimat ini ubah dari cara pandang Anda hari ini?",
    "Bagian mana dari kalimat ini yang paling mengena untuk Anda?",
    "Kapan terakhir kali Anda merasakan kebenaran kalimat ini?",
]

HASHTAG_DASAR = ["#quotes", "#kutipan", "#filsafat", "#motivasi", "#inspirasi", "#windcreat"]


def hashtag_tokoh(tokoh):
    nama = "".join(c for c in tokoh.lower() if c.isalnum())
    return "#" + nama if nama else ""


def buat_konten(quote):
    tokoh = quote["tokoh"]
    judul = random.choice(JUDUL).format(tokoh=tokoh)
    caption = (
        f"“{quote['teks']}”\n"
        f"— {tokoh}\n"
        f"Sumber: {quote['sumber']}\n\n"
        f"{random.choice(REFLEKSI)}\n"
        f"Simpan postingan ini dan bagikan ke orang yang perlu membacanya."
    )
    tag = [hashtag_tokoh(tokoh)] + HASHTAG_DASAR
    hashtag = " ".join(t for t in tag if t)
    return {"judul": judul, "caption": caption, "hashtag": hashtag}