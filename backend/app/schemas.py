from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CardData(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    details: str = ""


class ColumnData(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    cardIds: list[str]


class BoardData(BaseModel):
    columns: list[ColumnData]
    cards: dict[str, CardData]


class AIConnectivityResponse(BaseModel):
    model: str
    prompt: str
    response: str


class AIChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1)
    board: BoardData
    history: list[AIChatHistoryMessage] = Field(default_factory=list)


class AIModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assistantMessage: str = Field(min_length=1)
    boardUpdate: BoardData | None = None


class AIChatResponse(BaseModel):
    model: str
    assistantMessage: str
    boardUpdated: bool
    board: BoardData | None = None
