# AddToFirestore_local_images.py
import os
import firebase_admin
from firebase_admin import credentials, firestore

BASE = os.path.dirname(os.path.abspath(__file__))
cred = credentials.Certificate(os.path.join(BASE, "serviceAccountKey.json"))
# initialize once
firebase_admin.initialize_app(cred)
db = firestore.client()

# Example: build documents from local images folder & a small metadata dict
images_folder = os.path.join(BASE, "Images")
# map image filename -> metadata (you can build this programmatically)
metadata = {
    "347568.jpeg": {"name": "Gadipally Harish Reddy",
                    "Age":22,
                    "major":"Robotics",
                    "starting_year":2021,
                    "total_attendence":"60%",
                    "standing":"B","year": 4,
                    "last_attendence_time":"2022-12-11 00:52:34"},
    "436472.jpeg": { "name": "emily blunt",
            "Age":42,
            "major":"Economics",
            "starting_year":2006,
            "total_attendence":"50%",
            "standing":"C",
            "year":4,
            "last_attendence_time":"2013-2-15 00:54:34"},
    "784373.jpeg": {"name": "Murtaza Hassan",
            "major":"Maths",
            "starting_year":2018,
            "total_attendence":"40%",
            "standing":"D",
            "year":2,
            "last_attendence_time":"2021-12-11 00:53:34"},
    "867393.jpeg": { "name": "Elon Musk",
            "Age": 54,
            "major":"AI",
            "starting_year":2005,
            "total_attendence":"30%",
            "standing":"G",
            "year":3,
            "last_attendence_time":"2022-12-11 00:55:34"},
}

for fname, meta in metadata.items():
    student_id = os.path.splitext(fname)[0]
    doc_ref = db.collection("Students").document(student_id)
    payload = meta.copy()
    payload["image_filename"] = os.path.join("Images", fname)  # local path (for your local app)
    doc_ref.set(payload)
    print("Saved", student_id, payload)

print("Done — metadata stored in Firestore.")
