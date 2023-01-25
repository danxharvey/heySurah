import mediapipe as mp
from cv2 import cvtColor, COLOR_BGR2RGB, line
import config as c


def track_hand(frame, hands):
    """ This is a doc string """

    # Convert frame for mediapipe
    image = cvtColor(frame, COLOR_BGR2RGB)
    # Set writeable flag to false for improved performance
    image.flags.writeable = False
    # Perform hand detections
    results = hands.process(image)
    return results


def draw_landmarks(frame, results, selection):
    """ This is a doc string """

    # Create empty list of landmarks
    landmark_list = []

    if results.multi_hand_landmarks:
        for idx, hand in enumerate(results.multi_hand_landmarks):
            mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS,
                                      mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                                      mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2, circle_radius=2),)

            # Draw lines from all landmarks to selected target and create a list of landmark coordinates
            target_x = int(round(selection[0] + (selection[2] / 2), 0))
            target_y = int(round(selection[1] + (selection[3] / 2), 0))
            for idx2, landmark in enumerate(hand.landmark):
                landmark_list.append([idx2, int(landmark.x * c.cam_width), int(landmark.y * c.cam_height)])
                line(frame, (int(hand.landmark[idx2].x * c.cam_width), int(hand.landmark[idx2].y * c.cam_height)),
                     (target_x, target_y), (255, 0, 0), 1)

    return landmark_list


# ------------------------------------------------------------------------------
# Initialise hand tracker
print("\nCreating hand tracker object")
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
print("Hand tracker created")