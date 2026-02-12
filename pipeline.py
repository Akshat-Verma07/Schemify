import sys
import os
import subprocess

from transcribe import transcribe
from ollama_analyze import get_important_segments
from clip_video import clip_video

def merge_clips():
    os.makedirs("output", exist_ok=True)

    clip_dir = "clips"

    # Get all clip files
    clip_files = sorted([
        os.path.join(clip_dir, f)
        for f in os.listdir(clip_dir)
        if f.endswith(".mp4")
    ])

    if not clip_files:
        print("No clips found!")
        return

    # Create list.txt INSIDE clips folder
    list_path = os.path.join(clip_dir, "list.txt")

    with open(list_path, "w") as f:
        for clip in clip_files:
            clip_name = os.path.basename(clip)   # IMPORTANT
            f.write(f"file '{clip_name}'\n")

    # Run ffmpeg
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        "output/final.mp4"
    ])


def main():
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <video_path>")
        return

    video_path = sys.argv[1]

    if not os.path.exists(video_path):
        print("Video file not found:", video_path)
        return

    print("Transcribing video...")
    segments = transcribe(video_path)

    print("Analyzing important parts with Ollama...")
    important_segments = get_important_segments(segments)

    # Normalize Ollama output
    normalized_segments = []

    for seg in important_segments:
        if isinstance(seg, dict):
            normalized_segments.append(seg)
        elif isinstance(seg, (int, float)):
            normalized_segments.append({
                "start": float(seg),
                "end": float(seg) + 10
            })

    important_segments = normalized_segments

    print("Clipping video...")
    clip_video(video_path, important_segments)

    print("Merging clips...")
    merge_clips()

    print("DONE! Output saved to output/final.mp4")


if __name__ == "__main__":
    main()
