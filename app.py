from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io
import os

app = Flask(__name__)
CORS(app)

# 🚀 MAIN ENHANCER (SAFE VERSION)
def enhance_image(image, style="Normal"):
    img = np.array(image).astype(np.uint8)

    # Basic brightness + contrast
    img = cv2.convertScaleAbs(img, alpha=1.1, beta=10)

    # Saturation boost
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    hsv[:,:,1] = np.clip(hsv[:,:,1] * 1.2, 0, 255)
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    # Styles
    if style == "Cinematic":
        rows, cols = img.shape[:2]
        mask = np.zeros((rows, cols), np.float32)
        cv2.circle(mask, (cols//2, rows//2), min(rows, cols)//2, 1, -1)
        mask = cv2.GaussianBlur(mask, (101,101), 0)
        for i in range(3):
            img[:,:,i] = img[:,:,i] * mask

    elif style == "Sharp Pro":
        kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
        img = cv2.filter2D(img, -1, kernel)

    elif style == "Warm":
        img[:,:,0] = np.clip(img[:,:,0] * 1.1, 0, 255)

    return np.clip(img, 0, 255).astype(np.uint8)


# 🏠 HEALTH CHECK
@app.route('/')
def home():
    return "App is running 🔥"


# 📸 API
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
