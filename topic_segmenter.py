import os
import re
import shutil
import subprocess

from clip_video import clip_videos


def safe_topic_name(topic_name, fallback="topic"):
    
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", str(topic_name)).strip("_")
    return cleaned[:100] or fallback


def canonical_topic_id(topic_id):
    
    return re.sub(r"[^a-z0-9]+", "_", str(topic_id).lower()).strip("_")


def group_topic_segments(records, gap=0.3):
    
    grouped = {}
    for record in records:
        segment = record.get("segment", {})
        raw_id = segment.get("topic_id")
        if not raw_id or "start" not in segment or "end" not in segment:
            continue
        topic_id = canonical_topic_id(raw_id)
        if not topic_id:
            continue
        start, end = float(segment["start"]), float(segment["end"])
        if end <= start:
            continue
        item = dict(record)
        item["segment"] = dict(segment, start=start, end=end)
        grouped.setdefault(topic_id, []).append(item)

    result = {}
    for topic_id, items in grouped.items():
        items.sort(key=lambda item: (item["segment"]["start"], item["segment"]["end"]))
        merged = []
        for item in items:
            if (merged and item["source_video"] == merged[-1]["source_video"]
                    and item["segment"]["start"] <= merged[-1]["segment"]["end"] + gap):
                merged[-1]["segment"]["end"] = max(
                    merged[-1]["segment"]["end"], item["segment"]["end"]
                )
            else:
                merged.append(item)
        topic_name = next(
            (item["segment"].get("topic_name") for item in merged
             if item["segment"].get("topic_name")),
            topic_id.replace("_", " ").title(),
        )
        result[topic_id] = {"topic_name": topic_name, "segments": merged}
    return result


def _concat_clips(clip_paths, output_path):
    list_path = os.path.join(os.path.dirname(output_path), "concat.txt")
    with open(list_path, "w", encoding="utf-8") as handle:
        for path in clip_paths:
            handle.write("file '{}'\n".format(os.path.abspath(path).replace("'", "'\\\\''")))
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
            "-map", "0:v:0?", "-map", "0:a:0?", "-c:v", "libx264",
            "-preset", "fast", "-crf", "23", "-c:a", "aac", "-movflags",
            "+faststart", output_path,
        ], check=True)
    finally:
        if os.path.exists(list_path):
            os.remove(list_path)


def create_topic_videos(records, output_root="output/topics"):
    """Create one chronologically stitched MP4 per topic and return its paths."""
    created = []
    used_stems = set()
    for topic_id, topic in group_topic_segments(records).items():
        stem = safe_topic_name(topic["topic_name"], fallback=topic_id)
        # A model should reuse topic_id for equivalent labels.  If it does emit
        # two genuinely distinct IDs that sanitize to the same path, keep both
        # outputs rather than overwriting one of them.
        if stem.lower() in used_stems:
            stem = f"{stem}_{safe_topic_name(topic_id, fallback='topic')}"
        used_stems.add(stem.lower())
        topic_dir = os.path.join(output_root, stem)
        clip_dir = os.path.join(topic_dir, "_clips")
        # Start clean so a rerun cannot accidentally concatenate stale clips.
        shutil.rmtree(clip_dir, ignore_errors=True)
        os.makedirs(clip_dir, exist_ok=True)

        for index, record in enumerate(topic["segments"]):
            segment = record["segment"]
            local_segment = {
                "start": segment["start"] - float(record["chunk_start"]),
                "end": segment["end"] - float(record["chunk_start"]),
            }
            clip_videos(record["source_video"], [local_segment],
                        clip_dir=os.path.join(clip_dir, f"{index:03d}"))

        clip_paths = []
        for root, _, files in os.walk(clip_dir):
            clip_paths.extend(os.path.join(root, name) for name in files if name.endswith(".mp4"))
        clip_paths.sort()
        if not clip_paths:
            continue
        output_path = os.path.join(topic_dir, f"{stem}.mp4")
        _concat_clips(clip_paths, output_path)
        created.append(output_path)
        shutil.rmtree(clip_dir, ignore_errors=True)
    return created
