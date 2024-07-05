import mediapipe as mp
import cv2
import time
import serial
import numpy as np

# Serial setup
ser = serial.Serial('COM3', 115200, timeout=1)

# Function to send commands over serial
def send_command(command):
    ser.write((command + '\n').encode())
    print(f"Sent: {command}")

drawingModule = mp.solutions.drawing_utils
handsModule = mp.solutions.hands

cap = cv2.VideoCapture(0)
prev_frame_time = 0

screen_width = 640
screen_height = 480

# Speed regulation variables
min_speed = 0.1  # minimum interval in seconds
max_speed = 2.0  # maximum interval in seconds
speed = 1.0  # initial speed
last_command_time = time.time()

# Regulator rectangle (moved to bottom left)
regulator = [(0, screen_height - 100), (100, screen_height)]

# Rectangle definitions with updated positions
rectangles = {
    'Y1': [(100, 50), (225, 100)],  # moved left
    'Y2': [(100, 25), (225, 50)],   # moved left and adjusted coordinates
    'Y3': [(100, 0), (225, 25)],    # moved left and adjusted coordinates
    '-Y1': [(100, 225), (225, 275)],  # moved left and up
    '-Y2': [(100, 275), (225, 300)],  # moved left and up
    '-Y3': [(100, 300), (225, 325)],  # moved left and up
    'X1': [(225, 100), (275, 225)],  # narrowest and moved left
    'X2': [(275, 100), (300, 225)],  # medium and moved left
    'X3': [(300, 100), (325, 225)],  # widest and moved left
    '-X1': [(50, 100), (100, 225)],   # moved left
    '-X2': [(25, 100), (50, 225)],    # moved left
    '-X3': [(0, 100), (25, 225)],     # moved left
    'Up': [(400, 50), (450, 100)],     # moved left
    'Down': [(450, 50), (500, 100)],     # moved left
    'Pick': [(580, 50), (620, 150)],     # moved left
    'Place': [(580, 150), (620, 250)]     # moved left
}


# Command mapping
commands = {
    'Y1': 'G21G91 Y0.5',
    'Y2': 'G21G91 Y1',
    'Y3': 'G21G91 Y2',
    '-Y1': 'G21G91 Y-0.5',
    '-Y2': 'G21G91 Y-1',
    '-Y3': 'G21G91 Y-2',
    'X1': 'G21G91 X0.5',
    'X2': 'G21G91 X1',
    'X3': 'G21G91 X2',
    '-X1': 'G21G91 X-0.5',
    '-X2': 'G21G91 X-1',
    '-X3': 'G21G91 X-2',
    'Up': 'G21G91 Z 1',
    'Down': 'G21G91 Z -1',
    'Pick': 'M4',
    'Place': 'M3'
}

def is_point_in_rectangle(pt, rect):
    """ Check if a point (pt) is inside a rectangle (rect) """
    return rect[0][0] <= pt[0] <= rect[1][0] and rect[0][1] <= pt[1] <= rect[1][1]

def adjust_speed(distance):
    global speed
    # Map the distance to a speed value
    speed = max(min_speed, min(max_speed, distance * max_speed / 100))
    print(f"Adjusted speed: {speed}")

def is_hand_fisted(hand_landmarks):
    """Check if the hand is in a fist gesture."""
    thumb_tip = hand_landmarks.landmark[handsModule.HandLandmark.THUMB_TIP]
    index_finger_tip = hand_landmarks.landmark[handsModule.HandLandmark.INDEX_FINGER_TIP]
    middle_finger_tip = hand_landmarks.landmark[handsModule.HandLandmark.MIDDLE_FINGER_TIP]
    ring_finger_tip = hand_landmarks.landmark[handsModule.HandLandmark.RING_FINGER_TIP]
    pinky_tip = hand_landmarks.landmark[handsModule.HandLandmark.PINKY_TIP]

    # Check if the distances between fingertips and palm base are small (fist gesture)
    threshold = 0.03
    return (thumb_tip.y < index_finger_tip.y + threshold and
            thumb_tip.y < middle_finger_tip.y + threshold and
            thumb_tip.y < ring_finger_tip.y + threshold and
            thumb_tip.y < pinky_tip.y + threshold)

with handsModule.Hands(static_image_mode=False, min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1) as hands:
    while True:
        ret, frame = cap.read()
        frame1 = cv2.resize(frame, (640, 480))
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time
        font = cv2.FONT_HERSHEY_SIMPLEX
        fps = int(fps)
        fps = str(fps)

        flipped_frame = cv2.flip(frame1, 1)  # Always flip the frame

        results = hands.process(cv2.cvtColor(flipped_frame, cv2.COLOR_BGR2RGB))  # Process the flipped frame

        # Putting text on the flipped frame (moved FPS display to the right)
        cv2.putText(flipped_frame, f"FPS: {fps}", (screen_width - 150, 40), font, 1, (0, 0, 255), 2, cv2.LINE_AA)


        index_finger_tip = None
        thumb_tip = None

        if results.multi_hand_landmarks is not None:
            for hand_landmarks in results.multi_hand_landmarks:
                drawingModule.draw_landmarks(flipped_frame, hand_landmarks, handsModule.HAND_CONNECTIONS)

                if not is_hand_fisted(hand_landmarks):  # Only process fingertips if hand is not fisted
                    for point in handsModule.HandLandmark:
                        normalized_landmark = hand_landmarks.landmark[point]
                        pixel_coordinates_landmark = drawingModule._normalized_to_pixel_coordinates(
                            normalized_landmark.x, normalized_landmark.y, 640, 480)

                        if point == handsModule.HandLandmark.INDEX_FINGER_TIP:
                            index_finger_tip = pixel_coordinates_landmark
                        elif point == handsModule.HandLandmark.THUMB_TIP:
                            thumb_tip = pixel_coordinates_landmark

                    if index_finger_tip and thumb_tip:
                        # Calculate the distance between the index finger tip and thumb tip
                        distance = np.linalg.norm(np.array(index_finger_tip) - np.array(thumb_tip))

                        # If pinching inside the regulator area, adjust the speed
                        if is_point_in_rectangle(index_finger_tip, regulator) and is_point_in_rectangle(thumb_tip, regulator):
                            adjust_speed(distance)

                        if index_finger_tip is not None and (time.time() - last_command_time) > speed:
                            # Check which rectangle the finger is in
                            for name, rect in rectangles.items():
                                if is_point_in_rectangle(index_finger_tip, rect):
                                    send_command(commands[name])
                                    last_command_time = time.time()
                                    break

        # Draw the rectangles and labels on the frame
        for name, rect in rectangles.items():
            cv2.rectangle(flipped_frame, rect[0], rect[1], (255, 0, 0), 2)
            centroid = (int((rect[0][0] + rect[1][0]) / 2), int((rect[0][1] + rect[1][1]) / 2))
            cv2.putText(flipped_frame, name, centroid, font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

        # Draw the regulator
        cv2.rectangle(flipped_frame, regulator[0], regulator[1], (0, 255, 0), 2)
        cv2.putText(flipped_frame, f"Speed: {speed:.2f}s", (regulator[0][0] + 10, regulator[0][1] + 30), font, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

        cv2.imshow("Final Frame", flipped_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()