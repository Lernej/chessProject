import argparse
import json
import queue
import sys
import sounddevice as sd
import cameraHandler
import numpy as np
import requestHandler

from sentence_transformers import SentenceTransformer, util
from vosk import Model, KaldiRecognizer
from sklearn.metrics.pairwise import cosine_similarity


q = queue.Queue()
embeddingModel = SentenceTransformer('all-MiniLM-L6-v2')
pictureTakingPhrases = ["Take a picture", "Capture a photo", "Get a snapshot", "Shoot a photo", "Snap an Image", "Get a snapshot", "Please take a picture", "Please get a photo"]
keyPhrases = ["Initialize Board", "Update Position", "Update", "What is the best move here", "Best Move", "What is the best move", "Who is winning", "Who is winning here", "Who is winning in this position"]
bestMovePhrases = ["What is the best move here", "Best Move", "What is the best move"]
whoWinningPhrases = ["Who is winning", "Who is winning here", "Who is winning in this position"]

phrase_embeddings = embeddingModel.encode(pictureTakingPhrases)
keyPhrase_embeddings = embeddingModel.encode(keyPhrases)

def evaluate(sentence):
    embedding = embeddingModel.encode([sentence])

    similarities = cosine_similarity(embedding, phrase_embeddings)[0]
    return np.max(similarities)

def getClosestPhrase(sentence):
    embedding = embeddingModel.encode([sentence])
    
    similarities = cosine_similarity(embedding, keyPhrase_embeddings)[0]
    max_similarity = np.max(similarities)
    if (max_similarity > .6):
        return keyPhrases[np.argmax(similarities)]
    else:
        return None
    

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "-l", "--list-devices", action="store_true",
    help="show list of audio devices and exit")
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    "-f", "--filename", type=str, metavar="FILENAME",
    help="audio file to store recording to")
parser.add_argument(
    "-d", "--device", type=int_or_str,
    help="input device (numeric ID or substring)")
parser.add_argument(
    "-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument(
    "-m", "--model", type=str, help="language model; e.g. en-us, fr, nl; default is en-us")
args = parser.parse_args(remaining)

try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, "input")
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info["default_samplerate"])
        
    if args.model is None:
        model = Model(lang="en-us")
    else:
        model = Model(lang=args.model)

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 8000, device=args.device,
            dtype="int16", channels=1, callback=callback):
        print("#" * 80)
        print("Press Ctrl+C to stop the recording")
        print("#" * 80)

        rec = KaldiRecognizer(model, args.samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                voiceInput = res["text"]
                print(voiceInput)
                evaluation = evaluate(voiceInput)

                closestPhrase = getClosestPhrase(voiceInput)
                print(closestPhrase)

                if (closestPhrase == "Initialize Board"):
                    cameraHandler.capture_photo()
                    print("Sending!")
                    requestHandler.initialize_board()
                elif (closestPhrase == "Update Position" or closestPhrase == "Update"):
                    cameraHandler.capture_photo()
                    print("Sending!")
                    requestHandler.update_position()
                elif closestPhrase in bestMovePhrases:
                    requestHandler.get_best_move()
                elif closestPhrase in whoWinningPhrases:
                    print("Sending request!")
                    requestHandler.analyze_board()
                

            # else:
            #     print(rec.PartialResult())
                
            if dump_fn is not None:
                dump_fn.write(data)

except KeyboardInterrupt:
    print("\nDone")
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ": " + str(e))