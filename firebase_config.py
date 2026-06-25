import os
import json
import firebase_admin
from firebase_admin import credentials, db

def init_firebase():
    if firebase_admin._apps:
        return

    database_url = os.environ.get("FIREBASE_DATABASE_URL")
    credentials_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")

    if not database_url:
        raise RuntimeError("FIREBASE_DATABASE_URL belum diatur di Railway Variables")

    if not credentials_json:
        raise RuntimeError("FIREBASE_CREDENTIALS_JSON belum diatur di Railway Variables")

    cred_dict = json.loads(credentials_json)
    cred = credentials.Certificate(cred_dict)

    firebase_admin.initialize_app(cred, {
        "databaseURL": database_url
    })

def get_db():
    init_firebase()
    return db
