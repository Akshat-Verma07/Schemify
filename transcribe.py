import whisper
import json

def transcribe(video_path):
    model = whisper.load_model("base")
    result = model.transcribe(video_path)

    segments = []
    for seg in result["segments"]:
        segments.append({
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip()
        })

    with open("transcript.json", "w") as f:
        json.dump(segments, f, indent=2)

    return segments

