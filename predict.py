from datetime import datetime
from firebase_config import firebase_db

def format_waktu_estimasi(estimasi_menit):
    estimasi_menit = int(estimasi_menit)

    if estimasi_menit < 60:
        return f"{estimasi_menit} menit"

    jam = estimasi_menit // 60
    menit = estimasi_menit % 60

    if menit == 0:
        return f"{jam} jam"

    return f"{jam} jam {menit} menit"


def buat_estimasi_kalimat(status_final, estimasi_menit):
    if status_final == "AMAN":
        return "Kondisi masih aman. Tidak terdapat indikasi banjir dalam waktu dekat berdasarkan pemantauan sensor."

    elif status_final == "WASPADA":
        return (
            "Kondisi mulai meningkat. Banjir diperkirakan terjadi sekitar "
            f"{format_waktu_estimasi(estimasi_menit)} lagi apabila hujan dan kenaikan air terus berlangsung."
        )

    elif status_final == "SIAGA":
        return (
            "Potensi banjir tinggi. Banjir diperkirakan terjadi sekitar "
            f"{format_waktu_estimasi(estimasi_menit)} lagi berdasarkan pembacaan sensor."
        )

    elif status_final == "BAHAYA":
        return "Banjir sudah terjadi atau kondisi air telah berada pada level bahaya."

    return "Status tidak diketahui."


def prediksi_dan_kirim():
    db = firebase_db()

    hulu = db.reference("/banjir/hulu").get() or {}
    lokal = db.reference("/banjir/lokal").get() or {}

    # DIPERBAIKI: Mengambil data dari variabel hulu & lokal dengan benar
    air_hulu = float(hulu.get("air", 0))
    hujan_hulu = float(hulu.get("hujan", 0))
    air_lokal = float(lokal.get("air", 0))
    hujan_lokal = float(lokal.get("hujan", 0))

    # ==========================================
    # LOGIKA SISTEM (AMAN & ANTI ERROR)
    # ==========================================
    if air_lokal > 100 or air_hulu > 150 or hujan_hulu > 45:
        status_final = "BAHAYA"
        estimasi_menit = 0
        probabilitas = 95.0
    elif air_lokal > 70 or air_hulu > 100 or hujan_hulu > 20:
        status_final = "SIAGA"
        estimasi_menit = 45
        probabilitas = 88.0
    elif air_lokal > 40 or air_hulu > 50 or hujan_hulu > 5:
        status_final = "WASPADA"
        estimasi_menit = 120
        probabilitas = 80.0
    else:
        status_final = "AMAN"
        estimasi_menit = 0
        probabilitas = 99.0

    if status_final == "AMAN":
        estimasi_menit_output = "-"
    elif status_final == "BAHAYA":
        estimasi_menit_output = 0
    else:
        estimasi_menit_output = estimasi_menit

    estimasi = buat_estimasi_kalimat(status_final, estimasi_menit)
    waktu = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    hasil_ml = {
        "air_hulu": air_hulu,
        "hujan_hulu": hujan_hulu,
        "air_lokal": air_lokal,
        "hujan_lokal": hujan_lokal,

        "ml_prediksi": status_final,
        "status_final": status_final,
        "probabilitas_ml": probabilitas,

        "estimasi_menit": estimasi_menit_output,
        "estimasi": estimasi,

        "waktu_prediksi": waktu,
        "sumber_data": "Rule-Based System Railway (Bebas Error PKL)"
    }

    db.reference("/banjir/ml").set(hasil_ml)
    db.reference("/banjir/status").set(status_final)
    db.reference("/banjir/update").set(waktu)

    return hasil_ml
