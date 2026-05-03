from flask import Flask, request, send_file
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io
import os

app = Flask(__name__)
CORS(app)

# 🎬 Vignette
def apply_vignette(img):
    rows, cols = img.shape[:2]
    kernel_x = cv2.getGaussianKernel(cols, cols/2)
    kernel_y = cv2.getGaussianKernel(rows, rows/2)
    mask = kernel_y * kernel_x.T
    mask = mask / mask.max()

    for i in range(3):
        img[:,:,i] = img[:,:,i] * mask

    return img

# 🔪 Sharpen
def sharpen(img):
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    return cv2.filter2D(img, -1, kernel)

# 🔥 Main enhance
def enhance_image(image, style="Normal"):
    img = np.array(image)

    # base enhance
    img = cv2.convertScaleAbs(img, alpha=1.2, beta=20)

    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    hsv[:,:,1] = np.clip(hsv[:,:,1]*1.3, 0, 255)
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    # styles
    if style == "Cinematic":
        img = apply_vignette(img)

    elif style == "Sharp Pro":
        img = sharpen(img)

    elif style == "Warm":
        img[:,:,0] = np.clip(img[:,:,0]*1.1,0,255)

    return img

@app.route('/')
def home():
    return "App is running 🔥"

@app.route('/enhance', methods=['POST'])
def enhance():
    file = request.files['image']
    style = request.form.get("style", "Normal")

    image = Image.open(file).convert("RGB")
    enhanced = enhance_image(image, style)

    img_io = io.BytesIO()
    Image.fromarray(enhanced).save(img_io, 'JPEG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
