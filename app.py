from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import io
import os

app = Flask(__name__)
CORS(app)

# 🎬 Cinematic tone curve + highlight/shadow balance
def cinematic_grade(img):
    img = np.array(img).astype(np.float32) / 255.0

    # S-curve contrast
    img = (img - 0.5) * 1.25 + 0.5
    img = np.clip(img, 0, 1)

    r, g, b = img[:,:,0], img[:,:,1], img[:,:,2]

    # 🎨 Teal shadows, warm highlights
    shadows = img < 0.4
    highlights = img > 0.6

    img[shadows] *= [0.95, 1.0, 1.05]
    img[highlights] *= [1.05, 1.02, 0.95]

    # 🔥 Skin tone protect (avoid too much red)
    r = np.clip(r * 1.06, 0, 1)
    g = np.clip(g * 1.02, 0, 1)
    b = np.clip(b * 0.95, 0, 1)

    img = np.stack([r, g, b], axis=2)

    return Image.fromarray((img * 255).astype(np.uint8))


# 🎨 LUT-style presets (film looks)
def apply_lut(img, lut):
    img = np.array(img).astype(np.float32)

    if lut == "Teal & Orange":
        img[:,:,0] *= 1.08
        img[:,:,2] *= 0.9

    elif lut == "Moody":
        img *= 0.85
        img[:,:,2] *= 1.1

    elif lut == "Vintage":
        img[:,:,0] *= 1.15
        img[:,:,1] *= 1.05
        img[:,:,2] *= 0.85

    elif lut == "Cool Film":
        img[:,:,2] *= 1.12
        img[:,:,0] *= 0.92

    elif lut == "Soft Skin":
        img[:,:,0] *= 1.03
        img[:,:,1] *= 1.02
        img = np.clip(img * 1.02, 0, 255)

    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def enhance_image(image, style="Normal", lut="None"):

    # 🔥 STEP 1: resize first (VERY IMPORTANT)
    max_size = 2160
    w, h = image.size

    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        image = image.resize((int(w*scale), int(h*scale)), Image.LANCZOS)

    # 🔹 Base enhancement (lightweight)
    image = ImageEnhance.Brightness(image).enhance(1.05)
    image = ImageEnhance.Contrast(image).enhance(1.1)
    image = ImageEnhance.Color(image).enhance(1.08)
    image = ImageEnhance.Sharpness(image).enhance(1.1)

    # 🎬 Cinematic (NO heavy full numpy)
    if style == "Cinematic":
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=120))

    # 🎨 LUT (lightweight)
    if lut == "Warm":
        r, g, b = image.split()
        r = r.point(lambda i: i * 1.05)
        image = Image.merge("RGB", (r, g, b))

    elif lut == "Cool":
        r, g, b = image.split()
        b = b.point(lambda i: i * 1.05)
        image = Image.merge("RGB", (r, g, b))

    elif lut == "Vintage":
        r, g, b = image.split()
        r = r.point(lambda i: i * 1.1)
        b = b.point(lambda i: i * 0.9)
        image = Image.merge("RGB", (r, g, b))

    # ❌ UPSCALE DISABLED (memory killer)
    # (baad me add karenge smarter way)

    return image
    # 🎨 LUT apply
    if lut != "None":
        image = apply_lut(image, lut)

    # 📏 Smart upscale (safe)
    w, h = image.size
    if w < 1280:
        scale = 1280 / w
        new_w = int(w * scale)
        new_h = int(h * scale)

        if new_w <= 1920 and new_h <= 1920:
            image = image.resize((new_w, new_h), Image.LANCZOS)

    return image


@app.route('/')
def home():
    return "Backend running 🔥"


@app.route('/enhance', methods=['POST'])
def enhance():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        file = request.files['image']
        style = request.form.get("style", "Normal")
        lut = request.form.get("lut", "None")

       image = Image.open(file.stream)
original_format = image.format if image.format else "JPEG"
image = image.convert("RGB")

        output = enhance_image(image, style, lut)

       img_io = BytesIO()

save_format = "PNG" if str(original_format).upper() == "PNG" else "JPEG"

if save_format == "PNG":
    output.save(img_io, format="PNG")
    mimetype = "image/png"
else:
    output.save(
        img_io,
        format="JPEG",
        quality=100,
        optimize=False,
        subsampling=0
    )
    mimetype = "image/jpeg"

img_io.seek(0)

return send_file(
    img_io,
    mimetype=mimetype,
    as_attachment=False
)

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
