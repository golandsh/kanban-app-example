from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.db import get_board, save_board
from app.schemas import BoardData

router = APIRouter(prefix="/api/board", tags=["board"])


@router.get("", response_model=BoardData)
def read_board(username: str = Depends(get_current_user)) -> BoardData:
    return get_board(username)


@router.put("", response_model=BoardData)
def update_board(
    payload: BoardData,
    username: str = Depends(get_current_user),
) -> BoardData:
    return save_board(username, payload)
