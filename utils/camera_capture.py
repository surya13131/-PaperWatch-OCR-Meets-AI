import cv2
import requests

url = 'http://127.0.0.1:5000/'  # Flask server URL

cam = cv2.VideoCapture(0)
print("📷 Press SPACE to capture image, ESC to exit")

while True:
    ret, frame = cam.read()
    cv2.imshow("PaperWatch - Camera", frame)

    k = cv2.waitKey(1)
    if k % 256 == 27:  # ESC
        print("❌ Cancelled.")
        break
    elif k % 256 == 32:  # SPACE
        filename = "captured.jpg"
        cv2.imwrite(filename, frame)
        print(f"✅ Image saved as {filename}, sending to server...")

        with open(filename, 'rb') as f:
            files = {'doc': f}
            r = requests.post(url, files=files)
            print("📄 Server Response:\n")
            print(r.text)
        break

cam.release()
cv2.destroyAllWindows()
