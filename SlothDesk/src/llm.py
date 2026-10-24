import requests
from src.settings import OLLAMA_BASE_URL, DEFAULT_MODEL

TIMEOUT_SECONDS = 120

def check_ollama(model=DEFAULT_MODEL):
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        response.raise_for_status()
        names = [x.get("name", "") for x in response.json().get("models", [])]
        found = any(n == model or n.startswith(model + ":") for n in names)
        if found:
            return {"ok": True, "message": "Model available."}
        return {"ok": False, "message": f"Ollama is running, but '{model}' is not installed. Run: ollama pull {model}"}
    except requests.RequestException:
        return {"ok": False, "message": "Cannot reach Ollama at localhost:11434. Install/start Ollama, then pull a model."}

def generate(prompt, model=DEFAULT_MODEL, system=None, temperature=0.2):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature}
    }
    if system:
        payload["system"] = system
    try:
        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.RequestException as exc:
        raise RuntimeError(f"Local Ollama request failed. Check that Ollama is running and model '{model}' is installed. Details: {exc}") from exc

def summarize_text(text, model=DEFAULT_MODEL, system=None):
    prompt = (
        "Help with the following user-provided text or task. Be concise, useful, and honest. "
        "If it is notes, summarize key points and suggested next actions. Do not claim to have changed files.\n\n"
        f"USER INPUT:\n{text[:18000]}"
    )
    return generate(prompt, model=model, system=system)

def classify_file(filename, model=DEFAULT_MODEL):
    prompt = (
        "Classify this filename into exactly one folder category from: Documents, Images, Videos, "
        "Audio, Archives, Code, Spreadsheets, Presentations, Other. "
        "Return only the category word. Filename: " + filename
    )
    answer = generate(prompt, model=model, system="Return one category only.", temperature=0)
    allowed = {"Documents", "Images", "Videos", "Audio", "Archives", "Code", "Spreadsheets", "Presentations", "Other"}
    for category in allowed:
        if answer.strip().lower() == category.lower():
            return category
    return "Other"
