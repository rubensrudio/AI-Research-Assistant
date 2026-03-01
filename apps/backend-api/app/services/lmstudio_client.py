import os
from openai import OpenAI

def get_client() -> OpenAI:
    base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
    api_key = os.getenv("LMSTUDIO_API_KEY", "lm-studio")
    # O SDK pede api_key; LM Studio pode não exigir, mas passar um valor é ok. :contentReference[oaicite:5]{index=5}
    return OpenAI(base_url=base_url, api_key=api_key)

def embed_text(texts: list[str]) -> list[list[float]]:
    client = get_client()
    model = os.getenv("LMSTUDIO_EMBED_MODEL", "")
    if not model:
        raise RuntimeError("LMSTUDIO_EMBED_MODEL not set")

    resp = client.embeddings.create(
        model=model,
        input=texts,
    )
    return [d.embedding for d in resp.data]

def chat(messages: list[dict], temperature: float = 0.2) -> str:
    client = get_client()
    model = os.getenv("LMSTUDIO_CHAT_MODEL", "")
    if not model:
        raise RuntimeError("LMSTUDIO_CHAT_MODEL not set")

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content