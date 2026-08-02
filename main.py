from fastapi import FastAPI, File, UploadFile, HTTPException
import shutil
import uvicorn
import boardAnalyzer
import chess
import chess.engine

app = FastAPI()

GAME_STATE = {
	"board": None,
	"last_piece_map": None
}

stockfish_exe = "stockfish/stockfish.exe"

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

	success = False

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
	
	# Regular move
	if len(oldSquares) == 1 and len(newSquares) == 1:
		square1 = oldSquares[0]
		square2 = newSquares[0]
		moveStr = square1 + square2
		
		# Here, we check if we are promoting
		squareIdx = chess.parse_square(square1)
		if board.piece_at(squareIdx).piece_type == chess.PAWN:
			if board.turn == chess.WHITE:
				if '7' in square1 and '8' in square2:
					moveStr = moveStr + "q"
			elif board.turn == chess.BLACK:
				if '2' in square1 and '1' in square2:
					moveStr = moveStr + "q"

		move = chess.Move.from_uci(moveStr)
		if move in board.legal_moves:
			success = True
			board.push(move)
			print(board)
		else:
			return {"message" : "Illegal move, please try again!"}
	
	# Castling logic
	elif len(oldSquares) == 2 and len(newSquares) == 2:
		print("Are we castling?")
		
		piecesMoved = []
		for square in oldSquares:
			squareIdx = chess.parse_square(square)
			piece = board.piece_at(squareIdx)
			piecesMoved.append(piece.piece_type)

		if chess.KING in piecesMoved and chess.ROOK in piecesMoved:
			# We castled
			moveStr = ""
			if board.turn == chess.WHITE:
				if "g1" in newSquares:
					moveStr = "e1g1"
				elif "c1" in newSquares:
					moveStr = "e1c1"
			elif board.turn == chess.BLACK:
				if "g8" in newSquares:
					moveStr = "e8g8"
				elif "c8" in newSquares:
					moveStr = "e8c8"
			if moveStr != "":
				move = chess.Move.from_uci(moveStr)
				# Castling was successful
				print("Castling!")				
				if move in board.legal_moves:
					success = True
					board.push(move)
					print(board)
				else:
					return {"message" : "Illegal move, please try again!"}

	if success:
		GAME_STATE["last_piece_map"] = map
		return {"message" : "Success"}
	else:
		return {"message": "An error occured, please try again"}


@app.get("/best_move")
async def best_move():
	prev = GAME_STATE["last_piece_map"]
	
	if not prev:
		return {"message": "Please initialize the board first!"}

	
	board = GAME_STATE["board"]
	
	with chess.engine.SimpleEngine.popen_uci(stockfish_exe) as engine:
		result = engine.play(board, chess.engine.Limit(time = 1.0))
		return {"message": f"The best move in this position is {result.move}"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


@app.get("/analyze_position")
async def analyze_position():
	prev = GAME_STATE["last_piece_map"]
	
	if not prev:
		return {"message": "Please initialize the board first!"}

	
	board = GAME_STATE["board"]
	res = ""
	with chess.engine.SimpleEngine.popen_uci(stockfish_exe) as engine:
		info = engine.analyse(board, chess.engine.Limit(time = 1.0))

		score = info["score"].white()

		if score.is_mate():
			mate_moves = score.mate()
			if mate_moves > 0:
				res = f"White is winning! Forced checkmate in {mate_moves} moves."
			else:
				res = f"Black is winning! Forced checkmate in {abs(mate_moves)} moves."
		else:
			# Convert centipawns to standard pawn value
			pawn_advantage = score.score() / 100.0
			
			if pawn_advantage > 0.5:
				res = f"White is winning by {pawn_advantage:.2f} pawns."
			elif pawn_advantage < -0.5:
				res = f"Black is winning by {abs(pawn_advantage):.2f} pawns."
			else:
				res = f"The game is relatively balanced (Score: {pawn_advantage:.2f})."
		
	if res != "":
		return {"message": res}
	else:
		return {"message": "An error occured, please try again!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)