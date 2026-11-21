import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"

router = APIRouter(prefix="/api/ai", tags=["ai"])


def get_openrouter_config() -> tuple[str, str]:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENROUTER_API_KEY is not configured",
        )
    model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    return api_key, model


def call_openrouter(
    messages: list[dict[str, str]],
    response_format: dict | None = None,
) -> tuple[str, str]:
    api_key, model = get_openrouter_config()
    payload: dict = {"model": model, "messages": messages}
    if response_format is not None:
        payload["response_format"] = response_format

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        res = httpx.post(OPENROUTER_URL, json=payload, headers=headers, timeout=60.0)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenRouter request failed: {exc}",
        ) from exc

    if res.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenRouter error ({res.status_code}): {res.text}",
        )

    data = res.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected OpenRouter response format",
        ) from exc

    return content, data.get("model", model)


@router.post("/ping")
def ai_ping(_username: str = Depends(get_current_user)) -> dict[str, str]:
    reply, model = call_openrouter(
        [{"role": "user", "content": "What is 2+2? Reply with just the number."}]
    )
    return {"reply": reply.strip(), "model": model}
