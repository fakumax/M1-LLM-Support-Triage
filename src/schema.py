from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["billing", "technical", "account", "other"]


class SupportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    category: Category
    actions: list[str] = Field(min_length=1)
