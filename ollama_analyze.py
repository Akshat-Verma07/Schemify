import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"

def get_ml_teaching_segments(segments):
    """
    segments: list of dicts {"start", "end", "text"}
    returns: list of dicts [{"start": float, "end": float}]
    """
    prompt = f"""
You are an AI system extracting TEACHING content related to
Artificial Intelligence, Machine Learning, and Data Science
from a lecture transcript.

GOAL:
Select ALL segments that TEACH, EXPLAIN, or DISCUSS AI / ML concepts.
Do NOT be overly selective.

WHAT TO INCLUDE:
- Definitions or explanations of AI / ML concepts
- Step-by-step reasoning or intuition
- Examples, analogies, or use-cases
- Discussion of models, algorithms, training, evaluation, or errors
- Follow-up explanations that continue an earlier idea
- Segments referring to "this model", "this method", "this approach"
- Verbal walkthroughs of ML pipelines or code logic

CORE TOPICS (examples, not strict keywords):
Machine Learning, Artificial Intelligence, Deep Learning,
Neural Networks, Supervised / Unsupervised Learning,
Regression, Classification,
Loss functions, Optimizers, Gradient Descent, Backpropagation,
CNN, RNN, LSTM, Transformers,
Training, Validation, Accuracy, RMSE,
Overfitting, Regularization, Hyperparameters,
Datasets, Features, Labels,
NumPy, Pandas, PyTorch, TensorFlow, Scikit-learn

EXCLUDE ONLY:
- Greetings, introductions, or conclusions with no teaching
- Career advice, motivation, or personal stories
- Jokes or casual chat
- Silence, noise, hardware issues

IMPORTANT BEHAVIOR:
- If a segment is PROBABLY relevant, INCLUDE it
- Prefer longer continuous teaching sections
- Merge adjacent relevant segments naturally
- Do NOT split explanations into tiny fragments
- Aim for AT LEAST 30 seconds total per chunk if possible

OUTPUT RULES (STRICT):
- Output ONLY valid JSON and should be in ORDER
- No explanations
- No comments
- No markdown
- No extra text

OUTPUT FORMAT (exact):
[
  {{ "start": <float>, "end": <float>, "text":<str>}}
]

TRANSCRIPT:
{json.dumps(segments, ensure_ascii=False)}

RETURN JSON ONLY:
"""

    payload = {
        "model": "llama3.2:1b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

#rest api for calling ollama 
    response = requests.post(OLLAMA_URL, json=payload, timeout=300)  # 5 min instead of 2
    #checks for runtime error  - model takes too much time to analyze

    raw_text = response.json().get("response", "").strip()

    if not raw_text:
        raise RuntimeError("Ollama returned empty response")


    try:
        important_segments = json.loads(raw_text)
    except json.JSONDecodeError:
        print("JSON parsing failed. Raw response:")
        print(raw_text)
        return []

    # Validate segments
    cleaned = []

    for seg in important_segments:
        if (
            isinstance(seg, dict)
            and "start" in seg
            and "end" in seg
        ):
            start = float(seg["start"])
            end = float(seg["end"])
            text = seg.get("text", "")      #to get text in selection

            if end > start:
                cleaned.append({
                    "start": start,
                    "end": end,
                    "text": text.strip()
                })

    return cleaned
