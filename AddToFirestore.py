# AddToFirestore.py
import os
import firebase_admin
from firebase_admin import credentials, firestore

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cred = credentials.Certificate(os.path.join(BASE_DIR, "serviceAccountKey.json"))

# initialize app (only once per process)
firebase_admin.initialize_app(cred)  # no databaseURL needed for Firestore

db = firestore.client()  # this is Firestore client

# example data (same structure as your realtime db)
student_id = "347568"
data = {
    "name": "Gadipally Harish Reddy",
    "Age": 22,
    "major": "Robotics",
    "starting_year": 2021,
    "total_attendance": "60%",
    "standing": "B",
    "year": 4,
    "last_attendance_time": "2022-12-11 00:52:34"
}

# write document under collection "Students" with document id = student_id
doc_ref = db.collection("Students").document(student_id)
doc_ref.set(data)

print("Saved to Firestore at Students/{0}".format(student_id))
