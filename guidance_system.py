from sys import exit
from cv2 import putText, FONT_HERSHEY_SIMPLEX, line
from numpy import sqrt, min
from serial import Serial
from winsound import Beep
import config as c
import voice_assistant as va


def open_glove(com_port=c.com_port):
    """ Opens connection to CS Vibrating Glove """
    return Serial(com_port)


def close_glove():
    """ Closes connection to CS Vibrating Glove """
    ser.close()
    print("Glove connection closed")


def buzz(loc, dur=500):
    """
    Buzz given location for given duration in ms
    location codes:  t, b, l, r, tr, br, bl, tl
    """
    loc_ar = {'fw': '1000', 'r': '0100', 'bw': '0010', 'l': '0001',
              'tr': '1100', 'br': '0110', 'bl': '0011', 'tl': '1001'}
    com = loc_ar[loc] + 'buzz' + str(dur) + '.'
    ser.write(str.encode(com))
    print("Buzzer instructions delivered to glove")


def calc_min_dist(frame, landmarks, selection):
    """ Calculates distance from landmark to target and identifies minimum distance landmark """
    print("...Calculating minimum distance")
    # Create results list
    dists = [0]*len(landmarks)

    # Calculate distance to selected target for all landmarks
    for idx, lm in enumerate(landmarks):
        dists[idx] = int(round(sqrt((lm[1]-(selection[0]+(selection[2]/2)))**2 +
                                    (lm[2]-(selection[1]+(selection[3]/2)))**2), 0))

    # Add shortest distance to screen, highlight track in red and print to console
    putText(frame, f'Distance: {min(dists)}px', (125, 25), FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0))
    target_distance = min(dists)
    target_x = int(round(selection[0]+(selection[2]/2), 0))
    target_y = int(round(selection[1]+(selection[3]/2), 0))
    print(f"...target_x: {target_x}, target_y: {target_y}")
    closest_landmark = landmarks[dists.index(min(dists))]
    line(frame, (closest_landmark[1], closest_landmark[2]), (target_x, target_y), (0, 0, 255), 2)
    print(f'...Minimum distance is {target_distance} with landmark {c.mp_dict[dists.index(min(dists))]}')
    print(f'...Coordinates of closest landmark are: {closest_landmark}')

    # Return coordinates of shortest distance
    return closest_landmark, target_distance


def dir_to_target(closest_landmark, target):
    """ Calculates the required directional feedback to target """

    target_x = int(round(target[0]+(target[2]/2), 0))
    target_y = int(round(target[1]+(target[3]/2), 0))
    # Determine guidance direction for x coordinate
    if closest_landmark[1] < target_x - c.target_tolerance:
        a = "r"
    elif closest_landmark[1] > target_x + c.target_tolerance:
        a = "l"
    else:
        a = 'x'

    # Determine guidance direction for y coordinate
    if closest_landmark[2] < target_y - c.target_tolerance:
        b = "bw"
    elif closest_landmark[2] > target_y + c.target_tolerance:
        b = "fw"
    else:
        b = 'y'

    print("Directions to target calculated")
    return a, b


def guidance_feedback(closest_landmark, target_distance, target):
    """
    Delivers the directional feedback to the user
    Commenting out "c.guide_hand = 0" will allow you to keep the guidance window open on target acquired
    Very useful if experimenting with how it works and how tolerance parameters might be adjusted
    """

    # Calculate required x and y movements to reach target
    x, y = dir_to_target(closest_landmark, target)

    # Guide hand when in glove mode
    if c.guidance_mode == 'glove':
        print("\nEntering glove guidance loop")
        if target_distance < c.target_tolerance:
            print(f"Target acquired")
            va.surah.respond(va.surah.dict['acquired'], 1)
            c.guide_hand = 0
        else:
            print(f"x: {guidance_dict[x]}, y: {guidance_dict[y]}")
            buzz(x, 200) if x != 'x' else None
            buzz(y, 200) if y != 'y' else None

    # Guide hand when in voice mode
    elif c.guidance_mode == 'voice':
        print("\nEntering voice guidance loop")
        if target_distance < c.target_tolerance:
            print(f"Target acquired")
            va.surah.respond(va.surah.dict['acquired'], 1)
            c.guide_hand = 0
        else:
            print(f"x: {guidance_dict[x]}, y: {guidance_dict[y]}")
            if x == 'x':
                va.surah.respond(guidance_dict[y], 1)
            elif y == 'y':
                va.surah.respond(guidance_dict[x], 1)
            else:
                va.surah.respond(guidance_dict[y] + " " + guidance_dict[x], 1)

    # Guide hand when in beep mode
    elif c.guidance_mode == 'beep':
        print("\nEntering beep guidance loop")
        if target_distance < c.target_tolerance:
            print(f"Target acquired")
            va.surah.respond(va.surah.dict['acquired'], 1)
            c.guide_hand = 0
        else:
            freq = 3000 - (3*int(target_distance))
            Beep(freq, c.beep_duration)


# ------------------------------------------------------------------------------
# Initialise guidance parameters
print("\nInitialising guidance system module parameters")
# Open glove connection if using glove mode
if c.guidance_mode == 'glove':
    try:
        ser = open_glove()
        print("Glove connection opened")
    except OSError as err:
        print("\nOS error: {0}".format(err))
        print("Could not connect to glove. Please check that the glove is switched on and has battery power.\n")
        exit()      # sys.exit as per best practice for production code

# Define directional logging dictionary
print("...Creating guidance dictionary")
guidance_dict = dict(l="left", r="right", fw="forwards", bw="backwards", t="up", b="down",
                     x="x coordinate acquired", y="y coordinate acquired")
print("Guidance system initialised")