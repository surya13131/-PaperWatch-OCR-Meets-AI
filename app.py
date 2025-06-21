from flask import Flask, render_template, request, url_for, jsonify
import os, uuid, json, qrcode, logging
from PIL import Image
from utils.detector import predict_document_type, contains_face_opencv
from utils.ocr import extract_fields
import numpy as np

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB

UPLOAD_FOLDER = 'static/uploads/'
QRCODE_FOLDER = 'static/qrcodes/'
DB_PATH = 'static/db.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QRCODE_FOLDER, exist_ok=True)

if not os.path.exists(DB_PATH):
    with open(DB_PATH, 'w') as f:
        json.dump({}, f)

def load_db():
    try:
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def convert_np_types(obj):
    if isinstance(obj, dict):
        return {k: convert_np_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_np_types(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    else:
        return obj

def save_to_db(doc_id, data):
    db = load_db()
    db[doc_id] = convert_np_types(data)
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=2)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('doc')

        if not file or not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return render_template('index.html', result="❌ Invalid or missing image file.")

        try:
            img = Image.open(file.stream)
            img.verify()
        except Exception:
            return render_template('index.html', result="❌ Uploaded file is not a valid image.")

        filename = f"{uuid.uuid4().hex}.jpg"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.seek(0)
        file.save(save_path)

        # Run document type prediction
        doc_type, confidence = predict_document_type(save_path)
        logging.info(f"[MODEL] Predicted: {doc_type} (conf={confidence:.2f})")

        # Reject faces/selfies
        if doc_type in ['face', 'unknown']:
            if contains_face_opencv(save_path):
                return render_template('index.html',
                    result="❌ Rejected: Selfie or face-only image detected.",
                    image_path=url_for('static', filename=f'uploads/{filename}'))

        # Run OCR
        details = extract_fields(save_path, doc_type)
        logging.info(f"[OCR] Extracted: {details}")

        if not details or not details.get("is_verified"):
            return render_template('index.html',
                result="❌ Rejected: Fake document or Face detected.",
                image_path=url_for('static', filename=f'uploads/{filename}'))

        # Final fallback: OCR might override type
        if doc_type not in ['aadhaar', 'rationcard'] or confidence < 0.7:
            if details.get("detected_type") in ['aadhaar', 'rationcard']:
                doc_type = details['detected_type']
                confidence = 0.65
                logging.info("[OCR] Overriding doc type from OCR.")

        if not details.get("id_number") or details.get("id_number") == "Not found":
            return render_template('index.html',
                result="❌ ID Number not found or invalid.",
                image_path=url_for('static', filename=f'uploads/{filename}'))

        # ✅ Final details
        final_details = {
            "id_number": details.get("id_number"),
            "type": doc_type,
            "name": details.get("name", "Not found"),
            "dob": details.get("dob", "Not found"),
            "address": details.get("address", "Not found"),
            "detected_type": details.get("detected_type", doc_type),

        }

        # If ration card, include family count
        if doc_type == "rationcard" and "family_members_count" in details:
            final_details["family_members_count"] = details["family_members_count"]

        doc_id = uuid.uuid4().hex
        qr_url = url_for('document_api', doc_id=doc_id, _external=True)
        qr_path = os.path.join(QRCODE_FOLDER, f"{doc_id}.png")
        qrcode.make(qr_url).save(qr_path)

        save_to_db(doc_id, final_details)

        return render_template('index.html',
            result="✅ Verified Document",
            details=final_details,
            image_path=url_for('static', filename=f'uploads/{filename}'),
            qr_path=url_for('static', filename=f'qrcodes/{doc_id}.png'))

    return render_template('index.html')

@app.route('/document/<doc_id>')
def document_api(doc_id):
    db = load_db()
    if doc_id not in db:
        return jsonify({"status": "error", "message": "Document not found"}), 404
    return jsonify(db[doc_id])

@app.route('/gesture-scan')
def gesture_scan():
    return render_template('gesture.html')

if __name__ == '__main__':
    app.run(debug=True)
