import os
import cv2
import base64
import numpy as np
from io import BytesIO
from PIL import Image
from flask import Blueprint, render_template, request

# Create Blueprint
sketch_bp = Blueprint(
    "sketch", __name__,
    template_folder="templates",   # make sure folder name is lowercase
    static_folder="static"
)

UPLOAD_FOLDER = os.path.join(sketch_bp.static_folder, "sketches")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Helper Functions ----------------
def image_to_base64(img_pil, format="JPEG"):
    buf = BytesIO()
    img_pil.save(buf, format=format)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def create_pencil_sketch(img_stream, intensity=101, color_mode="gray"):
    file_bytes = np.frombuffer(img_stream.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    inverted = 255 - gray
    blurred = cv2.GaussianBlur(inverted, (intensity, intensity), 0)
    inverted_blur = 255 - blurred
    sketch = cv2.divide(gray, inverted_blur, scale=256.0)

    if color_mode == "color":
        sketch_rgb = cv2.merge([sketch, sketch, sketch])
    else:
        sketch_rgb = cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB)

    original_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    original_pil = Image.fromarray(original_rgb)
    sketch_pil = Image.fromarray(sketch_rgb)

    # Save sketch to disk for download
    filename = f"sketch_{np.random.randint(10000)}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    sketch_pil.save(filepath, "JPEG")

    return (
        image_to_base64(original_pil),
        image_to_base64(sketch_pil),
        f"/static/sketches/{filename}",  # serve from static
    )

# ---------------- Routes ----------------
@sketch_bp.route("/sketch", methods=["GET", "POST"])
def sketch_home():
    if request.method == "POST":
        file = request.files.get("image")
        intensity = int(request.form.get("intensity", 101))
        color_mode = request.form.get("mode", "gray")

        if file and file.filename:
            original_b64, sketch_b64, download_url = create_pencil_sketch(
                file, intensity, color_mode
            )
            return render_template(
                "pencil_result.html",
                original=original_b64,
                sketch=sketch_b64,
                download_url=download_url,
            )
    return render_template("pencil_index.html")
