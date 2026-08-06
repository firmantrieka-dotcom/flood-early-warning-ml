import os
import joblib
from datetime import datetime
from firebase_config import firebase_db

# PENTING: Pastikan nama file .pkl di bawah ini sama persis dengan yang ada di GitHub kamu
MODEL_PATH = "model.pkl"  # Contoh: model.pkl atau rf_model.pkl

model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        print("Model Machine Learning (.pkl) berhasil dimuat dengan sukses!")
    except Exception as e:
        print(f"Gagal memuat model Machine Learning: {e}")
else:
    print(f"Peringatan: File model '{MODEL_PATH}' tidak ditemukan di repository GitHub.")


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
        return f"Waspada! Potensi kenaikan air terdeteksi oleh model, estimasi kritis sekitar {format_waktu_estimasi(estimasi_menit)} lagi."
    elif status_final == "SIAGA":
        return f"Siaga! Model Machine Learning mendeteksi ancaman banjir sekitar {format_waktu_estimasi(estimasi_menit)} lagi."
    elif status_final == "BAHAYA":
        return "Bahaya! Model mendeteksi status kritis atau banjir telah terjadi."
    return "Status berdasarkan model Machine Learning."


def prediksi_dan_kirim():
    db = firebase_db()

    # Mengambil data dari sensor Firebase
    hulu = db.reference("/banjir/hulu").get() or {}
    lokal = db.reference("/banjir/lokal").get() or {}

    air_hulu = float(hulu.get("air", 0))
    hujan_hulu = float(hujan.get("hujan", 0))
    air_lokal = float(lokal.get("air", 0))
    hujan_lokal = float(lokal.get("hujan", 0))

    status_final = "AMAN"
    probabilitas = 100.0
    estimasi_menit = 0

    # ==========================================
    # EKsekusi Prediksi Murni dari Model .pkl
    # ==========================================
    if model is not None:
        try:
            # Urutan fitur harus SAMA PERSIS dengan saat kamu melatih model (Training di Colab/Jupyter)
            # Contoh umum urutan fitur: [air_hulu, hujan_hulu, air_lokal, hujan_lokal]
            fitur_input = [[air_hulu, hujan_hulu, air_lokal, hujan_lokal]]

            # Memprediksi kelas menggunakan model
            prediksi = model.predict(fitur_input)
            status_final = str(prediksi[0])

            # Mengambil nilai probabilitas (tingkat keyakinan) model jika ada
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(fitur_input)
                probabilitas = float(max(proba[0]) * 100)

            # Menentukan estimasi waktu berdasarkan kelas hasil prediksi model
            if status_final == "BAHAYA":
                estimasi_menit = 0
            elif status_final == "SIAGA":
                estimasi_menit = 45
            elif status_final == "WASPADA":
                estimasi_menit = 120
            else:
                estimasi_menit = 0

        except Exception as e:
            print("Error saat menjalankan model Machine Learning:", e)
            status_final = "AMAN"
    else:
        status_final = "AMAN"
        probabilitas = 0.0

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

    # Mengirim hasil ke database Firebase
    db.reference("/banjir/ml").set(hasil_ml)
    db.reference("/banjir/status").set(status_final)
    db.reference("/banjir/update").set(waktu)

    return hasil_ml
