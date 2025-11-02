FaceRecognitionSystem
=====================

Overview
--------
A webcam-based face recognition attendance system. It supports:
- Generating face encodings from local `Images/` (offline)
- Uploading encodings to Firestore (`FaceEncodings` collection)
- Storing student metadata in Firestore (`Students` collection)
- A Firestore-backed UI (`main_with_firestore.py`) that recognizes faces, shows UI modes, and marks attendance
- A simple local UI (`main.py`) that uses `EncodeFile.p` without Firestore

Quick setup (Windows PowerShell)
-------------------------------
1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
```

2. Add your Firebase service key

Place your `serviceAccountKey.json` into `Resources/` (the file is ignored by `.gitignore`).

3. Prepare images

Put labeled images in `Images/` named `<student_id>.jpeg` (or .jpg). Example: `Images/347568.jpeg`.

4. Generate local encodings (optional)

```powershell
python .\EncodeGenerator.py
```

This produces `EncodeFile.p` containing encodings and ids.

5. Upload encodings to Firestore (optional)

```powershell
python .\UploadEncodingsToFirestore.py
```

6. Seed Students metadata (optional)

Edit `AddToFirestore_local_images.py` or use `AddToFirestore.py` to add student metadata into Firestore.

7. Run the app

Firestore-backed UI (preferred):

```powershell
python .\main_with_firestore.py
```

Local-only UI (uses `EncodeFile.p`):

```powershell
python .\main.py
```

Runner helper
-------------
You can use the lightweight runner to pick the mode:

```powershell
python .\run.py --mode firestore
python .\run.py --mode local
```

Health check
------------
Quickly verify required files before running:

```powershell
python .\health_check.py
```

Notes & security
----------------
- Do NOT commit `Resources/serviceAccountKey.json` to public repos. Rotate credentials if this was committed.
- Face embeddings and images are personal data. Treat accordingly.

Troubleshooting
---------------
- If you get errors installing `face_recognition`, ensure you have the correct build tools (on Windows, installing `dlib` may require Visual Studio build tools).
- If the camera won't open, check your camera device index (0 by default) and that no other app is using the camera.

If you want, I can:
- add a small CLI wrapper to tune thresholds and mode timings
- add automated tests for encoder and upload scripts
- further improve UI layout and add a packaged executable
