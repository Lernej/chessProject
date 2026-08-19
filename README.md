# Chess Vision Assistant

A voice-controlled chess assistant built over one summer. When playing chess,
hold up a Pi 5 with a camera module pointed at the board and send an update to 
an API via voice commands. The Pi will update you with the best move and an analysis
of the position.

```
┌─────────────────────────┐         ┌──────────────────────────────────────┐
│  Raspberry Pi  (pi/)    │         │  API server  (api/)                  │
│                         │         │                                      │
│  Vosk  speech → text    │  JPEG   │  OpenCV   find + flatten the board   │
│  MiniLM text → intent   │ ──────► │  Roboflow detect piece occupancy     │
│  Picamera2  capture     │  HTTP   │  python-chess  track game state      │
│  Piper  text → speech   │ ◄────── │  Stockfish  best move / evaluation   │
└─────────────────────────┘  JSON   └──────────────────────────────────────┘
```

## The core idea

The vision model **only detects occupancy and colour.** It reports
`white_piece` or `black_piece`, never "knight" or "rook". Piece identity is
never seen by the camera at all. Instead it lives in a `python-chess` board that
the API maintains, and moves are inferred by diffing successive photographs:

- One square emptied, one square changed → a normal move (or a capture, since
  the destination changes colour)
- Two emptied, two changed, king and rook among them → castling

Every candidate move is validated against `board.legal_moves` before it is
applied, so a bad frame is rejected rather than silently corrupting the game.
This is what makes a colour-only detector sufficient.

## Layout

```
api/                     FastAPI server (runs on a laptop)
  main.py                Endpoints, game state, Stockfish
  boardAnalyzer.py       Locate the board, correct perspective
  pieceDetection.py      Roboflow inference → {square: colour}
  boardGrid.py           Pixel coordinates → square names
pi/                      Raspberry Pi client
  main.py                Voice loop and intent matching
  cameraHandler.py       Picamera2 capture + MJPEG preview
  requestHandler.py      API calls and speech synthesis
focused_photos/          30 sample rectified boards from testing
```

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Health check |
| `POST` | `/initialize` | Photograph a starting position and begin a game |
| `POST` | `/update_position` | Photograph the board, infer and apply the move |
| `GET` | `/best_move` | Stockfish's best move for the current position |
| `GET` | `/analyze_position` | Who is winning, in pawns or forced mate |

All endpoints return `{"message": "..."}`, including on failure, so the Pi can
speak any response verbatim.

## Voice commands

Speech is transcribed by Vosk, then matched against known phrases by cosine
similarity over MiniLM sentence embeddings (threshold 0.6). This means
wording will not have to be exact for commands to be registered.

| Say | Does |
| --- | --- |
| "Initialize board" | Starts a new game from the current position |
| "Update position" / "Update" | Registers the move you just played |
| "What is the best move" | Speaks Stockfish's recommendation |
| "Who is winning" | Speaks the evaluation |

## Setup

### Prerequisites

Three assets are **not** in this repository and must be downloaded separately.

| Asset | Where it goes | Source |
| --- | --- | --- |
| Stockfish engine | `api/stockfish/stockfish.exe` | [stockfishchess.org](https://stockfishchess.org/download/) |
| Vosk model (small en-us) | `pi/vosk-model-small-en-us-0.15/` | [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models) |
| Piper voice | `pi/voice-models/en_US-arctic-medium.onnx` | [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) |

Unzip the Vosk model so that `am/`, `conf/` and `graph/` are directly inside
`pi/vosk-model-small-en-us-0.15/`,  not nested in a second folder of the same
name.

### API server

```bash
cd api
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
```

Set your Roboflow key, then run **from inside `api/`.** The Stockfish and
output paths are relative to the working directory:

```bash
export ROBOFLOW_API_KEY=your_key_here
python main.py
```

Listens on `0.0.0.0:8000`.

### Raspberry Pi

`picamera2` ships as a system package on Raspberry Pi OS and should not be
installed with pip:

```bash
sudo apt install -y python3-picamera2
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r pi/requirements.txt
```

Point the client at your API machine and run **from inside `pi/`**:

```bash
export CHESS_API_URL=http://192.168.1.83:8000
cd pi && python3 main.py
```

A live MJPEG preview is served on port 5000, which is useful for aligning the
camera.

## Known limitations

This project was made with the intention of learning how to use Roboflow, OpenCV,
and the Raspberry Pi 5. As such, there are some limitations, many of which I intend to fix in the future.

**The Roboflow model is private.** `chess-project-9lzcy/1` lives in my Roboflow
workspace, so cloning this repo and supplying your own API key is *not* enough
to run the vision pipeline. You would need to train an equivalent
occupancy-and-colour detector and change the model ID in
`api/pieceDetection.py`.

**Computer vision is tuned to one setup.**

- Board detection was only ever tested against a single floor surface. It picks
  the first square-ish quadrilateral it finds, so a busy background can defeat it.
- `boardGrid.py` hardcodes pixel bounds (`x_start=30, x_end=610, y_start=30,
  y_end=465`) and a fixed file order. These bounds work for the particular board used
  during testing, but a different board may require different bounds.

**Chess rules are incompletely handled.**

- **En passant is currently not supported.** It produces two emptied squares and one
  changed square, which matches neither the normal-move nor the castling branch,
  so the move is rejected.
- Promotion always assumes a queen.
- `/initialize` checks that ranks 1, 2, 7 and 8 are occupied, but not that the
  colours are on the expected sides. A board set up 180° from what
  `boardGrid.py` expects will initialize successfully and then misread every move. **This is the most critical missing feature
  at the moment.**
- Castling that is detected but whose destination is not a `g` or `c` file falls
  through to a generic error rather than reporting the specific problem.

**State is in-memory.** One game at a time, no persistence; restarting the API
loses the position.

## Possible next steps

- Publish the detection model so the project is reproducible
- Handle en passant by treating "two emptied, one changed" as a capture candidate
- Persist game state so the API can restart mid-game


**Disclaimer:** I used Claude code for polishing the repository/drafting the README.
