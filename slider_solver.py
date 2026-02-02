import random
import cv2
import numpy as np
import io

HAS_DDDDOCR = False
ocr_instance = None

try:
    import ddddocr
    ocr_instance = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    HAS_DDDDOCR = True
    print("✅ [SliderSolver] AI 引擎加载成功")
except:
    print("⚠️ [SliderSolver] 切换至 OpenCV 模式")

def get_gap_distance(background_bytes):
    if HAS_DDDDOCR and ocr_instance: return _get_gap_by_ai(background_bytes)
    else: return _get_gap_by_opencv_contours(background_bytes)

def _get_gap_by_ai(bg_bytes):
    try:
        res = ocr_instance.slide_match(None, bg_bytes, simple_target=True)
        return res['target'][0]
    except: return None

def _get_gap_by_opencv_contours(bg_bytes):
    try:
        np_arr = np.frombuffer(bg_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        canny = cv2.Canny(blurred, 200, 400)
        contours, _ = cv2.findContours(canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1500 or area > 6000: continue
            x, y, w, h = cv2.boundingRect(contour)
            if x < 50: continue
            if 0.8 < w / h < 1.2: return x
        return None
    except: return None

def generate_tracks(distance):
    tracks = []
    current = 0
    mid = distance * 3 / 4 
    t = random.randint(2, 3) / 10 
    v = 0 
    while current < distance:
        if current < mid: a = 2 
        else: a = -3 
        v0 = v
        v = v0 + a * t
        move = v0 * t + 1 / 2 * a * t * t
        current += move
        y_shake = random.randint(-1, 1) if random.random() > 0.9 else 0
        tracks.append((round(move), y_shake, random.uniform(0.02, 0.04)))
    overshoot = random.randint(2, 5)
    for _ in range(overshoot): tracks.append((1, 0, 0.02)) 
    for _ in range(overshoot): tracks.append((-1, 0, 0.03)) 
    return tracks
