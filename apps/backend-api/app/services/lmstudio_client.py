from openai import OpenAI

from app.core.config import settings

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=settings.lmstudio_base_url, api_key="lm-studio")
    return _client


def embed_text(texts: list[str]) -> list[list[float]]:
    client = _get_client()
    model = settings.lmstudio_embed_model
    if not model:
        raise RuntimeError("LMSTUDIO_EMBED_MODEL not set")

    resp = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in resp.data]


def chat(messages: list[dict], temperature: float = 0.2) -> str:
    client = _get_client()
    model = settings.lmstudio_chat_model
    if not model:
        raise RuntimeError("LMSTUDIO_CHAT_MODEL not set")

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content