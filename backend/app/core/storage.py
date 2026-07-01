"""
Handles saving uploaded files to local disk.
Abstracted into its own module so swapping to S3 later
only requires changing this file, not the routes.
"""
import uuid
import os
from fastapi import UploadFile

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


def save_upload(file: UploadFile) -> tuple[str, str]:
    """
    Saves an uploaded file to disk with a UUID filename to avoid collisions.
    Returns (file_path, file_type) tuple.
    """
    ext = file.filename.rsplit(".", 1)[-1].lower()
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path, ext