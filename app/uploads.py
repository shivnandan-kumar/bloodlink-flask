from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename


ALLOWED_PRESCRIPTION_TYPES = {
    ".pdf": (b"%PDF-",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
}


class UploadValidationError(ValueError):
    pass


def prescription_upload_directory():
    return Path(current_app.instance_path) / "uploads" / "prescriptions"


def save_prescription(file_storage):
    if not file_storage or not file_storage.filename:
        raise UploadValidationError("Doctor prescription is required.")

    original_name = secure_filename(file_storage.filename)
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_PRESCRIPTION_TYPES:
        raise UploadValidationError("Prescription must be a PDF, JPG or PNG file.")

    file_storage.stream.seek(0, 2)
    file_size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if file_size == 0:
        raise UploadValidationError("Prescription file cannot be empty.")
    if file_size > current_app.config["PRESCRIPTION_MAX_SIZE"]:
        raise UploadValidationError("Prescription file must be 5 MB or smaller.")

    header = file_storage.stream.read(8)
    file_storage.stream.seek(0)
    if not any(header.startswith(signature) for signature in ALLOWED_PRESCRIPTION_TYPES[extension]):
        raise UploadValidationError("The selected file does not match its file type.")

    directory = prescription_upload_directory()
    directory.mkdir(parents=True, exist_ok=True)
    saved_name = f"{uuid4().hex}{extension}"
    file_storage.save(directory / saved_name)
    return saved_name, original_name


def delete_prescription(saved_name):
    if not saved_name:
        return
    file_path = prescription_upload_directory() / Path(saved_name).name
    if file_path.is_file():
        file_path.unlink()
