from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import io
import os

app = Flask(__name__)
CORS(app)

# 🎬 Cinematic Tone Curve
def cinematic_tone(img):
    img = np.array(img).astype(np.float32) / 255.0

    # S-curve contrast
    img = (img - 0.5) * 1.3 + 0.5
    img = np.clip(img, 0, 1)

    # Teal-Orange
    r = img[:,:,0] * 1.08
    g = img[:,:,1] * 1.02
    b = img[:,:,2] * 0.92

    img = np.stack([r,g,b], axis=2)

    return Image.fromarray((img * 255).astype(np.uint8))


# 🎨 LUT presets (fast)
def apply_lut(img, lut):
    img = np.array(img).astype(np.float32)

    if lut == "Teal & Orange":
        img[:,:,0] *= 1.1
        img[:,:,2] *= 0.9

    elif lut == "Moody":
        img *= 0.85
        img[:,:,2] *= 1.1

    elif lut == "Vintage":
        img[:,:,0] *= 1.15
        img[:,:,1] *= 1.05
        img[:,:,2] *= 0.85

    elif lut == "Cool Film":
        img[:,:,2] *= 1.15
        img[:,:,0] *= 0.9

    return Image.fromarray(np.clip(img,0,255).astype(np.uint8))


def enhance_image(image, style="Normal", lut="None"):

    # 🔹 Base Enhancements (FAST)
    image = ImageEnhance.Brightness(image).enhance(1.08)
    image = ImageEnhance.Contrast(image).enhance(1.15)
    image = ImageEnhance.Sharpness(image).enhance(1.2)
    image = ImageEnhance.Color(image).enhance(1.1)

    # 🔹 Slight clarity
    image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=120))

    # 🎬 Style
    if style == "Cinematic":
        image = cinematic_tone(image)

    elif style == "Warm":
        r, g, b = image.split()
        r = r.point(lambda i: i * 1.1)
        image = Image.merge("RGB", (r, g, b))

    elif style == "Cool":
        r, g, b = image.split()
        b = b.point(lambda i: i * 1.1)
        image = Image.merge("RGB", (r, g, b))

    elif style == "Sharp Pro":
        image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150))

    # 🎨 LUT
    if lut != "None":
        image = apply_lut(image, lut)

    # 📏 SAFE UPSCALE
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

        image = Image.open(file).convert("RGB")

        output = enhance_image(image, style, lut)

        img_io = io.BytesIO()
        output.save(img_io, format='JPEG', quality=92)
        img_io.seek(0)

        return send_file(img_io, mimetype='image/jpeg')

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
