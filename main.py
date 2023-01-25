from sys import exit
import cv2
import config as c
import voice_assistant as va                  # Custom module for voice assistant
import object_detect as ssd                   # Custom module for SSD mobilenet
import guidance_system as gs                  # Custom module for hand guidance system
import video_thread as vt                     # Custom module for video threading solution
print("\nAll module dependencies initialised")

# Check guidance mode contains a valid value
print("\nChecking guidance parameter")
if c.guidance_mode in c.guidance_options:
    print(f"Guidance parameter validated: {c.guidance_mode} selected")
else:
    print("Invalid selection on guidance mode parameter. Check config file.")
    exit()      # sys.exit as per best practice for production code

# # Initialise camera
cap = vt.assign_base_cam()

# Voice confirmation of system initialisation
print("\nStartup completed")
va.surah.respond(va.surah.dict['startup'], 0)
print("User informed of startup completion")

# Run until Surah is set to surah.operational = False
while va.surah.operational:

    # Capture voice input
    print("\nListening for user input")
    request = va.surah.capture_input()

    # --------------------------------------------------------------------------------------
    # Option to exit without waking Surah
    if 'exit' in request:
        print("\nSurah says goodbye and the program ends")
        va.surah.respond(va.surah.dict['exit'], 0)
        va.surah.operational = False

    # --------------------------------------------------------------------------------------
    # Check for Surah trigger word
    if 'Surah' in request:
        va.surah.respond(va.surah.dict['surah'], 0)
        va.surah.awake = True
        print("\nSurah is awake")

        # --- INNER CONTROL LOOP STARTS HERE ---
        while va.surah.awake:

            # Capture voice input for next request
            print("\nListening for user input")
            request = va.surah.capture_input()

            # If statement controls the flow of the interaction between Surah and the user
            # ------------------------------------------------------------------------------
            if 'introduce yourself' in request:
                print("\nSurah introduces herself")
                va.surah.respond(va.surah.dict['intro'], 0)

            # ------------------------------------------------------------------------------
            elif 'scan' in request:
                print("\nDetecting objects")
                va.surah.respond(va.surah.dict['scan'], 0)
                print("...Clearing previous detection data")
                ssd.detections.clear_previous_detections()

                # Access cam feed from background and make single frame detection
                _, frame = cap.read()
                ssd.detections.get_detections(frame)

                # Provide user with results of object detect request
                print(f"...Number of objects detected: {len(ssd.detections.detected_ids)}")
                print(f"\t{ssd.detections.detected_names}") if len(ssd.detections.detected_ids) > 0 else None
                if len(ssd.detections.detected_ids) == 0:
                    va.surah.respond(va.surah.dict['no_detections'], 0)
                else:
                    va.surah.respond(va.surah.dict['detections'], 0)
                    for name in ssd.detections.detected_names:
                        va.surah.respond(name, 0)
                    va.surah.respond(va.surah.dict['detections_complete'], 0)
                    print("Detection complete")

            # ------------------------------------------------------------------------------
            # Repeat list of detected objects
            elif 'list' in request:
                print("\nRepeating list of detected objects")
                va.surah.respond(va.surah.dict['detections_memory'], 0)
                for name in ssd.detections.detected_names:
                    va.surah.respond(name, 0)
                print("Repeat list of detections complete")

            # ------------------------------------------------------------------------------
            # Object selection and guidance system loop
            elif 'select' in request:
                print("\nSelecting an object")
                # Check scan has been performed.
                if len(ssd.detections.detected_ids) == 0:
                    print("...Can't select an object as scan not yet performed")
                    va.surah.respond(va.surah.dict['no_scan'], 0)
                else:
                    # Check each entry in detected objects to see if it is selected (boolean vector)
                    if ssd.detections.validate_object_selection(request) == 0:
                        print("...Invalid object selection")
                        va.surah.respond(va.surah.dict['invalid_selection'], 0)
                        print("Object selection complete")
                    elif ssd.detections.validate_object_selection(request) == 2:
                        print("...Multiple object selection")
                        va.surah.respond(va.surah.dict['multiple_selection'], 0)
                        print("Object selection complete")
                    else:
                        print(f'...{ssd.detections.selected_object} selected')
                        va.surah.respond(ssd.detections.selected_object + " selected.", 0)
                        va.surah.respond(va.surah.dict['selection_made'], 1)
                        print("Object selection complete")

                        # Start showing video frames
                        print("\nEntering guidance system")
                        vt.thread_video_show()
                        print("\nGuidance complete")

                        # Reassign camera variables due to persistence issue
                        print("\nResetting cap variable due to persistence issue with multi-threading")
                        va.surah.respond(va.surah.dict['reset_cam'], 1)
                        cap = vt.assign_base_cam()
                        va.surah.respond(va.surah.dict['reset_comp'], 0)
                        print("Reset complete")

            # ------------------------------------------------------------------------------
            elif 'awake' in request:
                print("\nSurah confirms she is still awake")
                va.surah.respond(va.surah.dict['awake'], 0)

            # ------------------------------------------------------------------------------
            # Send Surah to sleep without exiting the program. Background listens for trigger
            elif 'sleep' in request:
                print("\nSurah informs she is going to sleep")
                va.surah.respond(va.surah.dict['sleep'], 0)
                va.surah.awake = False

            # ------------------------------------------------------------------------------
            elif 'exit' in request:
                print("\nSurah says goodbye and the program ends")
                va.surah.respond(va.surah.dict['exit'], 0)
                va.surah.awake = False
                va.surah.operational = False

            # ------------------------------------------------------------------------------
            # If utterance does not contain a known command give error
            # Flag provided so that unrecognised speech capture error is not duplicated
            else:
                print("\nVoice assistant reports unknown user request")
                va.surah.respond(va.surah.dict['unknown'], 0) if va.surah.unheard == 0 else None


# Close glove connection if using glove mode
gs.close_glove() if c.guidance_mode == 'glove' else None

# Release cap and destroy camera window
cap.release()
cv2.destroyAllWindows()
print("\nCamera windows destroyed")

# Destroy objects
del ssd.detections, va.surah
print("All objects deleted")
print("Program ended successfully")
exit()