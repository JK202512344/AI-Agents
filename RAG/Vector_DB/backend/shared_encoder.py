"""
shared_encoder.py

Single source of truth for the Qwen encoder.
Both router.py and guardrails.py import from here so the model
is loaded exactly once — saving 4–10 s of cold-start time.
"""

from semantic_router.encoders import HuggingFaceEncoder

# Module-level singleton: loaded once, reused everywhere
_encoder: HuggingFaceEncoder | None = None


def get_encoder() -> HuggingFaceEncoder:
    global _encoder
    if _encoder is None:
        print("[shared_encoder] Loading Qwen encoder (once)...")
        _encoder = HuggingFaceEncoder(name="Qwen/Qwen3-Embedding-0.6B")
    return _encoder
