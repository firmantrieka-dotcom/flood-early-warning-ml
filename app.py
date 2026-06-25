from flask import Flask, jsonify
from predict import prediksi_dan_kirim

app = Flask(__name__)

@app.route("/")
def home():
    return "Flood Early Warning ML Railway is Running"

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
