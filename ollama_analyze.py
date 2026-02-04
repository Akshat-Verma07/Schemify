import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"

def get_important_segments(segments):
    """
    segments: list of dicts {"start", "end", "text"}
    returns: list of dicts [{"start": float, "end": float}]
    """
    prompt = f"""
You are an smart AI summarizer.

1.From the transcript below, identify the most important segments related to the topic 
the person is teaching (IDENTIFY WHAT THEY ARE TRYING TO TEACH/TELL).
2.Return only the start and end times in seconds as JSON objects.
3.Do NOT provide any explanation.
4.DO NOT INCLUDE ANY OUT OF CONTEXT /TOPIC THE PEROSN MAY REFER TOO !! 

Transcript:
{json.dumps(segments)}
"""

    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0}
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    raw_text = response.json().get("response", "").strip()

    if not raw_text:
        raise RuntimeError("Ollama returned empty response")


    numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", raw_text)]

    important_segments = []

    # group numbers into start/end pairs
    for i in range(0, len(numbers), 2):
        start = numbers[i]
        end = numbers[i+1] if i+1 < len(numbers) else start + 10  # default 10s
        important_segments.append({"start": start, "end": end})

    return important_segments
