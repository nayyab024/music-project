from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
import time
import os
import math
import pygame
import threading

app = Flask(__name__)

# ------------------------
# Configuration
# ------------------------

MUSIC_FOLDER = "music"
SWIPE_VEL_THRESHOLD = 1000
PINCH_THRESHOLD = 0.04
VOLUME_SMOOTHING = 0.05
SEEK_SECONDS = 10
FACE_ABSENCE_PAUSE_DELAY = 2.0

# ------------------------
# Utilities
# ------------------------

def load_playlist(folder):
    files = []
    for f in os.listdir(folder):
        if f.lower().endswith((".mp3", ".wav", ".ogg")):
            files.append(os.path.join(folder, f))
    files.sort()
    return files

def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

# ------------------------
# Initialize pygame
# ------------------------

pygame.mixer.init()
playlist = load_playlist(MUSIC_FOLDER)
if not playlist:
    print("No music files found in 'music' folder.")
    playlist = []

current_index = 0
favorites = set()
is_playing = False
volume = 0.7
gesture_text = ""

def load_track(idx):
    global current_index
    if len(playlist) == 0:
        return
    current_index = idx % len(playlist)
    pygame.mixer.music.load(playlist[current_index])

if len(playlist) > 0:
    load_track(current_index)
    pygame.mixer.music.play()
    is_playing = True
    pygame.mixer.music.set_volume(volume)

# ------------------------
# MediaPipe init
# ------------------------

mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.5)
face_detector = mp_face.FaceDetection(min_detection_confidence=0.6)

cap = cv2.VideoCapture(0)
last_centroid = None
last_move_time = time.time()
last_face_seen = time.time()
last_swipe_time = 0
last_seek_time = 0
volume_target = volume

TIP_IDS = [4,8,12,16,20]

def count_fingers(hand_landmarks):
    lm = hand_landmarks.landmark
    fingers = 0
    for i in range(1,5):
        tip = lm[TIP_IDS[i]]
        pip = lm[TIP_IDS[i]-2]
        if tip.y < pip.y:
            fingers += 1
    thumb_tip = lm[TIP_IDS[0]]
    thumb_ip = lm[TIP_IDS[0]-2]
    if abs(thumb_tip.x - thumb_ip.x) > 0.02:
        fingers += 1
    return fingers

# ------------------------
# Video generation
# ------------------------

def generate_frames():
    global is_playing, volume, volume_target, last_centroid, last_move_time
    global last_face_seen, last_swipe_time, last_seek_time, gesture_text

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Face detection
        face_results = face_detector.process(rgb)
        face_present = False
        if face_results.detections:
            face_present = True
            last_face_seen = time.time()

        if not face_present and is_playing and (time.time()-last_face_seen)>FACE_ABSENCE_PAUSE_DELAY:
            pygame.mixer.music.pause()
            is_playing = False
            gesture_text = "Auto-paused (no user)"

        hand_results = hands.process(rgb)
        gesture_text = ""

        if hand_results.multi_hand_landmarks:
            hand_landmarks = hand_results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            xs = [lm.x for lm in hand_landmarks.landmark]
            ys = [lm.y for lm in hand_landmarks.landmark]
            cx = sum(xs)/len(xs)
            cy = sum(ys)/len(ys)
            centroid_px = (int(cx*w), int(cy*h))

            fingers = count_fingers(hand_landmarks)

            thumb = hand_landmarks.landmark[4]
            index = hand_landmarks.landmark[8]
            pinch_dist = math.hypot(thumb.x-index.x, thumb.y-index.y)

            cv2.circle(frame, centroid_px, 5, (0,255,0), -1)

            now = time.time()
            if last_centroid is not None:
                dx = centroid_px[0]-last_centroid[0]
                dt = now-last_move_time if (now-last_move_time)>1e-6 else 1e-6
                vx = dx/dt
                if abs(vx)>SWIPE_VEL_THRESHOLD and (now-last_swipe_time)>0.6:
                    if vx>0:
                        load_track(current_index+1)
                        pygame.mixer.music.play()
                        is_playing = True
                        gesture_text="Next Track"
                    else:
                        load_track(current_index-1)
                        pygame.mixer.music.play()
                        is_playing = True
                        gesture_text="Previous Track"
                    last_swipe_time = now

            if fingers==1:
                idx_tip = hand_landmarks.landmark[8]
                vol = 1.0-idx_tip.y
                volume_target = volume_target*(1-VOLUME_SMOOTHING)+vol*VOLUME_SMOOTHING
                pygame.mixer.music.set_volume(max(0.0,min(1.0,volume_target)))
                gesture_text=f"Volume: {int(pygame.mixer.music.get_volume()*100)}%"
                volume = pygame.mixer.music.get_volume()

            if fingers>=4:
                if is_playing:
                    pygame.mixer.music.pause()
                    is_playing = False
                    gesture_text="Pause"
            elif fingers==0:
                if not is_playing:
                    pygame.mixer.music.unpause()
                    is_playing = True
                    gesture_text="Play"

            if fingers>=2 and last_centroid is not None:
                dx = centroid_px[0]-last_centroid[0]
                if abs(dx)>40 and (now-last_seek_time)>0.6:
                    if dx>0:
                        gesture_text=f"Seek +{SEEK_SECONDS}s"
                        try: pygame.mixer.music.play(start=SEEK_SECONDS)
                        except: pass
                    else:
                        gesture_text=f"Seek -{SEEK_SECONDS}s"
                        try: pygame.mixer.music.play(start=0)
                        except: pass
                    last_seek_time = now

            if pinch_dist<PINCH_THRESHOLD:
                if current_index in favorites:
                    favorites.remove(current_index)
                    gesture_text="Removed from Favorites"
                else:
                    favorites.add(current_index)
                    gesture_text="Added to Favorites"
                time.sleep(0.5)

            if fingers==2:
                gesture_text="Admin Mode"

            last_centroid = centroid_px
            last_move_time = now
        else:
            last_centroid = None

        # UI overlays
        cv2.rectangle(frame,(0,0),(w,60),(0,0,0),-1)
        if len(playlist) > 0:
            title = os.path.basename(playlist[current_index])
            status = "Playing" if is_playing else "Paused"
            fav_mark = "★" if current_index in favorites else ""
            cv2.putText(frame,f"{fav_mark} {title}",(10,25),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2)
            cv2.putText(frame,f"Status: {status}",(10,50),cv2.FONT_HERSHEY_SIMPLEX,0.6,(200,200,200),1)

        if gesture_text:
            cv2.putText(frame,gesture_text,(w-300,30),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,200,0),2)

        help_text="Gestures: Open palm=Pause | Fist=Play | Swipe=Next/Prev | Index up=Volume | Pinch=Fav"
        cv2.putText(frame,help_text,(10,h-10),cv2.FONT_HERSHEY_SIMPLEX,0.4,(180,180,180),1)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# ------------------------
# Flask routes
# ------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    track_name = ""
    if len(playlist) > 0:
        track_name = os.path.basename(playlist[current_index])

    playlist_names = [os.path.basename(p) for p in playlist]

    return jsonify({
        'track_name': track_name,
        'status': 'Playing' if is_playing else 'Paused',
        'volume': int(pygame.mixer.music.get_volume() * 100),
        'current_index': current_index,
        'playlist': playlist_names,
        'favorites': list(favorites)
    })

if __name__ == '__main__':
    print("Starting Gesture Music Player Web Interface...")
    print("Open your browser and go to: http://localhost:5001")
    app.run(debug=False, host='0.0.0.0', port=5001)
