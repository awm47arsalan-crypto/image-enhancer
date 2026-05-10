from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from io import BytesIO
import numpy as np

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "AI Image Enhancer Backend is running"
    })


def smart_upscale(image, max_size=2160):
    """Upscale image while preserving aspect ratio."""
    width, height = image.size

    # Don't downscale large images; keep original if already large enough.
    longest_side = max(width, height)
    if longest_side >= max_size:
        return image

    scale = max_size / longest_side
    new_width = int(width * scale)
    new_height = int(height * scale)

    return image.resize((new_width, new_height), Image.LANCZOS)


def basic_enhance(image):
    """Base enhancement applied to all modes."""
    # Slight denoise
    image = image.filter(ImageFilter.MedianFilter(size=3))

    # Auto contrast
    image = ImageOps.autocontrast(image, cutoff=1)

    # Sharpness
    image = ImageEnhance.Sharpness(image).enhance(1.8)

    # Contrast
    image = ImageEnhance.Contrast(image).enhance(1.12)

    return image


def apply_mode(image, mode):
    mode = (mode or "normal").lower()

    if mode == "normal":
        return image

    elif mode == "cinematic":
        image = ImageEnhance.Contrast(image).enhance(1.25)
        image = ImageEnhance.Color(image).enhance(0.95)
        image = ImageEnhance.Sharpness(image).enhance(1.25)
        r, g, b = image.split()
        r = r.point(lambda i: min(255, i * 1.05))
        b = b.point(lambda i: i * 0.95)
        return Image.merge("RGB", (r, g, b))

    elif mode == "portrait":
        image = ImageEnhance.Color(image).enhance(1.08)
        image = ImageEnhance.Brightness(image).enhance(1.03)
        image = ImageEnhance.Contrast(image).enhance(1.08)
        return image

    elif mode == "vivid":
        image = ImageEnhance.Color(image).enhance(1.45)
        image = ImageEnhance.Contrast(image).enhance(1.18)
        image = ImageEnhance.Sharpness(image).enhance(1.35)
        return image

    elif mode == "warm":
        r, g, b = image.split()
        r = r.point(lambda i: min(255, i * 1.10))
        g = g.point(lambda i: min(255, i * 1.03))
        b = b.point(lambda i: i * 0.94)
        return Image.merge("RGB", (r, g, b))

    elif mode == "cool":
        r, g, b = image.split()
        r = r.point(lambda i: i * 0.95)
        g = g.point(lambda i: min(255, i * 1.02))
        b = b.point(lambda i: min(255, i * 1.10))
        return Image.merge("RGB", (r, g, b))

    elif mode == "moody":
        image = ImageEnhance.Brightness(image).enhance(0.92)
        image = ImageEnhance.Contrast(image).enhance(1.30)
        image = ImageEnhance.Color(image).enhance(0.90)
        return image

    elif mode == "golden":
        r, g, b = image.split()
        r = r.point(lambda i: min(255, i * 1.12))
        g = g.point(lambda i: min(255, i * 1.08))
        b = b.point(lambda i: i * 0.90)
        return Image.merge("RGB", (r, g, b))

    elif mode == "teal_orange":
        arr = np.array(image).astype(np.float32)

        # Orange boost in reds
        arr[:, :, 0] *= 1.10
        # Teal boost in blue/green
        arr[:, :, 1] *= 1.03
        arr[:, :, 2] *= 1.08

        arr = np.clip(arr, 0, 255).astype(np.uint8)
        image = Image.fromarray(arr)
        image = ImageEnhance.Contrast(image).enhance(1.18)
        return image

    elif mode == "black_white":
        bw = ImageOps.grayscale(image)
        bw = ImageEnhance.Contrast(bw).enhance(1.20)
        return bw.convert("RGB")

    return image


@app.route("/enhance", methods=["POST"])
def enhance_image():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    mode = request.form.get("mode", "normal")

    try:
        # Open image and preserve original format
        image = Image.open(file.stream)
        original_format = image.format if image.format else "JPEG"

        # Convert to RGB for processing
        image = image.convert("RGB")

        # Smart upscale
        image = smart_upscale(image, max_size=2160)

        # Universal enhancement
        image = basic_enhance(image)

        # Apply selected LUT/mode
        image = apply_mode(image, mode)

        # Final micro-sharpening
        image = ImageEnhance.Sharpness(image).enhance(1.15)

        # Save output
        img_io = BytesIO()

        save_format = "PNG" if str(original_format).upper() == "PNG" else "JPEG"

        if save_format == "PNG":
            image.save(img_io, format="PNG")
            mimetype = "image/png"
            filename = "enhanced-image.png"
        else:
            image.save(
                img_io,
                format="JPEG",
                quality=100,
                optimize=False,
                subsampling=0
            )
            mimetype = "image/jpeg"
            filename = "enhanced-image.jpg"

        img_io.seek(0)

        return send_file(
            img_io,
            mimetype=mimetype,
            as_attachment=False,
            download_name=filename
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
