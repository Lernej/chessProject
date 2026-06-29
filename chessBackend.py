from fastapi import FastAPI, File, UploadFile, HTTPException
import shutil
import uvicorn
import boardAnalyzer
import chess


app = FastAPI()

GAME_STATE = {
	"board": None,
	"last_piece_map": None
}



@app.get("/")
async def root():
	return {"message" : "Hello World!"}

@app.post("/photo")
async def recieve_photo(file: UploadFile = File(...)):
	if file.content_type not in ["image/jpeg", "image/jpg"]:
		raise HTTPException(status_code=400, detail="File must be a JPEG image")
	
	file_location = f"uploaded_{file.filename}"

	with open(file_location, "wb+") as file_object:
		shutil.copyfileobj(file.file, file_object)

	boardAnalyzer.get_board_map()
	return {"info": f"File '{file.filename}' saved at '{file_location}'"}

@app.post("/initialize")
async def initialize(file: UploadFile = File(...)):
	if file.content_type not in ["image/jpeg", "image/jpg"]:
		raise HTTPException(status_code=400, detail="File must be a JPEG image")
	
	file_location = f"uploaded_{file.filename}"

	with open(file_location, "wb+") as file_object:
		shutil.copyfileobj(file.file, file_object)

	map = boardAnalyzer.get_board_map()
	
	files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
	ranks = ['1', '2', '7', '8']


	for f in files:
		for r in ranks:
			square = f + r
			if square not in map:
				print("Board failed to be initialized!")
				print(square)
				return {"message": "Failed to initialize board, please try again!"}
				

	GAME_STATE["board"] = chess.Board()
	GAME_STATE["last_piece_map"] = map

	return {"message": "Successfully initialized board!"}

@app.post("/update_position")
async def update_position(file: UploadFile = File(...)):
	if file.content_type not in ["image/jpeg", "image/jpg"]:
		raise HTTPException(status_code=400, detail="File must be a JPEG image")
	
	file_location = f"uploaded_{file.filename}"

	with open(file_location, "wb+") as file_object:
		shutil.copyfileobj(file.file, file_object)

	map = boardAnalyzer.get_board_map()
	prev = GAME_STATE["last_piece_map"]
	board = GAME_STATE["board"]

	if not prev:
		return {"message" : "Error, please initialize the board first!"}
	
	newSquares = []
	for key in map.keys():
		if key not in prev or prev[key] != map[key]:
			newSquares.append(key)
	oldSquares = []
	for key in prev.keys():
		if key not in map:
			oldSquares.append(key)

	if len(map) < len(prev) - 1:
		return {"message": "An error occured, please try again"}
	
	print(oldSquares)
	print(newSquares)
	if len(oldSquares) == 1 and len(newSquares) == 1:
		square1 = oldSquares[0]
		square2 = newSquares[0]
		moveStr = square1 + square2
		
		move = chess.Move.from_uci(moveStr)
		if move in board.legal_moves:
			board.push(move)
			print(board)

	
	GAME_STATE["last_piece_map"] = map

	return {"message" : "Successfully updated position"}


if __name__ == "__main__":
    uvicorn.run("chessBackend:app", host="0.0.0.0", port=8000, reload=True)