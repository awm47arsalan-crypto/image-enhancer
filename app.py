from flask import Flask, request, send_file
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io
import os

app = Flask(__name__)
CORS(app)  # 🔥 CORS fix

# 🔥 Image enhancement function
def enhance_image(image):
    img = np.array(image)

    # brightness + contrast
    img = cv2.convertScaleAbs(img, alpha=1.2, beta=20)

    # saturation boost
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.3, 0, 255)
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    return img

# 🏠 Home route (test ke liye)
@app.route('/')
def home():
    return "App is running 🔥"

# 🚀 Enhance API
@app.route('/enhance', methods=['POST'])
def enhance():
    if 'image' not in request.files:
        return {"error": "No image uploaded"}, 400

    file = request.files['image']
    image = Image.open(file).convert("RGB")

    enhanced = enhance_image(image)

    img_io = io.BytesIO()
    Image.fromarray(enhanced).save(img_io, 'JPEG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

# 🔥 Render compatible run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
