from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io
import os

app = Flask(__name__)
CORS(app)

# 🔥 MAIN ENHANCER
def enhance_image(image, style="Normal"):
    img = np.array(image).astype(np.uint8)

    # 🔹 Denoise (blur reduce lite)
    img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    # 🔹 Sharpen
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    img = cv2.filter2D(img, -1, kernel)

    # 🔹 Contrast enhancement (CLAHE)
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)

    lab = cv2.merge((l,a,b))
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    # 🔹 Color boost
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    hsv[:,:,1] = np.clip(hsv[:,:,1] * 1.25, 0, 255)
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    # 🎨 Styles
    if style == "Cinematic":
        img[:,:,2] = np.clip(img[:,:,2] * 1.2, 0, 255)

    elif style == "Warm":
        img[:,:,0] = np.clip(img[:,:,0] * 1.15, 0, 255)

    elif style == "Cool":
        img[:,:,2] = np.clip(img[:,:,2] * 1.15, 0, 255)

    elif style == "Sharp Pro":
        img = cv2.detailEnhance(img, sigma_s=10, sigma_r=0.15)

    # 🔥 Upscale to near 1080p
    h, w = img.shape[:2]
    scale = max(1920 / w, 1080 / h)
    if scale > 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    return np.clip(img, 0, 255).astype(np.uint8)


# 🏠 HEALTH CHECK
@app.route('/')
def home():
    return "App is running 🔥"


# 📸 ENHANCE API
@app.route('/enhance', methods=['POST'])
def enhance():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    style = request.form.get("style", "Normal")

    try:
        image = Image.open(file).convert("RGB")

        enhanced = enhance_image(image, style)

        output = Image.fromarray(enhanced)

        img_io = io.BytesIO()
        output.save(img_io, format='JPEG', quality=95)
        img_io.seek(0)

        return send_file(img_io, mimetype='image/jpeg')

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


# 🚀 RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
