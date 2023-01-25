from threading import Thread
from datetime import datetime
from time import sleep
from keyboard import press_and_release
import os
import cv2
import config as c
import hand_track as ht
import guidance_system as gs
import object_detect as ssd
import voice_assistant as va


def assign_base_cam():
    """ Assigns background cam feed for object detections """
    print("\nInitialising camera parameters")
    cap = cv2.VideoCapture(c.cam_src)
    cap.set(3, c.cam_width)
    cap.set(4, c.cam_height)
    print("Camera parameters initialised")
    return cap


class CountsPerSec:
    """
    Class that tracks the number of occurrences ("counts") of an
    arbitrary event and returns the frequency in occurrences
    (counts) per second. The caller must increment the count.
    """
    def __init__(self):
        self._start_time = None
        self.num_occurrences = 0

    def start(self):
        self._start_time = datetime.now()
        return self

    def increment(self):
        self.num_occurrences += 1

    def fps(self):
        elapsed_time = (datetime.now() - self._start_time).total_seconds()
        return self.num_occurrences / elapsed_time


def put_iterations_per_sec(frame, iterations_per_sec):
    """ Draws the frame rate """
    cv2.putText(frame, "FPS: {:.0f}".format(iterations_per_sec),
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0))
    return frame


class VideoShow:
    """ Class that continuously shows a frame using a dedicated thread """
    def __init__(self, frame=None):
        """ Initialises camera feed object """
        self.frame = frame
        self.stopped = False

    def start(self):
        """ Starts new thread """
        Thread(target=self.show, args=()).start()
        return self

    def show(self):
        """ Shows frames """
        while not self.stopped:
            cv2.imshow('Cam Feed', self.frame)
            self.stopped = True if (cv2.waitKey(1) & 0xFF == ord("q")) else None

    def stop(self):
        """ Stops cam feed """
        self.stopped = True


def thread_video_show():
    """
    Dedicated thread for showing video frames with VideoShow object
    Main thread grabs video frames
    """
    print("\nInitialising guidance camera parameters")
    guide_cap = cv2.VideoCapture(c.cam_src)
    guide_cap.set(3, c.cam_width)
    guide_cap.set(4, c.cam_height)
    # out = cv2.VideoWriter_fourcc(*'mp4')
    # guide_out = cv2.VideoWriter('output.mp4', out, 20.0, (c.cam_width, c.cam_height))
    print("Guidance camera parameters initialised")

    (grabbed, frame) = guide_cap.read()
    video_shower = VideoShow(frame).start()
    cps = CountsPerSec().start()

    # Set c.guide_hand to True
    c.guide_hand = 1

    # Define "hands" outside of guidance loop for efficiency
    with ht.mp_hands.Hands(min_detection_confidence=c.mp_detect_conf,
                           min_tracking_confidence=c.mp_track_conf,
                           max_num_hands=c.max_hands) as hands:

        # repeat loop whilst hand guidance is true
        while c.guide_hand == 1:
            (grabbed, frame) = guide_cap.read()
            # If using laptop webcam uncomment to flip image selfie style
            # frame = cv2.flip(frame, 1)

            if not grabbed or video_shower.stopped:
                video_shower.stop()
                break

            frame = put_iterations_per_sec(frame, cps.fps())
            video_shower.frame = frame

            # SELECTED OBJECT START
            if cps.num_occurrences == 0:
                ssd.detections.initialise_tracker(frame)

            # HAND DETECTION START ----------------------------------------------------------------
            if cps.num_occurrences % 2 == 0:       # Detect hand every x frames as laptop is slow
                print("\nTracking hands")
                results = ht.track_hand(frame, hands)
                print("Hand track complete")
            # HAND DETECTION END ------------------------------------------------------------------

            # SELECTED OBJECT TRACKING START ----------------------------------------------------------------
            print("\nTracking target")
            ssd.detections.track_thread(frame)
            print("Target track complete")
            # SELECTED OBJECT TRACKING END ------------------------------------------------------------------

            # FRAME DRAWING START -----------------------------------------------------------------
            # Result boxes drawn last to avoid confusion for object detectors
            print("\nDrawing landmarks")
            print("...Drawing hand landmarks")
            hand_landmarks = ht.draw_landmarks(frame, results, ssd.detections.selected_bound_box)
            print("...Drawing target landmarks")
            ssd.detections.draw_tracker(frame)
            print("Landmarks drawing complete")
            # FRAME DRAWING & DISTANCE CALCULATIONS END -------------------------------------------

            # GUIDANCE SYSTEM START ---------------------------------------------------------------
            # Check if landmarks have been detected before calling guidance system
            if len(hand_landmarks) > 0:
                # Calculate distance to target, call guidance function and direct user
                print("\nStarting frame guidance calculations")
                closest_lm, target_dist = gs.calc_min_dist(frame, hand_landmarks, ssd.detections.selected_bound_box)
                # If response_file exists then Surah is still speaking
                # 10fps for glove, 5 for voice
                if cps.num_occurrences % 10 == 0 and not os.path.isfile(va.surah.response_file):
                    gs.guidance_feedback(closest_lm, target_dist, ssd.detections.selected_bound_box)
                print("Frame guidance complete")
            # GUIDANCE SYSTEM END -----------------------------------------------------------------

            # Increment frame
            cps.increment()

    # Close window with simulated keystroke and release
    press_and_release('q')
    sleep(1)
    guide_cap.release()
    # guide_out.release()

    # While loop until previous speech has finished to avoid response file error
    while os.path.isfile(va.surah.response_file):
        sleep(1)
    print("\nReturning to inner control loop")
    va.surah.respond(va.surah.dict['guide_comp'], 0)
    return None