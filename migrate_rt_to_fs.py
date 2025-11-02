# migrate_rt_to_fs.py
import os
import firebase_admin
from firebase_admin import credentials, db, firestore

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cred = credentials.Certificate(os.path.join(BASE_DIR, "serviceAccountKey.json"))
# initialize both RTDB and Firestore in same app
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://facerecognitionsystem-68b2c-default-rtdb.firebaseio.com/"
})

rt_db = db.reference("Students")
fs = firestore.client()

students = rt_db.get()  # returns dict of all students
if not students:
    print("No students found in Realtime DB")
else:
    for sid, profile in students.items():
        print("Migrating", sid)
        # optional: transform profile keys (e.g. rename fields)
        fs.collection("Students").document(sid).set(profile)

    print("Migration complete.")
