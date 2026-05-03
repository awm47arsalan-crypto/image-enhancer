from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io
import os

app = Flask(__name__)
CORS(app)

# 🔥 AUTO BRIGHTNESS + CONTRAST
def auto_brightness_contrast(image, clip_hist_percent=1):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    hist = cv2.calcHist([gray],[0],None,[256],[0,256])
    hist_size = len(hist)

    accumulator = [float(hist[0])]
    for i in range(1, hist_size):
        accumulator.append(accumulator[i-1] + float(hist[i]))

    maximum = accumulator[-1]
    clip_hist_percent *= (maximum/100.0)
    clip_hist_percent /= 2.0

    minimum_gray = 0
    while accumulator[minimum_gray] < clip_hist_percent:
        minimum_gray += 1

    maximum_gray = hist_size - 1
    while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
        maximum_gray -= 1

    if maximum_gray - minimum_gray == 0:
        return image

    alpha = 255 / (maximum_gray - minimum_gray)
    beta = -minimum_gray * alpha

    return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

# 🎬 VIGNETTE (FIXED)
def apply_vignette(img):
    rows, cols = img.shape[:2]

    kernel_x = cv2.getGaussianKernel(cols, cols/2)
    kernel_y = cv2.getGaussianKernel(rows, rows/2)
    mask = kernel_y * kernel_x.T
    mask = mask / mask.max()

    # FIX: convert to float
    mask = mask.astype(np.float32)
    img = img.astype(np.float32)

    for i in range(3):
        img[:,:,i] = img[:,:,i] * mask

    return np.clip(img, 0, 255).astype(np.uint8)

# 🔪 SHARPEN
def sharpen(img):
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    return cv2.filter2D(img, -1, kernel)

# 🚀 MAIN ENHANCER
def enhance_image(image, style="Normal"):
    img = np.array(image)

    # Adaptive brightness
    img = auto_brightness_contrast(img)

    # Saturation control
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    hsv[:,:,1] = np.clip(hsv[:,:,1] * 1.2, 0, 255)
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    # Styles
    if style == "Cinematic":
        img = apply_vignette(img)
    elif style == "Sharp Pro":
        img = sharpen(img)
    elif style == "Warm":
        img[:,:,0] = np.clip(img[:,:,0] * 1.1, 0, 255)

    return img.astype(np.uint8)

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

        # ensure valid format
        enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)

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
