"""
app.py

Flask web app to remove image backgrounds using rembg + Pillow.
Features:
 - Upload a JPG/PNG/JPEG image via HTML form (or via API)
 - Background removal with rembg
 - Save result to static/outputs as PNG (transparent background)
 - View result in-browser and download as attachment
 - Basic input validation, filesize limit, and helpful error messages
 - All functions documented for maintainability

Usage:
    1. Activate your virtualenv
    2. pip install -r requirements.txt
    3. python app.py
    4. Open http://127.0.0.1:5000
"""

import os
import io
import uuid
import logging
from typing import Tuple

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    url_for,
    send_from_directory,
    send_file,
    abort,
)
from werkzeug.utils import secure_filename
from rembg import remove
from PIL import Image, UnidentifiedImageError

# ---------------------
# Configuration
# ---------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUTS_DIR = os.path.join(STATIC_DIR, "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max upload size (adjust if needed)

# Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["UPLOAD_FOLDER"] = OUTPUTS_DIR
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
# In production set a stable secret key; random one is OK for dev
app.secret_key = os.urandom(24)

# Setup basic logging to console for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------
# Helper functions
# ---------------------
def allowed_file(filename: str) -> bool:
    """
    Return True if the uploaded filename has an allowed image extension.
    """
    if not filename:
        return False
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename using UUID, while keeping a sanitized base.
    Output files are saved as .png (preserve transparency).
    """
    base = secure_filename(original_filename)
    # strip extension
    base_no_ext = base.rsplit(".", 1)[0]
    unique = f"{uuid.uuid4().hex}_{base_no_ext}.png"
    return unique


def process_image_bytes(input_bytes: bytes) -> bytes:
    """
    Given image bytes, run rembg.remove and return PNG bytes with alpha channel.
    This function verifies the input is a valid image with Pillow before calling rembg.
    Raises exceptions on invalid input or processing failure.
    """
    # Validate input bytes can be opened by Pillow
    try:
        with Image.open(io.BytesIO(input_bytes)) as img:
            img.verify()  # verify does not load full image but checks integrity
    except UnidentifiedImageError as e:
        raise ValueError("Uploaded file is not a valid image or is corrupted.") from e
    except Exception as e:
        raise ValueError("Failed to validate uploaded image.") from e

    # rembg.remove accepts bytes and returns bytes (PNG with alpha)
    try:
        output_bytes = remove(input_bytes)
        if not output_bytes:
            raise RuntimeError("rembg returned empty output.")
        return output_bytes
    except Exception as e:
        # Re-raise with clearer message
        raise RuntimeError(f"Background removal failed: {e}") from e


def save_bytes_to_file(b: bytes, path: str) -> None:
    """
    Write bytes to disk atomically (simple write). Raises on failure.
    """
    with open(path, "wb") as f:
        f.write(b)


# ---------------------
# Routes
# ---------------------
@app.route("/", methods=["GET"])
def index():
    """
    Render the main upload page (templates/index.html).
    The template handles client-side preview and AJAX upload.
    """
    return render_template("index.html")


@app.route("/remove", methods=["POST"])
def remove_background_api():
    """
    API endpoint to accept an image file under form field 'image'.
    Returns JSON containing:
        - success: bool
        - view_url: URL path to view the processed image (optional on success)
        - download_url: URL path to download the processed image (optional on success)
        - error: error message (on failure)
    This endpoint expects multipart/form-data.
    """
    # Basic validation: check that 'image' is present
    if "image" not in request.files:
        logger.debug("No 'image' field in request.files")
        return jsonify({"success": False, "error": "No file part in the request (field name 'image' missing)."}), 400

    file = request.files["image"]

    # Validate filename
    if file.filename == "":
        logger.debug("Empty filename in uploaded file")
        return jsonify({"success": False, "error": "No file selected."}), 400

    if not allowed_file(file.filename):
        logger.debug("File extension not allowed: %s", file.filename)
        return jsonify({
            "success": False,
            "error": "File type not allowed. Allowed extensions: png, jpg, jpeg."
        }), 400

    # Read file bytes (beware memory if very large files; MAX_CONTENT_LENGTH protects)
    try:
        input_bytes = file.read()
    except Exception as e:
        logger.exception("Failed to read uploaded file bytes")
        return jsonify({"success": False, "error": "Failed to read uploaded file."}), 500

    # Process image with rembg
    try:
        output_bytes = process_image_bytes(input_bytes)
    except ValueError as ve:
        logger.warning("Validation error: %s", ve)
        return jsonify({"success": False, "error": str(ve)}), 400
    except RuntimeError as re:
        logger.exception("Processing error: %s", re)
        return jsonify({"success": False, "error": str(re)}), 500
    except Exception as e:
        logger.exception("Unexpected error during processing")
        return jsonify({"success": False, "error": "Unexpected processing error."}), 500

    # Save file to outputs directory
    unique_name = generate_unique_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    try:
        save_bytes_to_file(output_bytes, save_path)
    except Exception as e:
        logger.exception("Failed to save output file")
        return jsonify({"success": False, "error": "Failed to save processed image."}), 500

    # Build URLs for view and download. view endpoint renders template with image (optional).
    view_url = url_for("view_image", filename=unique_name)
    download_url = url_for("download_image", filename=unique_name)

    logger.info("Processed image saved: %s", save_path)
    return jsonify({
        "success": True,
        "view_url": view_url,
        "download_url": download_url,
        "filename": unique_name
    }), 200


@app.route("/view/<path:filename>", methods=["GET"])
def view_image(filename: str):
    """
    Renders a page that displays the processed image inside a template.
    This endpoint verifies the file exists in the outputs folder before rendering.
    """
    safe_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.isfile(safe_path):
        logger.warning("Requested view for missing file: %s", safe_path)
        abort(404, description="File not found.")
    # The template will reference the static file under /static/outputs/<filename>
    img_url = f"/static/outputs/{filename}"
    return render_template("view.html", image_url=img_url, filename=filename)


@app.route("/download/<path:filename>", methods=["GET"])
def download_image(filename: str):
    """
    Serve the processed file as an attachment for download.
    Uses send_from_directory for safe serving.
    """
    safe_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.isfile(safe_path):
        logger.warning("Requested download for missing file: %s", safe_path)
        abort(404, description="File not found.")

    # send_from_directory will add appropriate headers for download
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


# Optional: route to retrieve raw bytes (useful for AJAX img src or direct embedding)
@app.route("/raw/<path:filename>", methods=["GET"])
def raw_image(filename: str):
    """
    Return image bytes directly (image/png). This can be used as an image src.
    Example URL: /raw/<filename>
    """
    safe_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.isfile(safe_path):
        abort(404, description="File not found.")
    return send_file(safe_path, mimetype="image/png")


# ---------------------
# Error handlers
# ---------------------
@app.errorhandler(413)
def request_entity_too_large(error):
    """
    Handle uploads larger than MAX_CONTENT_LENGTH.
    """
    msg = f"File is too large. Max file size is {MAX_CONTENT_LENGTH / (1024*1024)} MB."
    logger.warning("413: %s", msg)
    return jsonify({"success": False, "error": msg}), 413


@app.errorhandler(404)
def not_found(e):
    """
    Generic 404 handler (returns JSON for API calls or simple text).
    """
    # If AJAX/JS requested JSON, default to JSON; else a simple message
    return jsonify({"success": False, "error": getattr(e, 'description', 'Resource not found.')}), 404


# ---------------------
# App entrypoint
# ---------------------
if __name__ == "__main__":
    # Development server only. For production use a WSGI server (gunicorn/uvicorn/etc.)
    # Debug True is handy while developing, but turn off in production.
    app.run(host="0.0.0.0", port=5000, debug=True)
