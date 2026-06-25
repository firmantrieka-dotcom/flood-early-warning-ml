from flask import Flask, jsonify
from predict import prediksi_dan_kirim
from firebase_config import firebase_db
from threading import Thread
import time

app = Flask(__name__)

last_data = None

def baca_data_sensor():
    db = firebase_db()
    hulu = db.reference("/banjir/hulu").get() or {}
    lokal = db.reference("/banjir/lokal").get() or {}

    return {
        "air_hulu": hulu.get("air", 0),
        "hujan_hulu": hulu.get("hujan", 0),
        "air_lokal": lokal.get("air", 0),
        "hujan_lokal": lokal.get("hujan", 0)
    }

def background_worker():
    global last_data

    print("Background worker prediksi otomatis aktif")

    while True:
        try:
            data_sekarang = baca_data_sensor()

            if data_sekarang != last_data:
                print("Data sensor berubah, menjalankan prediksi...")
                hasil = prediksi_dan_kirim()
                print("Prediksi otomatis berhasil:", hasil.get("status_final"))
                last_data = data_sekarang
            else:
                print("Data belum berubah, prediksi tidak dijalankan")

        except Exception as e:
            print("Error background worker:", e)

        time.sleep(10)

worker_started = False

def start_worker():
    global worker_started
    if not worker_started:
        worker = Thread(target=background_worker, daemon=True)
        worker.start()
        worker_started = True

start_worker()

@app.route("/")
def home():
    return "Flood Early Warning ML Railway is Running with Auto Prediction"

@app.route("/predict")
def predict():
    try:
        hasil = prediksi_dan_kirim()
        return jsonify({
            "status": "success",
            "message": "Prediksi berhasil dikirim ke Firebase",
            "data": hasil
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/health")
def health():
    return jsonify({
        "status": "active",
        "message": "Auto prediction worker is running"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
