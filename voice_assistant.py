from google.cloud import texttospeech_v1
from playsound import playsound
import os
import threading
import speech_recognition as sr
import config as c


class VoiceAssistant:
    """
    Class object for voice assistant
    """
    def __init__(self):
        # Define json file for google cloud credentials (file was manually downloaded from cloud.google.com console)
        print('...Assigning google cloud credentials')
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = c.api_key
        # Initialise text to speech client
        print('...Assigning text-to-speech client')
        self.client = texttospeech_v1.TextToSpeechClient()
        self.response_file = 'response.mp3'
        # Check and remove response_file if already existing
        os.remove(self.response_file) if os.path.isfile(self.response_file) else None
        # Initialize the speech recognizer and microphone for listening
        print('...Assigning google speech recognition variables')
        self.r = sr.Recognizer()
        self.mic = sr.Microphone()
        # Adjust for background noise
        with self.mic as source:
            print("...Calibrating microphone")
            # Adjust microphone for ambient noise and dynamically adjust on ongoing basis
            self.r.adjust_for_ambient_noise(source, duration=2)
            self.r.dynamic_energy_threshold = True
        # Define flag so unknown command and unheard utterance don't cause repetitive statements
        self.unheard = 0
        # Define Surah's keyword response dictionary
        self.dict = dict(startup="Startup complete. AI assistant operational. Activate me by saying my name: Surah.",
                         surah="This is Surah. How can I help?",
                         intro="My name is Surah and I am an artificially intelligent assistant for the blind and \
                                partially sighted. I can scan your camera's field of vision to detect objects and help \
                                guide your hand towards your selected object. I hope you enjoy today's demonstration.",
                         scan="Scanning.",
                         detections="I have detected the following.",
                         detections_complete="To select an object just say select followed by an object I named. \
                                For example. Select cell phone.",
                         no_detections="No items have been detected.",
                         no_scan="There are no objects in my memory. You cannot select undetected objects. \
                                Ask me to scan if you are looking for something.",
                         detections_memory="Sure no problem. I detected the following objects.",
                         invalid_selection="I'm sorry. You have selected an object that I have not detected. \
                                Ask me to scan again if you not sure what you are looking for.",
                         multiple_selection="I'm sorry. You have selected more than 1 object. \
                                Select a single object or ask me to scan again.",
                         selection_made="Once your hand enters the camera's field of view I will guide your hand \
                                towards the selected object.",
                         detect_more="Do you need me to detect anything else? If so, just use the scan keyword.",
                         awake="Yes. I am still here. How can i be of assistance?",
                         sleep="Going to sleep. Just call my name if you need me again.",
                         exit="Program ending. I'll talk to you next time.",
                         unheard="Sorry. I didn't catch that. What did you say?",
                         unknown="Sorry. I didn't recognise that command. What did you say?",
                         acquired="Target acquired.",
                         guide_comp="Guidance complete. Returning to inner control loop.",
                         reset_cam="Resetting camera. Please wait a few seconds.",
                         reset_comp="Reset complete. Would you like help with anything else?")
        # Declare voice assistant operational as final step
        self.operational = True
        # self.awake used to avoid giving unknown/unheard error when she is asleep
        self.awake = False

    def respond(self, text, is_thread):
        """
        Define function for calling Surah's cloud_google_tts response engine
        Receives text input to generate response on google cloud text-to-speech
        Option to play response on separate thread (to avoid frame interruption)
        """
        response = self.client.synthesize_speech(  # Define REST json for desired response
            request={
                "audio_config": {"audio_encoding": "MP3", "pitch": -2.8, "speaking_rate": 1.15},
                "input": {"text": text},
                "voice": {"language_code": "en-IN", "name": "en-IN-Wavenet-D"}
            }
        )
        # Write response to file
        with open('response.mp3', 'wb') as output:
            output.write(response.audio_content)
        print('...Response received from google cloud and saved')
        # Check if threading is required for response
        if is_thread:
            self.thread()
        else:
            self.speak()
        print('...Response delivered to user and file removed')

    # For a smooth cam feed, use a separate thread to avoid GIL conflicts
    def thread(self):
        """ Optional threading for use when guidance system (video) is running """
        t1 = threading.Thread(target=self.speak)
        t1.start()

    def speak(self):
        """ Plays response file and then deletes ready for next response """
        # Play audio and cleanup
        playsound(self.response_file)
        os.remove(self.response_file)

    # Define function for Surah's google speech recognition
    def capture_input(self):
        """ Uses Google Audio for speech recognition """
        # Each speech loop resets the unheard to zero for efficient error handling
        self.unheard = 0
        with self.mic as source:
            request = self.r.listen(source)
            speech: str = ''  # Initialise speech capture variable in case no speech is detected
            try:  # Convert speech into text
                speech = self.r.recognize_google(request, language='en-gb')
                print(f"...User said: {speech}")
            # With full integration this line yields double unknown response as covered in main.py inner control loop
            except sr.UnknownValueError:
                if self.awake:
                    self.respond(surah.dict['unheard'], 0)
                    self.unheard = 1
                else:
                    print("...User utterance not understood")
            except sr.RequestError:
                # Play offline file when no internet connectivity
                playsound('offline_response/no_internet.mp3')
                print("\nSurah cannot connect to the internet. The program does not exit automatically.")
            return speech


# ------------------------------------------------------------------------------
# Initialise voice assistant
print("\nInitialise voice assistant")
print("...Creating voice assistant object")
surah = VoiceAssistant()
print("Voice assistant initialised")