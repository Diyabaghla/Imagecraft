import os
import uuid
import cv2
from flask import Blueprint, render_template, request, redirect, send_file, current_app
from werkzeug.utils import secure_filename

cartoon_bp = Blueprint(
    "cartoonify", __name__,
    template_folder="templates",   # ensure your template folder is named 'templates'
    static_folder="static"
)

# Save uploads inside static/uploads
UPLOAD_SUBFOLDER = "uploads"
UPLOAD_FOLDER = os.path.join(cartoon_bp.static_folder, UPLOAD_SUBFOLDER)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def cartoonify_image(in_path, out_path):
    img = cv2.imread(in_path)
    if img is None:
        return None
    img_color = cv2.bilateralFilter(img, 9, 75, 75)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.medianBlur(img_gray, 5)
    edges = cv2.adaptiveThreshold(img_blur, 255,
                                  cv2.ADAPTIVE_THRESH_MEAN_C,
                                  cv2.THRESH_BINARY, 9, 2)
    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cartoon = cv2.bitwise_and(img_color, edges_colored)
    cv2.imwrite(out_path, cartoon)
    return out_path


@cartoon_bp.route("/cartoonify", methods=["GET", "POST"])
def cartoonify():
    if request.method == "POST":
        if "image" not in request.files:
            return redirect(request.url)

        file = request.files["image"]
        if file.filename == "":
            return redirect(request.url)

        # secure filename and save original
        original_name = secure_filename(file.filename)
        # ensure unique filenames to avoid clashes
        base_name = os.path.splitext(original_name)[0]
        ext = os.path.splitext(original_name)[1] or ".png"

        unique_orig = f"{base_name}_{uuid.uuid4().hex}{ext}"
        orig_fs_path = os.path.join(UPLOAD_FOLDER, unique_orig)
        file.save(orig_fs_path)

        # create cartoonified filename
        cartoon_filename = f"{base_name}_cartoon_{uuid.uuid4().hex}.png"
        cartoon_fs_path = os.path.join(UPLOAD_FOLDER, cartoon_filename)

        # process
        cartoonify_image(orig_fs_path, cartoon_fs_path)

        # pass **relative static paths** to template (no leading slash)
        original_rel = f"{UPLOAD_SUBFOLDER}/{unique_orig}"
        cartoon_rel = f"{UPLOAD_SUBFOLDER}/{cartoon_filename}"

        return render_template(
            "cartoonify_result.html",
            original=original_rel,
            cartoon=cartoon_rel,
            cartoon_filename=cartoon_filename
        )

    # GET
    return render_template("cartoonify_index.html")


@cartoon_bp.route("/cartoonify/download/<filename>")
def download(filename):
    # filename is the file name inside uploads, sent from template
    safe_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(safe_path):
        return "File not found.", 404
    return send_file(safe_path, as_attachment=True)
