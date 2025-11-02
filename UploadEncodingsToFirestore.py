# UploadEncodingsToFirestore.py
import os, pickle
import firebase_admin
from firebase_admin import credentials, firestore

BASE = os.path.dirname(os.path.abspath(__file__))
cred = credentials.Certificate(os.path.join(BASE, "serviceAccountKey.json"))
firebase_admin.initialize_app(cred)
db = firestore.client()

ENC_PATH = os.path.join(BASE, "EncodeFile.p")
if not os.path.exists(ENC_PATH):
    print("EncodeFile.p not found. Run EncodeGenerator.py first to generate encodings.")
else:
    with open(ENC_PATH, "rb") as f:
        encodeListKnown, studentsIds = pickle.load(f)

    print("Loaded", len(studentsIds), "encodings")

    for enc, sid in zip(encodeListKnown, studentsIds):
        # convert numpy arrays to lists (if they aren't plain lists already)
        try:
            enc_list = enc.tolist()
        except Exception:
            enc_list = list(enc)
        doc_ref = db.collection("FaceEncodings").document(sid)
        doc_ref.set({"encoding": enc_list})
        print("Wrote encoding for", sid)

    print("All encodings uploaded.")
