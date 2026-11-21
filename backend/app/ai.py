import json
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.auth import get_current_user
from app.db import get_board, save_board
from app.schemas import AIChatRequest, AIChatResponse, AIStructuredOutput, BoardData

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


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2 and lines[-1].strip().startswith("```"):
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _build_system_prompt(board: BoardData) -> str:
    return (
        "You are an AI assistant embedded in Kanban Studio, a single-board Kanban app.\n"
        "You must respond with valid JSON matching the schema: "
        '{"reply": string, "board_update": BoardData | null}.\n'
        "- Set board_update to null if the user is only asking a question and no board change is needed.\n"
        "- When creating, editing, moving, or deleting cards, or renaming columns, "
        "return the complete updated board in board_update.\n"
        "- Preserve existing column and card IDs unless creating a new card (use unique IDs like 'card-ai-1').\n"
        "- Every card ID in column.cardIds must exist in board_update.cards.\n\n"
        f"Current board JSON:\n{board.model_dump_json()}"
    )


@router.post("/ping")
def ai_ping(_username: str = Depends(get_current_user)) -> dict[str, str]:
    reply, model = call_openrouter(
        [{"role": "user", "content": "What is 2+2? Reply with just the number."}]
    )
    return {"reply": reply.strip(), "model": model}


@router.post("/chat", response_model=AIChatResponse)
def ai_chat(
    payload: AIChatRequest,
    username: str = Depends(get_current_user),
) -> AIChatResponse:
    current_board = get_board(username)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": _build_system_prompt(current_board)},
        *[{"role": msg.role, "content": msg.content} for msg in payload.history],
        {"role": "user", "content": payload.message},
    ]

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "kanban_chat_response",
            "strict": False,
            "schema": AIStructuredOutput.model_json_schema(),
        },
    }

    raw_content, _ = call_openrouter(messages, response_format=response_format)

    try:
        parsed = AIStructuredOutput.model_validate_json(_strip_code_fences(raw_content))
    except (ValidationError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned invalid structured output",
        ) from exc

    if parsed.board_update is not None:
        updated_board = save_board(username, parsed.board_update)
        return AIChatResponse(reply=parsed.reply, updated=True, board=updated_board)

    return AIChatResponse(reply=parsed.reply, updated=False, board=current_board)
