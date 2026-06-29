import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

DATASET_FILE = "dataset_banjir_rf_100_data.csv"
MODEL_FILE = "model.pkl"

df = pd.read_csv(DATASET_FILE)

X = df[["air_hulu", "hujan_hulu", "air_lokal", "hujan_lokal"]]
y = df["status"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)
akurasi = accuracy_score(y_test, y_pred) * 100

joblib.dump(model, MODEL_FILE)

print("Training selesai")
print("Total dataset:", len(df))
print("Data training:", len(X_train))
print("Data testing:", len(X_test))
print("Akurasi model:", round(akurasi, 2), "%")
print(classification_report(y_test, y_pred))
print("Model disimpan sebagai:", MODEL_FILE)
