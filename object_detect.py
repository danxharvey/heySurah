from sys import exit
from numpy import array, where
import cv2
import threading
import config as c


def contains_word(detected_object, user_request):
    """
    Detects if a user selected object is in the detected objects list
    Returns True/False
    """
    return f"{detected_object.lower()}" in f"{user_request.lower()}"


class Detections:
    """
    Custom class for holding object detection results and selections
    Allows data to be accessed through various scopes
    """
    def __init__(self):
        """ Initialises object with all required variables """
        # Create variables for population upon detection
        self.coco_names = []            # Full class names list for SSD mobilenet model
        self.detected_ids = []          # Object IDs returned from SSD model
        self.detected_names = []        # Conversion of IDs into class names
        self.detections = []            # Object containing detection results data
        self.prob = []                  # Object detection confidence probability
        self.bound_box = []             # Bounding boxes
        self.selected_object = []       # Holds the user selected object for the guidance system
        self.selected_object_idx = []   # Holds the selection index for ease of access to bounding box data
        self.selected_bound_box = ()    # Holds bound box info for the selected object and requires tuple
        self.tracker = cv2.TrackerMOSSE_create()  # Defines tracker from opencv library
        self.guide_tracking = 0         # Flag to indicate active tracking during guidance

    def clear_previous_detections(self):
        """ Clears previous data ready for fresh detections """
        self.detected_ids = []
        self.detected_names = []
        self.prob = []
        self.bound_box = []
        self.detections = []
        self.selected_object = []
        self.selected_object_idx = []
        self.selected_bound_box = ()

    def get_detections(self, det_frame):
        """ Performs SSD-NMS and stores required data for later usage """
        # Make detections with SSD mobilenet model
        self.detected_ids, prob, bound_box = ssd.detect(det_frame, confThreshold=c.detect_thresh)
        # When using laptop selfie style cam you need to comment above and use this flipped line below
        # self.detected_ids, prob, bound_box = ssd.detect(cv2.flip(det_frame, 1), confThreshold=c.detect_thresh)
        self.prob = list(map(float, list(array(prob).reshape(1, -1)[0])))
        self.bound_box = list(bound_box)
        # Use Non-Max Suppression for higher quality detections
        self.detections = cv2.dnn.NMSBoxes(self.bound_box, self.prob, c.detect_thresh, c.nms_thresh)
        # Convert detected object IDs into readable names for Surah
        flat_list = [i for x in self.detected_ids for i in x]
        self.detected_names = [self.coco_names[i-1] for i in flat_list]

    def draw_detections(self, draw_frame):
        """ Draws the bounding boxes and class names of detected objects """
        print("\ndetections:", self.detected_names, self.detected_ids)
        for detection in self.detections:
            print(detection)
            i = detection[0]
            box = self.bound_box[i]
            x, y, w, h = box[0], box[1], box[2], box[3]
            cv2.rectangle(draw_frame, (x, y), (x + w, h + y), color=(0, 255, 0), thickness=2)
            cv2.putText(draw_frame, self.detected_names[i].upper(),
                        (box[0]+10, box[1]+30), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 1)

    def validate_object_selection(self, request):
        """ Checks if the user's selection in present in the list of detected objects """
        # Check each entry in detected objects to see if it is selected (boolean vector with single True
        selection = [None] * len(self.detected_ids)
        for idx, name in enumerate(self.detected_names):
            selection[idx] = contains_word(name, request)
        # Check a valid selection is made and return result (should only be single True)
        if sum(selection) == 0:
            return 0
        elif sum(selection) > 1:
            return 2
        else:
            # Store selection
            self.selected_object_idx = int(where(selection)[0])
            self.selected_object = self.detected_names[self.selected_object_idx]
            self.selected_bound_box = tuple(self.bound_box[self.selected_object_idx])
            return 1

    def initialise_tracker(self, track_frame):
        """ Initialises tracker """
        # Initialise tracker
        self.tracker.init(track_frame, self.selected_bound_box)
        print("\nObject tracker initialised")

    def track(self, track_frame):
        """ Updates location of bounding box for tracked object """
        # Update tracker and convert float values to int
        success, bbox = self.tracker.update(track_frame)
        self.selected_bound_box = tuple(int(i) for i in bbox)
        print(f"...{self.selected_bound_box}")
        # record tracking status
        if success:
            cv2.putText(track_frame, "Tracking", (10, 50), cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 0, 0))
            print("...Tracking object")
        else:
            cv2.putText(track_frame, "Track Lost", (10, 50), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 255))
            print("...Not tracking, object lost")

    def draw_tracker(self, draw_frame):
        """ Draws updated bounding box for tracker """
        # Get selected object data
        cv2.rectangle(draw_frame, (self.selected_bound_box[0], self.selected_bound_box[1]),
                      (self.selected_bound_box[0] + self.selected_bound_box[2],
                       self.selected_bound_box[1] + self.selected_bound_box[3]),
                      color=(0, 255, 0), thickness=2)
        cv2.putText(draw_frame, self.selected_object,
                    (self.selected_bound_box[0]+10, self.selected_bound_box[1]+30),
                    cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 1)

    def track_thread(self, thread_frame):
        """ Starts a new thread for tracker so guidance processing can continue """
        t2 = threading.Thread(target=self.track(thread_frame))
        t2.start()


# ------------------------------------------------------------------------------
# Initialise SSD model
print("\nInitialising SSD object detection module parameters")
print("...Defining model and parameters")
ssd = cv2.dnn_DetectionModel(c.weightsPath, c.configPath)
ssd.setInputSize((320, 320))
ssd.setInputScale(1.0 / 127.5)
ssd.setInputMean((127.5, 127.5, 127.5))
ssd.setInputSwapRB(True)

print("...Creating object detection results object")
detections = Detections()
print("...Results object created")

# Load class names from file and validate
print("...Loading class names from coco dataset")
with open(c.ssd_dataset, 'rt') as f:
    detections.coco_names = f.read().rstrip('\n').split('\n')
print(f"...Class names: {detections.coco_names}")
if len(detections.coco_names) != c.num_coco_class_names:  # Allows for future customisation and configuration
    print("Class names from coco dataset not loaded. Exiting program")
    exit()
else:
    print(f"...All {c.num_coco_class_names} class names loaded")
    print("SSD object detection module initialised")


# Retain code for debugging in isolation
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    from time import perf_counter

    print("\nInitialising cam feed")
    cap = cv2.VideoCapture(c.cam_src)
    cap.set(3, 1280)
    cap.set(4, 720)
    frame_count = 0

    # Start cam feed
    while cap.isOpened():

        # Start timing and grab frame
        start = perf_counter()
        _, frame = cap.read()

        # Flip on horizontal for laptop cam only
        # frame = cv2.flip(frame, 1)

        # Detect every x frames but draw each time
        if frame_count % 2 == 0:
            detections.get_detections(frame)
        detections.draw_detections(frame)

        # Calculate actual FPS and print on screen
        end = perf_counter()
        fps = 1 / (end - start)
        cv2.putText(frame, f'FPS: {int(fps)}', (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)

        # Show current frame and increment frame count
        cv2.imshow('Output', frame)
        frame_count += 1

        # Check for end of cam loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release video capture and clean up
    cap.release()
    cv2.destroyAllWindows()
    del detections