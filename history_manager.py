import os
import json
import uuid
from datetime import datetime

HISTORY_FILE = "brochure_history.json"

def load_history():
    """Reads brochure history from brochure_history.json."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        print(f"Error loading history: {e}")
        return []

def save_history(history):
    """Saves brochure history list to brochure_history.json."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")

def add_history_entry(urls, markdown_content, model_used="qwen-2.5-32b"):
    """
    Creates and appends a new history entry with timestamp, URLs, and markdown content.
    Returns the newly created entry.
    """
    history = load_history()
    
    # Formulate a readable title from the first URL or markdown heading
    title = "Brochure"
    if urls:
        first_url = urls[0].replace("https://", "").replace("http://", "").strip("/")
        title = first_url.split("/")[0]
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": now_str,
        "title": title,
        "urls": urls,
        "model": model_used,
        "markdown_content": markdown_content
    }
    
    history.insert(0, entry)  # Newest first
    save_history(history)
    return entry

def clear_history():
    """Clears all history records."""
    save_history([])
