import ollama

MODEL_NAME = "qwen2.5:3b"

response = ollama.chat(
    model=MODEL_NAME,
    messages=[
        {
            "role": "user",
            "content": "Where is my order?"
        }
    ]
)

print(response["message"]["content"])