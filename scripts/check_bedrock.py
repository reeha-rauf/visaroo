"""Smoke-test the Bedrock provider end to end. Run: python scripts/check_bedrock.py"""
import os
import sys
from pathlib import Path

os.environ["AI_PROVIDER"] = "bedrock"
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.ai.bedrock import BedrockProvider  # noqa: E402

p = BedrockProvider()

try:
    vec = p._client.invoke_model  # noqa: F841  (ensure client built)
    emb = p.embed_text("hello world")
    print(f"TITAN embeddings: OK (dim={len(emb)})")
except Exception as e:  # noqa: BLE001
    print(f"TITAN embeddings: FAILED -> {type(e).__name__}: {e}")

try:
    out = p._invoke_claude("You are helpful.", "Say the single word: ok", 20)
    print(f"CLAUDE: OK -> {out.strip()[:60]}")
except Exception as e:  # noqa: BLE001
    print(f"CLAUDE: FAILED -> {type(e).__name__}: {e}")
