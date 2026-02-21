# transcribe.py
import whisper
import json
import os
import subprocess

def preprocess_for_transcription(input_path):
    os.makedirs("preprocessed", exist_ok=True)

    base = os.path.splitext(os.path.basename(input_path))[0]    
    cleaned_audio = os.path.join("preprocessed", f"{base}_clean.wav")       
    #clean audio for better transcription

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", input_path,
            "-af", "highpass=f=120,lowpass=f=7000,afftdn=nf=-25,loudnorm",
            "-ac", "1",
            "-ar", "16000",
            cleaned_audio
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
        # cleaned audio for each chunk--- FIX
    return cleaned_audio


def transcribe(video_path, chunk_name=None, chunk_start=0.0):           #returns segments  - a fix we needed 
    audio_path = preprocess_for_transcription(video_path)
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)

    segments = []
    for seg in result["segments"]:
        segments.append({
            "start": round(seg["start"] + chunk_start, 2),  # offset added here
            "end": round(seg["end"] + chunk_start, 2),      # offset added here
            "text": seg["text"].strip()
        })

    os.makedirs("transcripts", exist_ok=True)
    out_path = f"transcripts/{chunk_name}.json" if chunk_name else "transcripts/transcript.json"

    with open(out_path, "w") as f:
        json.dump(segments, f, indent=2)

    return segments
