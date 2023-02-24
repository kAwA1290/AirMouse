import cv2
import time
import pyautogui as pag
import mediapipe as mp
import math

pag.FAILSAFE = False
pag.MINIMUM_DURATION = 0.0

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

def get_hand_landmarks(results):
    if results.multi_handedness is None:
        return None
    multi_hand_landmarks = results.multi_hand_landmarks
    multi_handedness = results.multi_handedness

    hands_labels = [item.classification[0].label for item in multi_handedness if item.classification[0].label]

    if len(hands_labels) == 1:
        hands_index = 0
    else:
        if 'Right' in hands_labels and len(set(hands_labels)) == 2:
            hands_index = hands_labels.index('Right')
        else:
            return None
    hand_landmarks = multi_hand_landmarks[hands_index]
    return hand_landmarks

def th_check(value, min_th, max_th):
    if value < min_th:
        return -1
    if value > max_th:
        return 1
    return 0

def landmark_to_location(landmark, width, height, min_th, max_th):
    x_out_of_range = th_check(landmark.x, min_th, max_th)
    y_out_of_range = th_check(landmark.y, min_th, max_th)
    if x_out_of_range == 1:
        landmark.x = 1
    elif x_out_of_range == -1:
        landmark.x = 0
    if y_out_of_range == 1:
        landmark.y = 1
    elif y_out_of_range == -1:
        landmark.y = 0
    # flip and align to window size
    aligned_x = width - ((landmark.x - min_th) * (1 / (max_th - min_th))) * width
    aligned_y = ((landmark.y - min_th) * (1 / (max_th - min_th))) * height
    location = {'x': aligned_x, 'y': aligned_y, 'z': landmark.z}
    return location

def landmark_to_distance(landmark_a, landmark_b):
    distance_x = (landmark_a.x - landmark_b.x) ** 2
    distance_y = (landmark_a.y - landmark_b.y) ** 2
    distance = math.sqrt(distance_x + distance_y)
    return distance

def move_mouse(location, interval):
    if not location is None:
        try:
            pag.moveTo(location['x'], location['y'], duration=interval)
        except:
            pass

def air_mouse():
    cap = cv2.VideoCapture(0)
    with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:
        fingers = {
                'thumb': {
                    'x': 0.0, 'y': 0.0
                    },
                'index': {
                    'x': 0.0, 'y': 0.0
                    },
                'middle': {
                    'x': 0.0, 'y': 0.0
                    },
                'ring': {
                    'x': 0.0, 'y': 0.0
                    }
                }
        prev_fingers = fingers.copy()
        gestures = {'scroll': False, 'pinch': False}
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(image)

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            if results.multi_hand_landmarks:
                hand_landmarks = get_hand_landmarks(results)
                if hand_landmarks:
                    for i, k in zip(range(4, 17, 4), fingers):
                        fingers[k] = hand_landmarks.landmark[i]

                    width, height = pag.size()

                    thumb_middle_distance = landmark_to_distance(fingers['thumb'], fingers['middle'])
                    index_middle_distance = landmark_to_distance(fingers['index'], fingers['middle'])
                    thumb_ring_distance = landmark_to_distance(fingers['thumb'], fingers['ring'])

                    if thumb_middle_distance < 0.04:
                        pag.click()
                        print('clicked')
                        print(thumb_middle_distance)
                    elif index_middle_distance < 0.07 and thumb_ring_distance < 0.07:
                        if gestures['scroll']:
                            scroll_range = prev_fingers['index'].y - fingers['index'].y
                            print('scrolled', scroll_range)
                            pag.scroll(-scroll_range * (height / 10))
                        else:
                            print('scroll_false')
                            gestures['scroll'] = True
                    else:
                        for k in gestures:
                            gestures[k] = False
                        location = landmark_to_location(fingers['index'], width, height, 0.1, 0.9)
                        move_mouse(location, 0)
                        prev_fingers = fingers.copy()
            if cv2.waitKey(5) & 0xFF == 27:
                break
    cap.release()
air_mouse()
