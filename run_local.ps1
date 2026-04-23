Remove-Item Env:OLLAMA_HOST -ErrorAction SilentlyContinue
$env:MODEL_NAME="llama3.2:3b"

uv run oficial.py