import os
import json
import firebase_admin
from firebase_admin import credentials, db

def init_firebase():
    if firebase_admin._apps:
        return

    firebase_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    database_url = os.environ.get("FIREBASE_DATABASE_URL")

    if not firebase_json:
        raise RuntimeError("FIREBASE_CREDENTIALS_JSON belum diatur di Railway Variables")

    if not database_url:
        raise RuntimeError("FIREBASE_DATABASE_URL belum diatur di Railway Variables")

    cred_dict = json.loads(firebase_json)
    cred = credentials.Certificate(cred_dict)

    firebase_admin.initialize_app(cred, {
        "databaseURL": database_url
    })

def firebase_db():
    init_firebase()
    return db
