import os
import subprocess

def split_video(video_path, chunk_minutes=8):
    os.makedirs("chunks", exist_ok=True)        #chunks file

    chunk_seconds = chunk_minutes * 60
    output_pattern = "chunks/chunk_%03d.mp4"

    # ❌ Remove -reset_timestamps
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-map", "0",
        "-c", "copy",
        "-f", "segment",
        "-segment_time", str(chunk_seconds),
        output_pattern
    ], check=True)

    return sorted(
        os.path.join("chunks", f)
        for f in os.listdir("chunks")
        if f.endswith(".mp4")
    )

