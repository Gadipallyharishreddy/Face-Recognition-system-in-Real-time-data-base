import os
import sys
import time
from datetime import datetime
import cv2
import numpy as np
import face_recognition
import firebase_admin
from firebase_admin import credentials, firestore

# ---------------- CONFIG ----------------
try:
    BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE = os.getcwd()

SERVICE_KEY = os.path.join(BASE, "Resources", "serviceAccountKey.json")
COOLDOWN_SECONDS = 10
DISTANCE_THRESHOLD = 0.50
WEB_W, WEB_H = 640, 480
SCALE = 0.25

IMAGES_FOLDER = os.path.join(os.path.dirname(BASE), "Images")
MODES_FOLDER = os.path.join(BASE, "Resources", "modes")

CANVAS_W, CANVAS_H = 1100, 620
LEFT_X, LEFT_Y = 25, 126
LEFT_W, LEFT_H = 590, 440
PANEL_BORDER = 12

PURPLE = (255, 170, 210)

NO_FACE_TIMEOUT = 6.0
MULTI_FACE_TIMEOUT = 3.0

MODE_FILES = {
    "ACTIVE": os.path.join(MODES_FOLDER, "1.png"),
    "FETCHING": os.path.join(MODES_FOLDER, "2.png"),
    "MARKED": os.path.join(MODES_FOLDER, "3.png"),
    "ALREADY_MARKED": os.path.join(MODES_FOLDER, "4.png")
}
# ----------------------------------------

# --- Firestore init ---
if not os.path.exists(SERVICE_KEY):
    print("ERROR: serviceAccountKey.json not found at:", SERVICE_KEY)
    sys.exit(1)

try:
    cred = credentials.Certificate(SERVICE_KEY)
    firebase_admin.initialize_app(cred)
    fs = firestore.client()
except Exception as e:
    print("Failed to initialize Firebase. Error:", e)
    sys.exit(1)

# --- Load known encodings + metadata ---
print("Loading encodings from Firestore...")
known_encodings, known_ids = [], []
try:
    for doc in fs.collection("FaceEncodings").stream():
        d = doc.to_dict()
        if "encoding" in d:
            known_encodings.append(np.array(d["encoding"], dtype=np.float64))
            known_ids.append(doc.id)
except Exception as e:
    print("Warning: failed to read FaceEncodings:", e)
print("Encodings loaded:", known_ids)

students_meta = {}
try:
    for doc in fs.collection("Students").stream():
        students_meta[doc.id] = doc.to_dict()
except Exception as e:
    print("Warning: couldn't load Students collection:", e)
print("Student metadata loaded for:", list(students_meta.keys()))

# --- Background ---
BG_PATH = os.path.join(BASE, "Resources", "background.png")
if os.path.exists(BG_PATH):
    bg_original = cv2.imread(BG_PATH)
    bg = cv2.resize(bg_original, (CANVAS_W, CANVAS_H)) if bg_original is not None else np.full((CANVAS_H, CANVAS_W, 3), 255, np.uint8)
else:
    print("background.png not found. Using fallback.")
    bg = np.full((CANVAS_H, CANVAS_W, 3), 255, np.uint8)
    cv2.rectangle(bg, (CANVAS_W//2 + 50, 0), (CANVAS_W, CANVAS_H), PURPLE, cv2.FILLED)
    cv2.putText(bg, "ATTENDANCE SYSTEM", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

# --- Mode Images ---
mode_images = {}
for key, path in MODE_FILES.items():
    if os.path.exists(path):
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is None:
            img = np.full((150, 450, 3), 230, np.uint8)
        target_w = 420
        h = int(img.shape[0] * (target_w / img.shape[1]))
        mode_images[key] = cv2.resize(img, (target_w, h))
    else:
        mode_images[key] = np.full((150, 420, 3), 230, np.uint8)

# --- Helper functions ---
def overlay_image(canvas, img, cx, cy):
    h, w = img.shape[:2]
    x1, y1 = max(int(cx - w//2), 0), max(int(cy - h//2), 0)
    x2, y2 = min(x1 + w, canvas.shape[1]), min(y1 + h, canvas.shape[0])
    src = img[:y2-y1, :x2-x1]
    dst = canvas[y1:y2, x1:x2]
    if src.shape[2] == 4:
        alpha = src[:, :, 3] / 255.0
        for c in range(3):
            dst[:, :, c] = (alpha * src[:, :, c] + (1 - alpha) * dst[:, :, c]).astype(np.uint8)
    else:
        dst[:] = src
    return canvas

def draw_info_block(canvas, info_lines, x, y, w=360, h=140):
    cv2.rectangle(canvas, (x, y), (x + w, y + h), (245, 245, 245), cv2.FILLED)
    cv2.rectangle(canvas, (x, y), (x + w, y + h), (200, 200, 200), 1)
    yy = y + 25
    for line in info_lines:
        cv2.putText(canvas, line, (x+12, yy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40,40,40), 1)
        yy += 28

# 🆕 New function — overlay text on image
def overlay_student_info(image, name, student_id, major):
    """Overlay name, ID, and major on student photo."""
    if image is None:
        return None
    overlay = image.copy()
    h, w = image.shape[:2]
    line1 = name
    line2 = f"ID: {student_id} | {major}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.4, w / 400.0)
    thickness = 1
    (t1_w, t1_h), _ = cv2.getTextSize(line1, font, font_scale, thickness)
    (t2_w, t2_h), _ = cv2.getTextSize(line2, font, font_scale * 0.9, thickness)
    margin = 5
    y2 = h - margin
    y1 = y2 - t1_h - t2_h - margin * 2
    cv2.rectangle(overlay, (0, y1 - 5), (w, h), (0, 0, 0), -1)
    image = cv2.addWeighted(overlay, 0.5, image, 0.5, 0)
    cv2.putText(image, line1, (10, y2 - t2_h - 5), font, font_scale, (255, 255, 255), thickness + 1, cv2.LINE_AA)
    cv2.putText(image, line2, (10, y2), font, font_scale * 0.9, (200, 200, 200), thickness, cv2.LINE_AA)
    return image

# --- Camera math ---
inner_x, inner_y = LEFT_X + PANEL_BORDER, LEFT_Y + PANEL_BORDER
inner_w, inner_h = LEFT_W - PANEL_BORDER*2, LEFT_H - PANEL_BORDER*2
scale_w, scale_h = inner_w / WEB_W, inner_h / WEB_H
cam_scale = min(scale_w, scale_h)
new_cam_w, new_cam_h = int(WEB_W * cam_scale), int(WEB_H * cam_scale)
cam_offset_x, cam_offset_y = inner_x + (inner_w - new_cam_w)//2, inner_y + (inner_h - new_cam_h)//2

print(f"Canvas {CANVAS_W}x{CANVAS_H}, camera target {new_cam_w}x{new_cam_h}")

# --- Webcam ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    sys.exit(1)
cap.set(3, WEB_W)
cap.set(4, WEB_H)

last_seen = {}
no_face_since = None
multi_face_since = None

def mark_attendance(student_id):
    doc_ref = fs.collection("Students").document(student_id)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        doc_ref.update({
            "last_seen": now_str,
            "attendance_count": firestore.Increment(1)
        })
    except Exception:
        doc = doc_ref.get()
        base = doc.to_dict() if doc.exists else {}
        base.update({"last_seen": now_str, "attendance_count": base.get("attendance_count", 0) + 1})
        doc_ref.set(base)
    print(f"[{now_str}] attendance marked: {student_id}")

def draw_label(frame, text, x, y, w=150, h=25):
    cv2.rectangle(frame, (x-2, y-20), (x+w, y), (0,0,0), cv2.FILLED)
    cv2.putText(frame, text, (x+2, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)

# --- Main Loop ---
current_mode = "ACTIVE"
mode_display_until = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.03)
            continue

        small = cv2.resize(frame, (0,0), fx=SCALE, fy=SCALE)
        small_rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(small_rgb)
        encodings = face_recognition.face_encodings(small_rgb, locations)

        canvas = bg.copy()
        cam_resized = cv2.resize(frame, (new_cam_w, new_cam_h))
        canvas[cam_offset_y:cam_offset_y + new_cam_h, cam_offset_x:cam_offset_x + new_cam_w] = cam_resized

        faces_count = len(encodings)
        now_ts = time.time()

        # Timeout checks
        if faces_count == 0:
            if no_face_since is None:
                no_face_since = now_ts
            if multi_face_since is not None:
                multi_face_since = None
            if now_ts - no_face_since >= NO_FACE_TIMEOUT:
                print("No face timeout.")
                break
        elif faces_count > 1:
            if multi_face_since is None:
                multi_face_since = now_ts
            if no_face_since is not None:
                no_face_since = None
            if now_ts - multi_face_since >= MULTI_FACE_TIMEOUT:
                print("Multiple faces timeout.")
                break
        else:
            no_face_since = None
            multi_face_since = None

        if faces_count == 1 and encodings:
            enc = encodings[0]
            if known_encodings:
                dists = face_recognition.face_distance(known_encodings, enc)
                best_idx = np.argmin(dists)
                best_dist = float(dists[best_idx])
                top, right, bottom, left = locations[0]
                top, right, bottom, left = [int(v / SCALE) for v in (top, right, bottom, left)]
                c_left = cam_offset_x + int(left * (new_cam_w / WEB_W))
                c_right = cam_offset_x + int(right * (new_cam_w / WEB_W))
                c_top = cam_offset_y + int(top * (new_cam_h / WEB_H))
                c_bottom = cam_offset_y + int(bottom * (new_cam_h / WEB_H))

                if best_dist <= DISTANCE_THRESHOLD:
                    sid = known_ids[best_idx]
                    meta = students_meta.get(sid, {})
                    name, major = meta.get("name", sid), meta.get("major", "")
                    cv2.rectangle(canvas, (c_left, c_top), (c_right, c_bottom), (0,255,0), 2)
                    draw_label(canvas, f"{name} ({major})", c_left, c_top)

                    current_mode = "FETCHING"
                    mode_display_until = now_ts + 1.2

                    img_path = meta.get("image_filename") or os.path.join("Images", f"{sid}.jpeg")
                    local_path = os.path.join(os.path.dirname(BASE), img_path)
                    if os.path.exists(local_path):
                        try:
                            thumb = cv2.imread(local_path)
                            thumb = cv2.resize(thumb, (120, 120))
                            thumb = overlay_student_info(thumb, meta.get("name", "-"), sid, meta.get("major", "-"))
                            tx1, ty1 = cam_offset_x + new_cam_w - 130, cam_offset_y + 10
                            canvas[ty1:ty1+120, tx1:tx1+120] = thumb
                        except Exception:
                            pass

                    info_lines = [
                        f"Name: {meta.get('name','-')}",
                        f"ID: {sid}",
                        f"Major: {meta.get('major','-')}",
                        f"Year: {meta.get('year','-')}",
                        f"Starting Year: {meta.get('starting_year','-')}",
                        f"Last Attendance: {meta.get('last_seen','-')}"
                    ]
                    draw_info_block(canvas, info_lines, CANVAS_W - 460, 120, w=420, h=180)

                    if now_ts - last_seen.get(sid, 0) >= COOLDOWN_SECONDS:
                        last_seen[sid] = now_ts
                        mark_attendance(sid)
                        current_mode = "MARKED"
                        mode_display_until = now_ts + 1.6
                    else:
                        current_mode = "ALREADY_MARKED"
                        mode_display_until = now_ts + 1.6
                else:
                    current_mode = "ACTIVE"
                    cv2.rectangle(canvas, (c_left, c_top), (c_right, c_bottom), (0,0,255), 2)
                    draw_label(canvas, "Unknown", c_left, c_top)
            else:
                draw_label(canvas, "No encodings loaded", cam_offset_x+10, cam_offset_y+20)
                current_mode = "ACTIVE"
        else:
            if mode_display_until <= now_ts:
                current_mode = "ACTIVE"

        # Mode overlay
        mode_to_show = current_mode if mode_display_until > now_ts else "ACTIVE"
        mode_img = mode_images.get(mode_to_show, mode_images["ACTIVE"])
        mode_resized = cv2.resize(mode_img, (400, 600))
        if mode_resized.shape[2] == 4:
            mode_resized = cv2.cvtColor(mode_resized, cv2.COLOR_BGRA2BGR)
        y1, y2, x1, x2 = 10, 610, 670, 1070
        region = canvas[y1:y2, x1:x2]
        mode_resized = cv2.resize(mode_resized, (region.shape[1], region.shape[0]))
        canvas[y1:y2, x1:x2] = cv2.addWeighted(region, 0.4, mode_resized, 0.6, 0)

        # Display
        cv2.imshow("Face Attendance (UI Modes)", canvas)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Manual quit.")
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Cleaned up and exited.")





    
