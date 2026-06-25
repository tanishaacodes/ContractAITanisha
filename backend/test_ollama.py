import requests
import json

# Test Ollama API directly
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

print("Testing Ollama API...")
print(f"URL: {OLLAMA_API}")
print(f"Model: {OLLAMA_MODEL}")

payload = {
    "model": OLLAMA_MODEL,
    "prompt": "What is a contract? Answer in one sentence.",
    "options": {
        "num_predict": 100,
        "temperature": 0.2
    },
    "stream": False
}

print(f"\nSending request...")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(OLLAMA_API, json=payload, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
