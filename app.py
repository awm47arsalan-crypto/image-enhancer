from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io
import os

app = Flask(__name__)
CORS(app)

# 🎬 Cinematic grading
def cinematic_grade(img):
    img = img.astype(np.float32) / 255.0

    # S-curve contrast
    img = np.clip((img - 0.5) * 1.2 + 0.5, 0, 1)

    r, g, b = cv2.split(img)

    r *= 1.08
    b *= 0.92
    g *= 1.02

    img = cv2.merge((r, g, b))

    # shadows cool, highlights warm
    shadow_mask = img < 0.4
    highlight_mask = img > 0.6

    img[shadow_mask] *= [0.95, 1.0, 1.05]
    img[highlight_mask] *= [1.05, 1.02, 0.95]

    return np.clip(img * 255, 0, 255).astype(np.uint8)


# 🎨 LUT STYLE PRESETS
def apply_lut(img, lut_type):
    img = img.astype(np.float32)

    if lut_type == "Teal & Orange":
        img[:,:,0] *= 1.1   # red boost
        img[:,:,2] *= 0.9   # blue reduce

    elif lut_type == "Moody":
        img *= 0.85
        img[:,:,2] *= 1.1

    elif lut_type == "Vintage":
        img[:,:,0] *= 1.15
        img[:,:,1] *= 1.05
        img[:,:,2] *= 0.85

    elif lut_type == "Cool Film":
        img[:,:,2] *= 1.15
        img[:,:,0] *= 0.9

    return np.clip(img, 0, 255).astype(np.uint8)


def enhance_image(image, style="Normal", lut="None"):
    img = np.array(image).astype(np.uint8)

    # 🔹 Base correction
    img = cv2.convertScaleAbs(img, alpha=1.05, beta=8)

    # 🔹 Sharpen
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    img = cv2.filter2D(img, -1, kernel)

    # 🔹 Saturation
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    hsv[:,:,1] = np.clip(hsv[:,:,1] * 1.15, 0, 255)
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    # 🎬 Style
    if style == "Cinematic":
        img = cinematic_grade(img)

    elif style == "Warm":
        img[:,:,0] = np.clip(img[:,:,0] * 1.1, 0, 255)

    elif style == "Cool":
        img[:,:,2] = np.clip(img[:,:,2] * 1.1, 0, 255)

    elif style == "Sharp Pro":
        blur = cv2.GaussianBlur(img, (0,0), 1)
        img = cv2.addWeighted(img, 1.5, blur, -0.5, 0)

    # 🎨 LUT apply
    if lut != "None":
        img = apply_lut(img, lut)

    # 🔥 Safe upscale
    h, w = img.shape[:2]
    if w < 1280:
        scale = 1280 / w
        new_w = int(w * scale)
        new_h = int(h * scale)

        if new_w <= 1920 and new_h <= 1920:
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    return img


@app.route('/')
def home():
    return "App is running 🔥"


@app.route('/enhance', methods=['POST'])
def enhance():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        file = request.files['image']
        style = request.form.get("style", "Normal")
        lut = request.form.get("lut", "None")

        image = Image.open(file).convert("RGB")

        enhanced = enhance_image(image, style, lut)

        output = Image.fromarray(enhanced.astype(np.uint8))

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
