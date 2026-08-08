import requests
import numpy as np
import sounddevice as sd
from piper import PiperVoice
from playsound3 import playsound


url = "http://192.168.1.83:8000"
file_path = "test.jpg"

# Seconds to wait on the API before giving up. Stockfish gets a second per
# analysis, so the read has to be comfortably longer than that.
TIMEOUT = 15

model_path = "voice-models/en_US-arctic-medium.onnx"
voice = PiperVoice.load(model_path)



def speak(message):
	for chunk in voice.synthesize(message):
		audio_data = np.frombuffer(chunk.audio_int16_bytes, dtype = np.int16)

		sd.play(audio_data, samplerate =22050)
		sd.wait()

def test_route():
	response = requests.get(url + "/", timeout = TIMEOUT)
	print(response.json())

# Post the last captured photo to an endpoint and return its message. Returns
# None if the API could not be reached, so a dropped request never takes the
# voice loop down with it.
def _post_photo(endpoint):
	try:
		with open(file_path, 'rb') as f:
			files = {'file': (file_path, f, 'image/jpeg')}
			response = requests.post(url + endpoint, files = files, timeout = TIMEOUT)
		return response.json().get("message", "An error occured, please try again")
	except requests.exceptions.RequestException as e:
		print(f"Request to {endpoint} failed: {e}")
		return None

def _get(endpoint):
	try:
		response = requests.get(url + endpoint, timeout = TIMEOUT)
		return response.json().get("message", "An error occured, please try again")
	except requests.exceptions.RequestException as e:
		print(f"Request to {endpoint} failed: {e}")
		return None

def initialize_board():
	message = _post_photo("/initialize")
	speak(message if message else "I could not reach the chess server")

def update_position():
	message = _post_photo("/update_position")

	if message is None:
		speak("I could not reach the chess server")
	elif message == "Success":
		# Fall back to speech if the chime is missing, rather than dying
		try:
			playsound("audio-output/success.mp3")
		except Exception as e:
			print(f"Could not play success chime: {e}")
			speak("Move accepted")
	else:
		speak(message)

def get_best_move():
	message = _get("/best_move")
	speak(message if message else "I could not reach the chess server")

def analyze_board():
	message = _get("/analyze_position")
	speak(message if message else "I could not reach the chess server")


