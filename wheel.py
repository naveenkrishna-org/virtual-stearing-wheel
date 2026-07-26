import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pydirectinput
import os
import time
import sys
import math

# 1. ATTRACTIVE TERMINAL LAUNCH ANIMATION
def terminal_launch():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = """
    ========================================================
               Parthiban's Virtual Steering Wheel           
              - Real-Time Webcam Gesture Controller -       
    ========================================================
    """
    print(banner)
    
    message = "Parthiban's virtual steering wheel is launching "
    sys.stdout.write(message)
    sys.stdout.flush()
    
    for _ in range(5):
        time.sleep(0.4)
        sys.stdout.write(".")
        sys.stdout.flush()
    print("\n\n[✓] System Ready! Opening Dashboard...")
    time.sleep(1)

terminal_launch()

# 2. SETUP MEDIAPIPE TASKS
model_path = 'hand_landmarker.task'
if not os.path.exists(model_path):
    print(f"ERROR: Could not find '{model_path}' on your Desktop.")
    print("Please make sure it's in the same folder as this script.")
    exit()

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO, 
    num_hands=2
)
detector = vision.HandLandmarker.create_from_options(options)

# Open Webcam
cap = cv2.VideoCapture(0)

# Global variables for state management
app_state = "HOME"
button_clicked = False

# Dynamic button coordinates
btn_x1, btn_y1, btn_x2, btn_y2 = 0, 0, 0, 0

# Mouse callback function
def mouse_click(event, x, y, flags, param):
    global app_state, button_clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        if app_state == "HOME":
            if btn_x1 <= x <= btn_x2 and btn_y1 <= y <= btn_y2:
                button_clicked = True
                app_state = "GAME"

cv2.namedWindow("Parthiban's Virtual Steering Wheel")
cv2.setMouseCallback("Parthiban's Virtual Steering Wheel", mouse_click)

# Game Control State Variables
current_steering = None
up_pressed = False
down_pressed = False
frame_timestamp_ms = 0

# Helper function for UI Text
def draw_centered_text(img, text, font, scale, thickness, y_pos, color):
    text_size = cv2.getTextSize(text, font, scale, thickness)[0]
    text_x = (img.shape[1] - text_size[0]) // 2
    cv2.putText(img, text, (text_x + 2, y_pos + 2), font, scale, (0, 0, 0), thickness, cv2.LINE_AA)
    cv2.putText(img, text, (text_x, y_pos), font, scale, color, thickness, cv2.LINE_AA)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        continue

    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape 

    if app_state == "HOME":
        # UI rendering logic
        blurred_bg = cv2.GaussianBlur(frame, (35, 35), 0)
        overlay = blurred_bg.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (15, 15, 20), -1) 
        home_screen = cv2.addWeighted(overlay, 0.7, blurred_bg, 0.3, 0)
        
        cv2.rectangle(home_screen, (15, 15), (w-15, h-15), (255, 255, 255), 1)
        cv2.rectangle(home_screen, (20, 20), (w-20, h-20), (255, 200, 0), 1) 
        
        draw_centered_text(home_screen, "WELCOME TO", cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1, h//2 - 120, (200, 200, 200))
        draw_centered_text(home_screen, "PARTHIBAN'S", cv2.FONT_HERSHEY_DUPLEX, 1.4, 2, h//2 - 70, (255, 215, 0)) 
        draw_centered_text(home_screen, "VIRTUAL STEERING WHEEL", cv2.FONT_HERSHEY_DUPLEX, 0.8, 2, h//2 - 25, (255, 255, 255))
        
        cv2.line(home_screen, (w//2 - 100, h//2 + 5), (w//2 + 100, h//2 + 5), (255, 200, 0), 2)
        
        draw_centered_text(home_screen, "Press BEGIN to start the engine...", cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, 1, h//2 + 45, (180, 180, 180))
        
        btn_w, btn_h = 200, 50
        btn_x1 = (w - btn_w) // 2
        btn_y1 = h//2 + 80
        btn_x2 = btn_x1 + btn_w
        btn_y2 = btn_y1 + btn_h
        
        cv2.rectangle(home_screen, (btn_x1+4, btn_y1+4), (btn_x2+4, btn_y2+4), (0, 0, 0), -1)
        cv2.rectangle(home_screen, (btn_x1, btn_y1), (btn_x2, btn_y2), (255, 170, 0), -1)
        cv2.rectangle(home_screen, (btn_x1, btn_y1), (btn_x2, btn_y2), (255, 255, 255), 2)
        
        text_size = cv2.getTextSize("BEGIN", cv2.FONT_HERSHEY_DUPLEX, 0.8, 2)[0]
        text_x = btn_x1 + (btn_w - text_size[0]) // 2
        text_y = btn_y1 + (btn_h + text_size[1]) // 2 - 2
        cv2.putText(home_screen, "BEGIN", (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Updated footer with Brake instructions
        draw_centered_text(home_screen, "[Fist] Gas | [Tilt] Steer | [Pull Hands Back] Brake", cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1, h - 40, (150, 150, 150))
        
        cv2.imshow("Parthiban's Virtual Steering Wheel", home_screen)

    elif app_state == "GAME":
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        frame_timestamp_ms += 1
        results = detector.detect_for_video(mp_image, frame_timestamp_ms)

        wrists = []
        closed_fists = 0

        if results.hand_landmarks:
            for hand_landmarks in results.hand_landmarks:
                for lm in hand_landmarks:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)
                
                wrist = hand_landmarks[0]
                cx, cy = int(wrist.x * w), int(wrist.y * h)
                wrists.append((cx, cy))

                # Check if hand is closed (Fist)
                if hand_landmarks[8].y > hand_landmarks[6].y:
                    closed_fists += 1

        # 1. HANDLE GAS (UP)
        if closed_fists > 0 and not down_pressed:
            if not up_pressed:
                pydirectinput.keyDown('up')
                up_pressed = True
        else:
            if up_pressed:
                pydirectinput.keyUp('up')
                up_pressed = False

        # 2. HANDLE STEERING AND BRAKING
        if len(wrists) == 2:
            wrists = sorted(wrists, key=lambda x: x[0])
            left_wrist, right_wrist = wrists[0], wrists[1]

            # --- NEW: BRAKE LOGIC (PULLING HANDS BACK) ---
            # Calculate distance between wrists
            wrist_distance = math.hypot(right_wrist[0] - left_wrist[0], right_wrist[1] - left_wrist[1])
            
            # If distance is large, hands are pulled back closer to the body/camera
            # You may need to tweak this number (e.g., 250) based on how close you sit to the camera
            brake_threshold = 280 

            if wrist_distance > brake_threshold:
                # Draw the line red to indicate braking
                cv2.line(frame, left_wrist, right_wrist, (0, 0, 255), 4)
                if not down_pressed:
                    pydirectinput.keyDown('down')
                    down_pressed = True
            else:
                # Normal driving, line is cyan/blue
                cv2.line(frame, left_wrist, right_wrist, (255, 200, 0), 3)
                if down_pressed:
                    pydirectinput.keyUp('down')
                    down_pressed = False

            # --- ORIGINAL STEERING LOGIC ---
            y_diff = left_wrist[1] - right_wrist[1]
            steer_threshold = 40 

            if y_diff > steer_threshold:
                if current_steering != 'left':
                    if current_steering: pydirectinput.keyUp(current_steering)
                    pydirectinput.keyDown('left')
                    current_steering = 'left'
            elif y_diff < -steer_threshold:
                if current_steering != 'right':
                    if current_steering: pydirectinput.keyUp(current_steering)
                    pydirectinput.keyDown('right')
                    current_steering = 'right'
            else:
                if current_steering:
                    pydirectinput.keyUp(current_steering)
                    current_steering = None
        else:
            # If hands are lost, release steering and brake
            if current_steering:
                pydirectinput.keyUp(current_steering)
                current_steering = None
            if down_pressed:
                pydirectinput.keyUp('down')
                down_pressed = False

        # Visual HUD overlay
        cv2.putText(frame, f"Steering: {current_steering or 'STRAIGHT'}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"Gas: {'ON' if up_pressed else 'OFF'}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0) if up_pressed else (0, 255, 255), 2)
        
        # Show Brake status in red when active
        brake_color = (0, 0, 255) if down_pressed else (0, 255, 255)
        cv2.putText(frame, f"Brake: {'ACTIVE' if down_pressed else 'OFF'}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, brake_color, 2)

        cv2.imshow("Parthiban's Virtual Steering Wheel", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
if current_steering: pydirectinput.keyUp(current_steering)
if up_pressed: pydirectinput.keyUp('up')
if down_pressed: pydirectinput.keyUp('down')
cap.release()
cv2.destroyAllWindows()