import os
import joblib
import pandas as pd
from datetime import datetime
from firebase_config import firebase_db

MODEL_PATH = "model.pkl"  # Sesuaikan dengan nama file modelmu di GitHub

model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        print("Model Machine Learning berhasil dimuat!")
    except Exception as e:
        print(f"Gagal memuat model: {e}")
else:
    print(f"File model '{MODEL_PATH}' tidak ditemukan.")

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
    hujan_hulu = float(hulu.get("hujan", 0))
    air_lokal = float(lokal.get("air", 0))
    hujan_lokal = float(lokal.get("hujan", 0))

    status_final = "AMAN"
    probabilitas = 100.0
    estimasi_menit = 0

    if model is not None:
        try:
            # Menggunakan DataFrame agar aman jika model dilatih menggunakan Pandas
            fitur_input = pd.DataFrame([[air_hulu, hujan_hulu, air_lokal, hujan_lokal]], 
                                       columns=['air_hulu', 'hujan_hulu', 'air_lokal', 'hujan_lokal'])

            prediksi = model.predict(fitur_input)
            status_final = str(prediksi[0])

            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(fitur_input)
                probabilitas = float(max(proba[0]) * 100)

            if status_final == "BAHAYA":
                estimasi_menit = 0
            elif status_final == "SIAGA":
                estimasi_menit = 45
            elif status_final == "WASPADA":
                estimasi_menit = 120
            else:
                estimasi_menit = 0

        except Exception as e:
            # Jika ada error pada model, cetak error aslinya agar kelihatan di log Railway
            print("ERROR DETAIL DI MODEL PREDICT:", str(e))
            raise e  # Melempar error agar tertangkap di browser saat tes manual
    else:
        raise Exception("Model Machine Learning (.pkl) tidak berhasil dimuat di server.")

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
        "probabilitas_ml": round(probabilitas, 2),
        "estimasi_menit": estimasi_menit_output,
        "estimasi": estimasi,
        "waktu_prediksi": waktu,
        "sumber_data": "Trained Machine Learning Model (.pkl)"
    }

    # Mengirim ke Firebase
    db.reference("/banjir/ml").set(hasil_ml)
    db.reference("/banjir/status").set(status_final)
    db.reference("/banjir/update").set(waktu)

    return hasil_ml
