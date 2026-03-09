import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"

def get_ml_teaching_segments(segments,keywords):
    """
    segments: list of dicts {"start", "end", "text"}
    returns: list of dicts [{"start": float, "end": float}]
    """
    prompt = f"""
You are analyzing a lecture transcript.

GOAL:
Select transcript segments that contain ACTUAL TEACHING related to the given topics.

TOPICS (context only, not strict keywords):
{keywords}

IMPORTANT:
A segment can still be relevant EVEN IF the keywords are not directly mentioned,
as long as the explanation clearly belongs to the topics above.

INCLUDE segments where the teacher is:
- Explaining a concept
- Giving definitions
- Describing how something works
- Walking through examples
- Explaining algorithms, models, graphs, or methods
- Continuing an explanation from a previous segment

EXCLUDE segments that contain:
- Greetings
- Class introductions
- Attendance checking
- Personal stories
- Career advice
- Jokes or casual conversation
- Classroom management (telling students to be quiet, settle down, etc.)
- Random off-topic discussions
- Conclusions without teaching

SEGMENT RULES:
- Prefer continuous teaching blocks
- Merge adjacent relevant segments
- Do NOT split explanations into tiny pieces

OUTPUT RULES:
- Output ONLY valid JSON
- No explanations
- No markdown
- No extra text

OUTPUT FORMAT:
[
  {{ "start": <float>, "end": <float>, "text": "<string>" }}
]

TRANSCRIPT:
{json.dumps(segments, ensure_ascii=False)}

RETURN JSON ONLY:
"""

    payload = {
    "model": "llama3.2",
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.1
    }
}

#rest api for calling ollama 
    response = requests.post(OLLAMA_URL, json=payload, timeout=600)  # 5 min instead of 2
    #checks for runtime error  - model takes too much time to analyze
    print("RAW OLLAMA RESPONSE:")
    print(response.text)
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
























"""GOAL:
Extract ALL technically substantive teaching content related to AI / ML.
Do NOT compress away algorithm names, mathematical expressions, model names,
optimization techniques, or implementation details.

DEPTH REQUIREMENT (MANDATORY):
A segment MUST be included if it contains:
- Any algorithm name (e.g., SVM, K-Means, HMM, Logistic Regression)
- Any optimization method (Gradient Descent variants, Backpropagation)
- Any mathematical concept (equations, hypothesis function, loss function)
- Any model architecture reference
- Any training/evaluation metric
- Any theoretical construct (concept learning, hypothesis space, etc.)

DO NOT:
- Replace specific algorithm names with generic phrases like "a model"
- Replace technical terms with abstractions
- Omit mathematical reasoning for brevity
- Remove step-by-step derivations

STRICT PRIORITY:
Technical depth > Brevity.

If an explanation contains:
- Algorithm mechanics
- Mathematical formulation
- Parameter update rules
- Model comparison
- Theoretical justification

It MUST be included fully.

SEGMENT LENGTH RULE:
If a technical explanation spans multiple segments,
merge them into one continuous block.
Never cut a derivation midway.





keyiowrds: Machine Learning, Artificial Intelligence, Deep Learning,
Neural Networks, Supervised / Unsupervised Learning,
Regression, Classification,
Loss functions, Optimizers, Gradient Descent, Backpropagation,
CNN, RNN, LSTM, Transformers,
Training, Validation, Accuracy, RMSE,
Overfitting, Regularization, Hyperparameters,
Datasets, Features, Labels,
NumPy, Pandas, PyTorch, TensorFlow, Scikit-learn"""
