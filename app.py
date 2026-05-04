from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io
import os

app = Flask(__name__)
CORS(app)

def enhance_image(image, style="Normal"):
    img = np.array(image).astype(np.uint8)

    # 🔹 Basic safe enhancements
    img = cv2.convertScaleAbs(img, alpha=1.1, beta=10)

    # 🔹 Slight sharpening (safe)
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    img = cv2.filter2D(img, -1, kernel)

    # 🔹 Saturation boost
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    hsv[:,:,1] = np.clip(hsv[:,:,1] * 1.2, 0, 255)
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    # 🎨 Styles (SAFE)
    if style == "Cinematic":
        img[:,:,2] = np.clip(img[:,:,2] * 1.1, 0, 255)

    elif style == "Warm":
        img[:,:,0] = np.clip(img[:,:,0] * 1.1, 0, 255)

    elif style == "Cool":
        img[:,:,2] = np.clip(img[:,:,2] * 1.1, 0, 255)

    elif style == "Sharp Pro":
        img = cv2.GaussianBlur(img, (0,0), 1)
        img = cv2.addWeighted(img, 1.5, img, -0.5, 0)

    # 🔥 SAFE UPSCALE (limit size)
    h, w = img.shape[:2]

    if w < 1280:
        scale = 1280 / w
        new_w = int(w * scale)
        new_h = int(h * scale)

        # limit max size (important for Render)
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

        image = Image.open(file).convert("RGB")

        enhanced = enhance_image(image, style)

        output = Image.fromarray(enhanced.astype(np.uint8))

        img_io = io.BytesIO()
        output.save(img_io, format='JPEG', quality=90)
        img_io.seek(0)

        return send_file(img_io, mimetype='image/jpeg')

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
