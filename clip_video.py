import os
import subprocess

def has_video_stream(path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v",
            "-show_entries", "stream=index",
            "-of", "csv=p=0",
            path
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return bool(result.stdout.strip())


def has_audio_stream(path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=index",
            "-of", "csv=p=0",
            path
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return bool(result.stdout.strip())


def clip_videos(video_path, segments, clip_dir="clips"):
    os.makedirs(clip_dir, exist_ok=True)

    for i, seg in enumerate(segments):
        if "start" not in seg or "end" not in seg:
            continue

        start = max(0.0, seg["start"] - 1.0)
        end = seg["end"] + 1.0
        duration = end - start

        if duration < 4.0:
            continue

        output = os.path.join(clip_dir, f"clip_{i:03d}.mp4")

        cmd = [
            "ffmpeg", "-y",

            "-i", video_path,

            "-ss", str(start),
            "-t", str(duration),

            "-map", "0:v:0",        #checks video 
            "-map", "0:a:0?",       # checks audio

            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",

            "-c:a", "aac",
            "-b:a", "192k",

            "-movflags", "+faststart",
            output
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            if os.path.exists(output):
                os.remove(output)
            continue

        if not has_video_stream(output) or not has_audio_stream(output):
            os.remove(output)
            print(f"Removed broken clip: {output}")
