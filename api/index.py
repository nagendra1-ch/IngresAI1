import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

candidates = [
    os.path.join(root_dir, "backend"),
    os.path.join(current_dir, "backend"),
    root_dir,
    current_dir
]

for p in candidates:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from app.main import app
