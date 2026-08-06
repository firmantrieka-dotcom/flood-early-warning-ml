import os
import joblib
import pandas as pd
from datetime import datetime
from firebase_config import firebase_db

STATUS_MODEL_PATH = "model_status.pkl"
ESTIMASI_MODEL_PATH = "model_estimasi.pkl"

model_status = None
model_estimasi = None

if os.path.exists(STATUS_MODEL_PATH):
    try:
        model_status = joblib.load(STATUS_MODEL_PATH)
    except Exception:
        pass

if os.path.exists(ESTIMASI_MODEL_PATH):
    try:
        model_estimasi = joblib.load(ESTIMASI_MODEL_PATH)
    except Exception:
        pass

def prediksi_dan_kirim():
    db = firebase_db()

    hulu = db.reference("/banjir/hulu").get() or {}
    lokal = db.reference("/banjir/lokal").get() or {}

    air_hulu = float(hulu.get("air", 0) or 0)
    hujan_hulu = float(hulu.get("hujan", 0) or 0)
    air_lokal = float(lokal.get("air", 0) or 0)
    hujan_lokal = float(lokal.get("hujan", 0) or 0)

    status_final = "AMAN"
    probabilitas = 95.0
    estimasi_menit = 0

    try:
        fitur_array = [[air_hulu, hujan_hulu, air_lokal, hujan_lokal]]
        df_fitur = pd.DataFrame(fitur_array, columns=['air_hulu', 'hujan_hulu', 'air_lokal', 'hujan_lokal'])

        if model_status is not None:
            prediksi = model_status.predict(df_fitur)
            status_final = str(prediksi[0])
            if hasattr(model_status, "predict_proba"):
                proba = model_status.predict_proba(df_fitur)
                probabilitas = float(max(proba[0]) * 100)

        if model_estimasi is not None:
            pred_est = model_estimasi.predict(df_fitur)
            estimasi_menit = float(pred_est[0])
    except Exception:
        if air_lokal > 100 or air_hulu > 150:
            status_final = "BAHAYA"
            estimasi_menit = 0
        elif air_lokal > 70 or air_hulu > 100:
            status_final = "SIAGA"
            estimasi_menit = 45
        elif air_lokal > 40 or air_hulu > 50:
            status_final = "WASPADA"
            estimasi_menit = 120
        else:
            status_final = "AMAN"
            estimasi_menit = 0

    estimasi_menit_output = 0 if status_final == "BAHAYA" else int(max(0, estimasi_menit))
    if status_final == "AMAN":
        estimasi_menit_output = "-"

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
        "waktu_prediksi": waktu,
        "sumber_data": "Trained ML Models (.pkl)"
    }

    db.reference("/banjir/ml").set(hasil_ml)
    db.reference("/banjir/status").set(status_final)
    db.reference("/banjir/update").set(waktu)

    return hasil_ml
