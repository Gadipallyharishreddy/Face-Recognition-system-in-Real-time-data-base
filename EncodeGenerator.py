import os
import pickle
import cv2
import face_recognition

try:
    BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE = os.getcwd()

IMAGES_DIR = os.path.join(BASE, "Images")
ENC_FILE = os.path.join(BASE, "EncodeFile.p")

def collect_images(images_dir):
    files = []
    if not os.path.isdir(images_dir):
        print(f"Images folder not found: {images_dir}")
        return files
    for fname in os.listdir(images_dir):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            files.append(os.path.join(images_dir, fname))
    return sorted(files)

def find_encodings(image_paths):
    encodings = []
    ids = []
    for p in image_paths:
        img = cv2.imread(p)
        if img is None:
            print(f"Warning: could not read image {p}, skipping")
            continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_encs = face_recognition.face_encodings(rgb)
        if not face_encs:
            print(f"Warning: no face found in {p}, skipping")
            continue
        encodings.append(face_encs[0])
        ids.append(os.path.splitext(os.path.basename(p))[0])
    return encodings, ids

def main():
    print("Scanning Images folder for files...")
    images = collect_images(IMAGES_DIR)
    if not images:
        print("No images found. Place images in the Images/ folder named <id>.jpeg")
        return
    print(f"Found {len(images)} images. Encoding...")
    encs, ids = find_encodings(images)
    print(f"Encodings generated: {len(encs)} (skipped {len(images)-len(encs)} images)")
    with open(ENC_FILE, 'wb') as f:
        pickle.dump((encs, ids), f)
    print(f"Saved encodings to {ENC_FILE}")

if __name__ == '__main__':
    main()