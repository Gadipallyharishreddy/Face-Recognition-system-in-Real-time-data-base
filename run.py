"""
Simple runner for the project.
Usage:
  python run.py --mode local    # uses main.py (EncodeFile.p)
  python run.py --mode firestore # uses main_with_firestore.py

This wrapper is intentionally minimal. It launches the selected script as a subprocess
so that files and constants in each script remain unchanged.
"""
import argparse
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['local', 'firestore'], default='firestore', help='Which runtime to launch')
    p.add_argument('--script-args', nargs='*', help='Additional args passed to the script')
    args = p.parse_args()

    if args.mode == 'local':
        script = os.path.join(BASE, 'main.py')
    else:
        script = os.path.join(BASE, 'main_with_firestore.py')

    if not os.path.exists(script):
        print(f"Script not found: {script}")
        sys.exit(2)

    cmd = [sys.executable, script]
    if args.script_args:
        cmd.extend(args.script_args)

    print('Launching:', ' '.join(cmd))
    # run in the same console so cv2 windows appear
    rc = subprocess.call(cmd)
    print('Process exited with code', rc)

if __name__ == '__main__':
    main()
