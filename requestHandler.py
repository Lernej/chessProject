import requests

url = "http://192.168.1.83:8000"
file_path = "test.jpg"

def test_route():
	response = requests.get(url + "/")
	print(response.json())

def send_image():
	
	with open(file_path, 'rb') as f:
		files = {'file': (file_path, f, 'image/jpeg')}
		response = requests.post(url + "/photo", files = files)
	
	print(response.status_code)
	print(response.json())

