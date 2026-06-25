import joblib
import pandas as pd
from datetime import datetime
from firebase_config import firebase_db

MODEL_STATUS_FILE = "model_status.pkl"
MODEL_ESTIMASI_FILE = "model_estimasi.pkl"

model_status = joblib.load(MODEL_STATUS_FILE)
model_estimasi = joblib.load(MODEL_ESTIMASI_FILE)

BATAS_BAHAYA_AIR = 203  # skala air 0–270 cm

def buat_status_logika(air_hulu, hujan_hulu, air_lokal, hujan_lokal):
    nilai_air_tertinggi = max(air_hulu, air_lokal)

    if nilai_air_tertinggi >= 203:
        return "BAHAYA"
    elif nilai_air_tertinggi >= 136 or hujan_hulu >= 80 or hujan_lokal >= 80:
        return "SIAGA"
    elif nilai_air_tertinggi >= 68 or hujan_hulu >= 40 or hujan_lokal >= 40:
        return "WASPADA"
    else:
        return "AMAN"

def buat_estimasi_kalimat(status_final, estimasi_menit):
    if status_final == "BAHAYA":
        return "Banjir sudah terjadi atau kondisi air telah berada pada level bahaya"

    if estimasi_menit <= 0:
        return "Banjir sudah terjadi atau kondisi air telah mencapai batas bahaya"
    elif estimasi_menit < 60:
        return f"Banjir diperkirakan terjadi sekitar {estimasi_menit} menit lagi berdasarkan prediksi Machine Learning"
    else:
        jam = estimasi_menit // 60
        menit = estimasi_menit % 60

        if menit == 0:
            return f"Banjir diperkirakan terjadi sekitar {jam} jam lagi berdasarkan prediksi Machine Learning"
        else:
            return f"Banjir diperkirakan terjadi sekitar {jam} jam {menit} menit lagi berdasarkan prediksi Machine Learning"

def prediksi_dan_kirim():
    db = firebase_db()

    hulu = db.reference("/banjir/hulu").get() or {}
    lokal = db.reference("/banjir/lokal").get() or {}

    air_hulu = float(hulu.get("air", 0))
    hujan_hulu = float(hulu.get("hujan", 0))
    air_lokal = float(lokal.get("air", 0))
    hujan_lokal = float(lokal.get("hujan", 0))

    data_baru = pd.DataFrame([{
        "air_hulu_cm": air_hulu,
        "hujan_hulu_mm": hujan_hulu,
        "air_lokal_cm": air_lokal,
        "hujan_lokal_mm": hujan_lokal
    }])

    prediksi_ml = model_status.predict(data_baru)[0]
    probabilitas = max(model_status.predict_proba(data_baru)[0]) * 100

    estimasi_menit = model_estimasi.predict(data_baru)[0]
    estimasi_menit = int(round(estimasi_menit))

    if estimasi_menit < 0:
        estimasi_menit = 0

    status_logika = buat_status_logika(
        air_hulu,
        hujan_hulu,
        air_lokal,
        hujan_lokal
    )

    # Random Forest sebagai penentu utama
    status_final = prediksi_ml

    # Logika hanya sebagai pengaman jika air melewati batas bahaya
    if air_hulu >= BATAS_BAHAYA_AIR or air_lokal >= BATAS_BAHAYA_AIR:
        status_final = "BAHAYA"
        estimasi_menit = 0

    estimasi = buat_estimasi_kalimat(status_final, estimasi_menit)

    waktu = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    hasil_ml = {
        "air_hulu": air_hulu,
        "hujan_hulu": hujan_hulu,
        "air_lokal": air_lokal,
        "hujan_lokal": hujan_lokal,
        "ml_prediksi": prediksi_ml,
        "status_logika": status_logika,
        "status_final": status_final,
        "probabilitas_ml": round(probabilitas, 2),
        "estimasi_menit": estimasi_menit,
        "estimasi": estimasi,
        "waktu_prediksi": waktu,
        "sumber_data": "Random Forest Classifier + Random Forest Regressor Railway"
    }

    db.reference("/banjir/ml").set(hasil_ml)
    db.reference("/banjir/status").set(status_final)
    db.reference("/banjir/update").set(waktu)

    return hasil_ml
