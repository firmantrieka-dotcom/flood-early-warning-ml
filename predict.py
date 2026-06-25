import joblib
import pandas as pd
from datetime import datetime
from firebase_config import firebase_db

MODEL_FILE = "model.pkl"
model = joblib.load(MODEL_FILE)

BATAS_BAHAYA_AIR = 203  # skala 0–270 cm

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

def buat_estimasi(status_final):
    if status_final == "BAHAYA":
        return "Ketinggian air sudah berada pada level bahaya, potensi banjir sangat tinggi"
    elif status_final == "SIAGA":
        return "Ketinggian air meningkat, masyarakat perlu bersiap"
    elif status_final == "WASPADA":
        return "Kondisi air mulai meningkat, masyarakat perlu waspada"
    else:
        return "Kondisi air masih normal"

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

    prediksi_ml = model.predict(data_baru)[0]
    probabilitas = max(model.predict_proba(data_baru)[0]) * 100

    status_logika = buat_status_logika(
        air_hulu,
        hujan_hulu,
        air_lokal,
        hujan_lokal
    )

    # Random Forest sebagai penentu utama
    status_final = prediksi_ml

    # Logika hanya sebagai pengaman jika air benar-benar melewati batas bahaya
    if air_hulu >= BATAS_BAHAYA_AIR or air_lokal >= BATAS_BAHAYA_AIR:
        status_final = "BAHAYA"

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
        "estimasi": buat_estimasi(status_final),
        "waktu_prediksi": waktu,
        
    }

    db.reference("/banjir/ml").set(hasil_ml)
    db.reference("/banjir/status").set(status_final)
    db.reference("/banjir/update").set(waktu)

    return hasil_ml
