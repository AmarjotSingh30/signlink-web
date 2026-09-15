import base64
import cv2
import json
import mediapipe as mp
import numpy as np
from flask import Flask, jsonify, render_template, request
from keras.models import model_from_json

app = Flask(__name__)

# ----------------------------------------------------
# 1. Load Model, Weights, and Classes
# ----------------------------------------------------
MODEL_DIR = "model/"
with open(MODEL_DIR + "model-mp.json", "r") as f:
    model = model_from_json(f.read())
model.load_weights(MODEL_DIR + "model-mp.h5")

raw_classes = np.load(MODEL_DIR + "classes.npy", allow_pickle=True)
classes = [str(c) for c in raw_classes]
excluded_signs = ["BLANK", "DEL", "DELETE", "SPACE", "NOTHING"]

# ----------------------------------------------------
# 2. Initialize MediaPipe Hands
# ----------------------------------------------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5,
)

# ----------------------------------------------------
# 3. Global State
# ----------------------------------------------------
APP_MODE = "INTERPRETER"
current_symbol = "--"
last_symbol = "--"
stable_frames = 0
current_sentence = ""

curriculum = sorted([c for c in classes if c not in excluded_signs])
current_index = 0
target_letter = curriculum[current_index] if curriculum else "A"
hold_frames = 0
required_frames = 20
diagnostic_log = "[SYSTEM] Cloud Engine Initialized. Awaiting video stream..."


def process_interpreter_logic(symbol):
  global current_symbol, last_symbol, stable_frames, current_sentence
  current_symbol = symbol

  if current_symbol == last_symbol:
    stable_frames += 1
  else:
    last_symbol = current_symbol
    stable_frames = 0

  if stable_frames == 6:
    if current_symbol != "--":
      current_sentence += current_symbol


def process_learn_logic(symbol):
  global current_symbol, hold_frames, target_letter, current_index, diagnostic_log
  current_symbol = symbol

  if symbol == target_letter:
    hold_frames += 1
    if hold_frames == 1:
      diagnostic_log = "[VALIDATING] Target lock acquired. Hold position..."
    if hold_frames >= required_frames:
      diagnostic_log = (
          f"[SUCCESS] Matrix '{target_letter}' validated! Advancing pipeline..."
      )
      current_index = (current_index + 1) % len(curriculum)
      target_letter = curriculum[current_index]
      hold_frames = 0
  else:
    if hold_frames > 0:
      diagnostic_log = (
          f"[ERROR] Posture deviation. AI tracking '{symbol}'. Adjust hand."
      )
      hold_frames = max(0, hold_frames - 2)
    else:
      diagnostic_log = "[WARNING] Target lost. Match the reference sign."


# ----------------------------------------------------
# 4. Web Endpoints
# ----------------------------------------------------
@app.route("/")
def index():
  return render_template("index.html")


@app.route("/process_frame", methods=["POST"])
def process_frame():
  global current_symbol, APP_MODE, target_letter, hold_frames, required_frames, diagnostic_log, current_index, curriculum, current_sentence
  try:
    # Decode Base64 JPEG frame sent from client's browser
    data = request.get_json()
    img_bytes = base64.b64decode(data["image"].split(",")[1])
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Flip horizontally for selfie mirror effect & convert to RGB
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Black canvas for Panel 2: Handlandmarks Preview
    black_canvas = np.zeros(frame.shape, dtype=np.uint8)
    results = hands.process(rgb_frame)

    detected = "--"
    if results.multi_hand_landmarks and results.multi_handedness:
      for hand_landmarks, handedness in zip(
          results.multi_hand_landmarks, results.multi_handedness
      ):
        # Draw 21 topological points and bones on black canvas
        mp_drawing.draw_landmarks(
            black_canvas, hand_landmarks, mp_hands.HAND_CONNECTIONS
        )
        hand_type = handedness.classification[0].label

        # Dynamic Chirality Correction
        coords = []
        for lm in hand_landmarks.landmark:
          x_val = lm.x
          if hand_type == "Right":
            x_val = 1.0 - x_val
          coords.extend([x_val, lm.y, lm.z])

        # DNN Inference
        reshaped_coords = np.array([coords])
        predictions = model.predict(reshaped_coords, verbose=0)
        max_index = np.argmax(predictions[0])

        if predictions[0][max_index] > 0.85:
          sign = str(classes[max_index])
          if sign.strip().upper() not in excluded_signs:
            detected = sign

    # Update logic based on active tab
    if APP_MODE == "INTERPRETER":
      process_interpreter_logic(detected)
    elif APP_MODE == "LEARN":
      process_learn_logic(detected)

    # Encode black canvas skeleton to Base64 to render in Panel 2
    _, skel_buf = cv2.imencode(".jpg", black_canvas)
    skel_base64 = "data:image/jpeg;base64," + base64.b64encode(
        skel_buf
    ).decode("utf-8")

    progress_pct = (
        min(100, int((hold_frames / required_frames) * 100))
        if APP_MODE == "LEARN"
        else 0
    )

    return jsonify({
        "status": "success",
        "skeleton": skel_base64,
        "prediction": current_symbol,
        "sentence": current_sentence,
        "target_letter": target_letter,
        "progress_pct": progress_pct,
        "diagnostic_log": diagnostic_log,
        "progress_text": f"({current_index + 1}/{len(curriculum)})",
    })

  except Exception as e:
    return jsonify({"status": "error", "message": str(e)})


@app.route("/switch_mode", methods=["POST"])
def switch_mode():
  global APP_MODE, hold_frames, diagnostic_log
  data = request.get_json()
  APP_MODE = data.get("mode", "INTERPRETER")
  hold_frames = 0
  diagnostic_log = "[SYSTEM] Initialized. Awaiting hand topology..."
  return jsonify({"status": "ok"})


@app.route("/navigate_learn", methods=["POST"])
def navigate_learn():
  global current_index, target_letter, hold_frames, diagnostic_log
  data = request.get_json()
  direction = data.get("direction", "next")

  if direction == "next":
    current_index = (current_index + 1) % len(curriculum)
  else:
    current_index = (current_index - 1) % len(curriculum)

  target_letter = curriculum[current_index]
  hold_frames = 0
  diagnostic_log = f"[SYSTEM] Sequence '{target_letter}' loaded."
  return jsonify({"status": "ok"})


@app.route("/clear_sentence", methods=["POST"])
def clear_sentence():
  global current_sentence
  current_sentence = ""
  return jsonify({"status": "ok"})


@app.route("/add_space", methods=["POST"])
def add_space():
  global current_sentence
  current_sentence += " "
  return jsonify({"status": "ok"})


@app.route("/backspace", methods=["POST"])
def backspace():
  global current_sentence
  if len(current_sentence) > 0:
    current_sentence = current_sentence[:-1]
  return jsonify({"status": "ok"})


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=False)