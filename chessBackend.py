from fastapi import FastAPI, File, UploadFile, HTTPException
import shutil
import uvicorn
import boardAnalyzer



app = FastAPI()

@app.get("/")
async def root():
	return {"mesage" : "Hello World!"}

@app.post("/photo")
async def recieve_photo(file: UploadFile = File(...)):
	if file.content_type not in ["image/jpeg", "image/jpg"]:
		raise HTTPException(status_code=400, detail="File must be a JPEG image")
	
	file_location = f"uploaded_{file.filename}"

	with open(file_location, "wb+") as file_object:
		shutil.copyfileobj(file.file, file_object)

	boardAnalyzer.analyze_photo()
	return {"info": f"File '{file.filename}' saved at '{file_location}'"}


if __name__ == "__main__":
    uvicorn.run("chessBackend:app", host="0.0.0.0", port=8000, reload=True)