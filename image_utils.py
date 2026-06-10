import os
import shutil
import uuid

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


def app_root():
    return os.path.dirname(os.path.abspath(__file__))


def dresses_images_dir():
    path = os.path.join(app_root(), "images", "dresses")
    os.makedirs(path, exist_ok=True)
    return path


def resolve_image_path(relative_path):
    if not relative_path:
        return None
    full = os.path.join(app_root(), relative_path.replace("/", os.sep))
    return full if os.path.isfile(full) else None


def save_dress_image(source_path, dress_id, dress_code):
    ext = os.path.splitext(source_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"
    safe_code = "".join(c if c.isalnum() or c in "-_" else "_" for c in dress_code)
    fname = f"{safe_code}_{dress_id}_{uuid.uuid4().hex[:8]}{ext}"
    dest = os.path.join(dresses_images_dir(), fname)
    shutil.copy2(source_path, dest)
    return os.path.join("images", "dresses", fname).replace("\\", "/")


def delete_dress_image(relative_path):
    full = resolve_image_path(relative_path)
    if full:
        try:
            os.remove(full)
        except OSError:
            pass
