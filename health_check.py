"""
Health check script — validates the workspace has the required resources.
Run: python health_check.py
It checks for:
 - Resources/serviceAccountKey.json
 - Resources/Modes contains 1.png..4.png (or at least some images)
 - Images/ exists and has at least one image
 - EncodeFile.p exists (optional: recommended for local mode)
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

checks = []

# service key
svc = os.path.join(BASE, 'Resources', 'serviceAccountKey.json')
checks.append(('Firebase service account', svc, os.path.exists(svc)))

# modes folder
modes_dir = os.path.join(BASE, 'Resources', 'Modes')
modes_exist = os.path.isdir(modes_dir) and any(fname.lower().endswith(('.png','.jpg','.jpeg')) for fname in os.listdir(modes_dir))
checks.append(('Modes images (Resources/Modes)', modes_dir, modes_exist))

# images folder
images_dir = os.path.join(BASE, 'Images')
images_exist = os.path.isdir(images_dir) and any(fname.lower().endswith(('.png','.jpg','.jpeg')) for fname in os.listdir(images_dir))
checks.append(('Images folder', images_dir, images_exist))

# encode file
enc = os.path.join(BASE, 'EncodeFile.p')
checks.append(('EncodeFile.p', enc, os.path.exists(enc)))

# background
bg = os.path.join(BASE, 'Resources', 'background.png')
checks.append(('Background image', bg, os.path.exists(bg)))

print('Health check — project path:', BASE)
ok = True
for name, path, result in checks:
    print(f"- {name}: {path} -> {'OK' if result else 'MISSING'}")
    if not result:
        ok = False

if ok:
    print('\nAll checks passed — project looks ready to run.')
else:
    print('\nSome items are missing. See above for details.')
    print('If you plan to use Firestore-backed mode, ensure the service account file exists and you have network access.')
