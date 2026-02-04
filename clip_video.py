import subprocess
import os

def clip_video(video_path, segments):
    os.makedirs("clips", exist_ok=True)

    for i, seg in enumerate(segments):
        output = f"clips/clip_{i}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-ss", str(seg["start"]),
            "-to", str(seg["end"]),
            "-c", "copy",
            output
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
