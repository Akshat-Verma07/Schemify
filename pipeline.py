import subprocess
import sys
import json
from chunker import split_video
from transcribe import transcribe
from ollama_analyze import get_ml_teaching_segments
from clip_video import clip_videos


def merge_overlapping_segments(segments, gap=3.0):
    """Merge overlapping segments:
      {10-19, 20-34} -> {10-34}"""
    if not segments:
        return []

    segments = sorted(segments, key=lambda x: x["start"])
    merged = [segments[0]]

    for seg in segments[1:]:
        last = merged[-1]
        if seg["start"] <= last["end"] + gap:
            last["end"] = max(last["end"], seg["end"])
        else:
            merged.append(seg)

    return merged


def merge_clips():
    os.makedirs("output", exist_ok=True)

    clip_paths = []

    for root, _, files in os.walk("clips"):
        for f in files:
            if f.endswith(".mp4"):
                clip_paths.append(os.path.join(root, f))

    if not clip_paths:
        print("No clips found!")
        return

    list_path = "clips/list.txt"

    with open(list_path, "w") as f:
        for clip in sorted(clip_paths):
            f.write(f"file '{os.path.abspath(clip)}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-map", "0:v:0?",       #video
        "-map", "0:a:0?",       #audio
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        "output/final.mp4"
    ], check=True)



def main():
    if len(sys.argv) < 3:
        print('Usage: python pipeline.py <video_path> "[AI, ML, NeuralNetworks]"')
        return

    video_path = sys.argv[1]
    keywords = sys.argv[2]   # Just a formatted string

    print("Video Path:", video_path)
    print("Keywords:", keywords)

    print("Splitting long video...")
    chunks = split_video(video_path, chunk_minutes=8)

    chunk_seconds = 8 * 60  # 8 minutes per chunk

    for idx, chunk in enumerate(chunks):
        print(f"\nProcessing chunk {idx+1}/{len(chunks)}")

        chunk_name = os.path.splitext(os.path.basename(chunk))[0]
        chunk_start = idx * chunk_seconds  # absolute start for this chunk

        # Transcribe with absolute timestamps
        print("transcribing...")
        segments = transcribe(chunk, chunk_name, chunk_start)
        print("Transcripting  --> DONE")

        # Ollama analysis
        print("getting ml segments")
        important = get_ml_teaching_segments(segments,keywords)
        print("getting ml segments --> DONE")
        

        # FIX 1: enforce minimum segment length
        MIN_SEGMENT_LEN = 8.0  # seconds
        fixed = []
        for seg in important:
            length = seg["end"] - seg["start"]
            if length < MIN_SEGMENT_LEN:
                fixed.append({
                    "start": seg["start"],
                    "end": seg["start"] + MIN_SEGMENT_LEN,
                    "text": seg.get("text", "")
                })
            else:
                fixed.append(seg)

        important = fixed

        important = merge_overlapping_segments(important, gap=0.3)


        total = sum(seg["end"] - seg["start"] for seg in important)
        if total < 30:
            print(f"⚠️ Ollama weak on {chunk_name}, applying fallback")

            important = []
            for seg in segments:  # Whisper segments
                if seg["end"] - seg["start"] >= 6:      #segment based decision
                    important.append({
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"]
                    }) 



        # Save per-chunk Ollama-selected segments
        os.makedirs("selections", exist_ok=True)
        with open(f"selections/{chunk_name}_segments.json", "w") as f:
            json.dump(important, f, indent=2)


        # Convert absolute → chunk-local timestamps--  ensures each chunk start time is its
        # respective timeline zero. This is crucial for accurate clipping
        local_segments = []
        for seg in important:
            local_segments.append({
                "start": max(0.0, seg["start"] - chunk_start),
                "end": max(0.0, seg["end"] - chunk_start)
            })

        clip_videos(chunk, local_segments, clip_dir=f"clips/{chunk_name}")



    print("Merging all clips...")
    merge_clips()
    print("DONE")


if __name__ == "__main__":
    main()






# analysis/ scoring metrics/ use FPS/FVD models 
