# CAMERA PARAMETERS -------------------------------------------------------------------------------
cam_src: int = 1                        # 0 for laptop cam - requires uncommenting of flip screen code
cam_width: int = 640
cam_height: int = 480

# OBJECT DETECTION PARAMETERS ---------------------------------------------------------------------
ssd_dataset: str = 'ssd/coco.names'                 # Class names for SSD object detect
configPath: str = 'ssd/ssd_mobilenet_v3.pbtxt'      # SSD config file
weightsPath: str = 'ssd/inference_graph.pb'         # SSD weights file
detect_thresh: float = 0.45             # Probability threshold for object detection
nms_thresh: float = 0.2                 # Non-Max Suppression probability threshold
num_coco_class_names: int = 91          # Current downloaded version has 91 class names

# HAND TRACKING PARAMETERS ------------------------------------------------------------------------
mp_detect_conf: float = 0.75            # Mediapipe hand detection probability threshold
mp_track_conf: float = 0.4              # Mediapipe tracking probability threshold
max_hands: int = 1                      # Maximum number of hands to detect

# GUIDANCE SYSTEM PARAMETERS ----------------------------------------------------------------------
guidance_options: tuple = ('glove', 'voice', 'beep', 'none')
guidance_mode: str = 'voice'            # none: No guidance gives fastest visual feedback of system
com_port: str = "COM5"                  # COM port for glove connection
target_tolerance: int = 40              # Pixel proximity to assume target is acquired (helps with 2D limitations)
beep_duration: int = 200                # Duration of beeps in milliseconds
guide_hand: int = 1                     # Temp mechanism for ending guidance loop

# MEDIAPIPE LANDMARK DICTIONARY (CAN BE USED FOR FUTURE CUSTOMISING OF LANDMARK CALCULATIONS)
mp_dict: dict = {0: "wrist", 1: "thumb cmc", 2: "thumb mcp", 3: "thumb ip", 4: "thumb tip",
                 5: "index finger mcp", 6: "index finger pip", 7: "index finger dip", 8: "index finger tip",
                 9: "middle finger mcp", 10: "middle finger pip", 11: "middle finger dip", 12: "middle finger tip",
                 13: "ring finger mcp", 14: "ring finger pip", 15: "ring finger dip", 16: "ring finger tip",
                 17: "pinky finger mcp", 18: "pinky finger pip", 19: "pinky finger dip", 20: "pinky finger tip"}

# VOICE ASSISTANT PARAMETERS ----------------------------------------------------------------------
api_key: str = 'cloud-tts-api-key/a-guiding-hand-service-account.json'      # API key file for Google Cloud