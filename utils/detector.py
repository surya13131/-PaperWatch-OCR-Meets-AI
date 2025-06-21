import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'paperwatch_model.h5')

try:
    model = load_model(MODEL_PATH)
    print("[✅] Document classification model loaded.")
except Exception as e:
    print(f"[❌] Failed to load model: {e}")
    model = None

labels = ['aadhaar', 'rationcard', 'face']

def predict_document_type(image_path):
    if model is None:
        return 'unknown', 0.0
    try:
        img = load_img(image_path, target_size=(128, 128))
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        pred = model.predict(img_array)[0]
        print(f"[DEBUG] Prediction vector: {pred}")
        label = labels[np.argmax(pred)]
        confidence = float(np.max(pred))
        print(f"[📄] Predicted: {label} ({confidence:.2f})")
        return label, confidence
    except Exception as e:
        print(f"[❌] Prediction failed: {e}")
        return 'unknown', 0.0

# Face detection logic
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def contains_face_opencv(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return False
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    print(f"[🔍 FACE DETECTION] Found {len(faces)} face(s).")
    return len(faces) > 0
