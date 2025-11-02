import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    'databaseURL':"https://facerecognitionsystem-68b2c-default-rtdb.firebaseio.com/"
})

ref = db.reference('Students')

data = {
    "347568":
        {
            "name": "Gadipally Harish Reddy",
            "Age":22,
            "major":"Robotics",
            "starting_year":2021,
            "total_attendence":"60%",
            "standing":"B",
            "year":4,
            "last_attendence_time":"2022-12-11 00:52:34"
        },
    "436472":
        {
            "name": "emily blunt",
            "Age":42,
            "major":"Economics",
            "starting_year":2006,
            "total_attendence":"50%",
            "standing":"C",
            "year":4,
            "last_attendence_time":"2013-2-15 00:54:34"
        },
    "784373":
        {
            "name": "Murtaza Hassan",
            "major":"Maths",
            "starting_year":2018,
            "total_attendence":"40%",
            "standing":"D",
            "year":2,
            "last_attendence_time":"2021-12-11 00:53:34"
        },
    "867393":
        {
            "name": "Elon Musk",
            "Age": 54,
            "major":"AI",
            "starting_year":2005,
            "total_attendence":"30%",
            "standing":"G",
            "year":3,
            "last_attendence_time":"2022-12-11 00:55:34"
        }

}

for key, value in data.items():
    ref.child(key).set(value)

print("✅ Data uploaded successfully!")