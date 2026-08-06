import os
import joblib
import pandas as pd
from datetime import datetime
from firebase_config import firebase_db

# Memuat dua model terpisah sesuai file di GitHub kamu
STATUS_MODEL_PATH = "model_status.pkl"
ESTIMASI_MODEL_PATH = "model_estimasi.pkl"

model_status = None
model_estimasi = None

if os.path.exists(STATUS_MODEL_PATH):
    try:
        model_status = joblib.load(STATUS_MODEL_PATH)
        print("Model status.pkl berhasil dimuat!")
    except Exception as e:
        print(f"Gagal memuat model status: {e}")
else:
    print(f"File '{STATUS_MODEL_PATH}' tidak ditemukan.")

if os.path.exists(ESTIMASI_MODEL_PATH):
    try:
        model_estimasi = joblib.load(ESTIMASI_MODEL_PATH)
        print("Model estimasi.pkl berhasil dimuat!")
    except Exception as e:
        print(f"Gagal memuat model estimasi: {e}")
else:
    print(f"File '{ESTIMASI_MODEL_PATH}' tidak ditemukan.")


def format_waktu_estimasi(estimasi_menit):
    try:
        estimasi_menit = int(estimasi_menit)
    except:
        return "0 menit"
    if estimasi_menit < 60:
        return f"{estimasi_menit} menit"
    jam = estimasi_menit // 60
    menit = estimasi_menit % 60
    if menit == 0:
        return f"{jam} jam"
    return f"{jam} jam {menit} menit"


def buat_estimasi_kalimat(status_final, estimasi_menit):
    if status_final == "AMAN":
        return "Kondisi aman berdasarkan analisis Machine Learning."
    elif status_final == "WASPADA":
        return f"Waspada! Potensi kenaikan air terdeteksi, estimasi sekitar {format_waktu_estimasi(estimasi_menit)} lagi."
    elif status_final == "SIAGA":
        return f"Siaga! Model mendeteksi ancaman banjir sekitar {format_waktu_estimasi(estimasi_menit)} lagi."
    elif status_final == "BAHAYA":
        return "Bahaya! Model mendeteksi status kritis atau banjir telah terjadi."
    return "Status berdasarkan model Machine Learning."


def prediksi_dan_kirim():
    db = firebase_db()

    hulu = db.reference("/banjir/hulu").get() or {}
    lokal = db.reference("/banjir/lokal").get() or {}

    air_hulu = float(hulu.get("air", 0))
    hujan_hulu = float(hujan.get("hujan", 0))
    air_lokal = float(lokal.get("air", 0))
    hujan_lokal = float(lokal.get("hujan", 0))

    status_final = "AMAN"
    probabilitas = 100.0
    estimasi_menit = 0

    # Format input menggunakan DataFrame agar sesuai standar scikit-learn
    fitur_input = pd.DataFrame(
        [[air_hulu, hujan_hulu, air_lokal, hujan_lokal]],
        columns=["air_hulu", "hujan_hulu", "air_lokal", "hujan_lokal"]
    )

    # 1. Prediksi Status menggunakan model_status.pkl
    if model_status is not None:
        try:
            prediksi = model_status.predict(fitur_input)
            status_final = str(prediksi[0])

            if hasattr(model_status, "predict_proba"):
                proba = model_status.predict_proba(fitur_input)
                probabilitas = float(max(proba[0]) * 100)
        except Exception as e:
            print("Error saat prediksi status:", e)

    # 2. Prediksi Estimasi waktu menggunakan model_estimasi.pkl
    if model_estimasi is not None:
        try:
            pred_estimasi = model_estimasi.predict(fitur_input)
            estimasi_menit = float(pred_estimasi[0])
        except Exception as e:
            print("Error saat prediksi estimasi:", e)

    # Penyesuaian angka estimasi berdasarkan status
    if status_final == "AMAN":
        estimasi_menit_output = "-"
        estimasi_menit = 0
    elif status_final == "BAHAYA":
        estimasi_menit_output = 0
    else:
        estimasi_menit_output = int(max(0, estimasi_menit))

    estimasi = buat_estimasi_kalimat(status_final, estimasi_menit_output)
    waktu = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    hasil_ml = {
        "air_hulu": air_hulu,
        "hujan_hulu": hujan_hulu,
        "air_lokal": air_lokal,
        "hujan_lokal": hujan_lokal,
        "ml_prediksi": status_final,
        "status_final": status_final,
        "probabilitas_ml": round(probabilitas, 2),
        "estimasi_menit": estimasi_menit_output,
        "estimasi": estimasi,
        "waktu_prediksi": waktu,
        "sumber_data": "Dual Trained ML Models (status & estimasi)"
    }

    # Kirim hasil ke Firebase
    db.reference("/banjir/ml").set(hasil_ml)
    db.reference("/banjir/status").set(status_final)
    db.reference("/banjir/update").set(waktu)

    return hasil_ml
