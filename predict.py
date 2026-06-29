import joblib
import pandas as pd
from datetime import datetime
from firebase_config import firebase_db

MODEL_STATUS_FILE = "model_status.pkl"
MODEL_ESTIMASI_FILE = "model_estimasi.pkl"

model_status = joblib.load(MODEL_STATUS_FILE)
model_estimasi = joblib.load(MODEL_ESTIMASI_FILE)


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
        return "Kondisi masih aman. Tidak terdapat indikasi banjir dalam waktu dekat berdasarkan prediksi Machine Learning."

    elif status_final == "WASPADA":
        return (
            "Kondisi mulai meningkat. Banjir diperkirakan terjadi sekitar "
            f"{format_waktu_estimasi(estimasi_menit)} lagi apabila hujan dan kenaikan air terus berlangsung."
        )

    elif status_final == "SIAGA":
        return (
            "Potensi banjir tinggi. Banjir diperkirakan terjadi sekitar "
            f"{format_waktu_estimasi(estimasi_menit)} lagi berdasarkan prediksi Machine Learning."
        )

    elif status_final == "BAHAYA":
        return "Banjir sudah terjadi atau kondisi air telah berada pada level bahaya."

    return "Status tidak diketahui."


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

    prediksi_ml = str(model_status.predict(data_baru)[0])

    probabilitas = float(max(model_status.predict_proba(data_baru)[0])) * 100

    estimasi_pred = model_estimasi.predict(data_baru)[0]

    try:
        estimasi_menit = int(float(estimasi_pred))
    except:
        estimasi_menit = 0

    if estimasi_menit < 0:
        estimasi_menit = 0

    status_final = prediksi_ml

    if status_final == "AMAN":
        estimasi_menit_output = "-"
    elif status_final == "BAHAYA":
        estimasi_menit = 0
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

        "ml_prediksi": prediksi_ml,
        "status_final": status_final,
        "probabilitas_ml": round(probabilitas, 2),

        "estimasi_menit": estimasi_menit_output,
        "estimasi": estimasi,

        "waktu_prediksi": waktu,
        "sumber_data": "Random Forest Classifier + Random Forest Regressor Railway"
    }

    db.reference("/banjir/ml").set(hasil_ml)
    db.reference("/banjir/status").set(status_final)
    db.reference("/banjir/update").set(waktu)

    return hasil_ml
