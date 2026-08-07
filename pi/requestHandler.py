import requests
import numpy as np
import sounddevice as sd
from piper import PiperVoice
from playsound3 import playsound


url = "http://192.168.1.83:8000"
file_path = "test.jpg"

model_path = "pi/voice-models/en_US-arctic-medium.onnx"
voice = PiperVoice.load(model_path)



def speak(message):
	for chunk in voice.synthesize(message):
		audio_data = np.frombuffer(chunk.audio_int16_bytes, dtype = np.int16)

		sd.play(audio_data, samplerate =22050)
		sd.wait()

def test_route():
	response = requests.get(url + "/")
	print(response.json())

def send_image():
	with open(file_path, 'rb') as f:
		files = {'file': (file_path, f, 'image/jpeg')}
		response = requests.post(url + "/photo", files = files)
	
	print(response.status_code)
	print(response.json())

def initialize_board():
	with open(file_path, 'rb') as f:
		files = {'file': (file_path, f, 'image/jpeg')}
		response = requests.post(url + "/initialize", files = files)

	json = response.json()
	message = json.get("message", "An error occured, please try again")
	speak(message)




def update_position():
	with open(file_path, 'rb') as f:
		files = {'file': (file_path, f, 'image/jpeg')}
		response = requests.post(url + "/update_position", files = files)

	json = response.json()
	message = json.get("message", "An error occured, please try again")
	
	if (message == "Success"):
		playsound("audio-output/success.mp3")
	else:
		speak(message)

def get_best_move():
	response = requests.get(url + "/best_move")

	json = response.json()

	message = json.get("message", "An error occured, please try again")
	speak(message)	

def analyze_board():
	response = requests.get(url + "/analyze_position")

	json = response.json()

	message = json.get("message", "An error occured, please try again")
	speak(message)	


