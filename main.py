import os
import pickle
import cv2
import face_recognition
import numpy as np
import cvzone
from datetime import datetime

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import firestore

cred = credentials.Certificate("Resources/serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    'databaseURL':"https://facerecognitionsystem-68b2c-default-rtdb.firebaseio.com/"
})

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam")
    exit()

# Set webcam properties
cap.set(3, 640)  # Width
cap.set(4, 480)  # Height

# Load background image
imagebackground = cv2.imread('Resources/background.png')
if imagebackground is None:
    print("Error: Could not load background image")
    cap.release()
    exit()

#importing the mode images into a list
folderModepath = 'Resources/Modes'
modePathList = os.listdir(folderModepath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModepath,path)))
#print(len(imgModeList))

#load the  encoding file

print("Loading Encode file ...")
file = open('EncodeFile.p','rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentsIds = encodeListKnownWithIds
#print(studentsIds)
print("Encode file loaded ...")

# Constants
FACE_MATCH_THRESHOLD = 0.6  # Lower is more strict
PROCESS_EVERY_N_FRAMES = 2  # Process every 2nd frame for better performance
frame_count = 0

while True:
    success, img = cap.read()
    if not success:
        print("Error: Could not read frame from webcam")
        break

    frame_count += 1
    # Only process every nth frame
    if frame_count % PROCESS_EVERY_N_FRAMES == 0:
        # Resize frame for faster processing
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        # Detect faces in frame
        faceCurFrame = face_recognition.face_locations(imgS, model="hog")  # Use HOG for faster processing
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)


    imagebackground[0:480, 0:640] = img
    # Resize mode image to fit the background
    mode_img = cv2.resize(imgModeList[3], (213, 436))
    imagebackground[44:44+436, 640:640+213] = mode_img

    if len(encodeCurFrame) == 0:
        # Only print message occasionally to avoid spam
        if frame_count % 30 == 0:
            print("Waiting for face detection...")
    else:
        # Process each detected face
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace, tolerance=FACE_MATCH_THRESHOLD)
            faceDistance = face_recognition.face_distance(encodeListKnown, encodeFace)

            if len(faceDistance) > 0:
                best_idx = np.argmin(faceDistance)
                best_match = matches[best_idx]
                min_distance = faceDistance[best_idx]

                # Scale back face locations to original size
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                
                if best_match and min_distance < FACE_MATCH_THRESHOLD:
                    # Draw green box for recognized faces
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                    imagebackground = cvzone.cornerRect(imagebackground, bbox, rt=0, colorC=(0, 255, 0))
                    
                    # Add name/ID and confidence score
                    student_id = studentsIds[best_idx]
                    confidence = (1 - min_distance) * 100
                    cv2.putText(imagebackground, f"ID: {student_id}", (55 + x1, 162 + y1 - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(imagebackground, f"Conf: {confidence:.1f}%", (55 + x1, 162 + y2 + 25),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                else:
                    # Draw red box for unknown faces
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                    imagebackground = cvzone.cornerRect(imagebackground, bbox, rt=0, colorC=(0, 0, 255))
                    cv2.putText(imagebackground, "Unknown", (55 + x1, 162 + y1 - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)


    # Add timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(imagebackground, current_time, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Display help text
    cv2.putText(imagebackground, "Press 'q' to quit", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Show the result
    cv2.imshow('Face Attendance', imagebackground)

    # Check for 'q' key to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()