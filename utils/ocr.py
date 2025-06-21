import cv2
import pytesseract
import re
import numpy as np

# ✅ Path to Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Surya\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# === Configs
TESS_CONFIG = '--oem 3 --psm 6'
LANGUAGES = 'eng+tam+hin'

# === Preprocessing
def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    sharpen = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    gray = cv2.filter2D(gray, -1, sharpen)
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 9)
    return gray

# === Color Detection for Ration Card
def is_green_card(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return False
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([40, 40, 40])
    upper = np.array([90, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    green_ratio = cv2.countNonZero(mask) / (img.shape[0] * img.shape[1])
    print(f"[🎨] Green Ratio: {green_ratio:.2f}")
    return green_ratio > 0.2

# === Keyword Score
RATION_KEYWORDS = [
    "ration card", "family card", "head of family", "rc no", "member name",
    "sl no", "age", "relation", "பெயர்", "राशन कार्ड"
]

def ration_keyword_score(text):
    score = sum(1 for kw in RATION_KEYWORDS if kw.lower() in text.lower())
    print(f"[🔍] Ration keyword hits: {score}")
    return score

# === Type Detection
def detect_document_type(text):
    text_lower = text.lower()
    if re.search(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", text): return "aadhaar"
    if re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text): return "pan"
    if any(kw in text_lower for kw in RATION_KEYWORDS): return "rationcard"
    if re.search(r"\b(?:DL|TN|KA|MH|RJ|UP|GJ|BR|MP)?[-\s]?\d{2,4}[-\s]?\d{6,10}\b", text, re.IGNORECASE):
        return "driving_license"
    return "unknown"

# === Main Extraction
def extract_fields(image_path, doc_type=None):
    try:
        processed = preprocess_image(image_path)
    except Exception as e:
        print(f"[❌] Preprocessing error: {e}")
        return {"error": str(e), "is_verified": False, "detected_type": "unknown"}

    text = pytesseract.image_to_string(processed, lang=LANGUAGES, config=TESS_CONFIG)

    print("\n[🧾 OCR TEXT OUTPUT]\n" + "="*40 + f"\n{text}\n" + "="*40)

    detected_type = detect_document_type(text)
    if doc_type in [None, "unknown"]:
        doc_type = detected_type

    is_green = is_green_card(image_path)
    keyword_hits = ration_keyword_score(text)

    if doc_type == "rationcard":
        if not is_green and keyword_hits < 2:
            print("[⚠️] Ration Card not confidently verified (low green + keywords)")
            return {
                "detected_type": "rationcard",
                "id_number": "Not found",
                "is_verified": False
            }

    # === Extract ID
    if doc_type == "aadhaar":
        id_number = find_aadhaar_number(text)
    elif doc_type == "pan":
        id_number = find_pan_number(text)
    elif doc_type == "rationcard":
        id_number = find_ration_card_number(text)
    elif doc_type == "driving_license":
        id_number = find_dl_number(text)
    else:
        id_number = "Not found"

    is_verified = id_number != "Not found"
    output = {
        "raw_ocr_text": text,
        "detected_type": detected_type,
        "id_number": id_number,
        "is_verified": is_verified
    }

    if doc_type == "rationcard":
        output["family_members_count"] = count_family_members(text)

    print(f"[✅] Verified: {is_verified} | [ID] {id_number} | [TYPE] {doc_type}")
    return output

# === ID Extraction
def find_aadhaar_number(text):
    match = re.search(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", text)
    return match.group().replace(" ", "").replace("-", "") if match else "Not found"

def find_pan_number(text):
    match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text)
    return match.group() if match else "Not found"

def find_dl_number(text):
    match = re.search(r"\b(?:DL|TN|KA|MH|RJ|UP|GJ|BR|MP)[-\s]?\d{2,4}[-\s]?\d{6,10}\b", text, re.IGNORECASE)
    return match.group().replace(" ", "").replace("-", "") if match else "Not found"

def find_ration_card_number(text):
    match = re.search(r"(RC\s*(No|Number)\s*[:\-]?\s*[A-Z0-9\-]+)", text, re.IGNORECASE)
    if match:
        return re.sub(r"(RC\s*(No|Number)\s*[:\-]?\s*)", "", match.group(0), flags=re.IGNORECASE).strip()
    return find_number(text, min_digits=6)

def find_number(text, min_digits=6):
    for line in text.splitlines():
        digits = re.sub(r"\D", "", line)
        if len(digits) >= min_digits:
            return digits
    return "Not found"

# ✅ Final fixed function
def count_family_members(text):
    count_keywords = ["Member Name", "Sl No", "Name", "Sr.", "பெயர்", "नाम", "Relation", "Age"]
    return sum(1 for line in text.splitlines() if any(k.lower() in line.lower() for k in count_keywords))
