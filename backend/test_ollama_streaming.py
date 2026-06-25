import requests
import json

# Test Ollama API with streaming
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

print("Testing Ollama API with STREAMING...")
print(f"URL: {OLLAMA_API}")
print(f"Model: {OLLAMA_MODEL}")

payload = {
    "model": OLLAMA_MODEL,
    "prompt": "What is a contract? Answer in one sentence.",
    "options": {
        "num_predict": 100,
        "temperature": 0.2
    },
    "stream": True  # Enable streaming
}

print(f"\nSending request...")

try:
    response = requests.post(OLLAMA_API, json=payload, timeout=30, stream=True)
    print(f"Status Code: {response.status_code}")

    print("\nReceiving streaming response:")
    full_response = ""

    for line in response.iter_lines():
        if line:
            chunk = json.loads(line)
            if "response" in chunk:
                full_response += chunk["response"]
                print(chunk["response"], end="", flush=True)

            if chunk.get("done", False):
                print("\n\n✓ Done!")
                print(f"\nFull response: {full_response}")
                break

    print(f"\n✅ SUCCESS! Generated {len(full_response)} characters")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
