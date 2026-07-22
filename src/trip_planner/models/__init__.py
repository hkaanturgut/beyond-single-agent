"""Final output model."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FinalTripBrief(BaseModel):
    """Final end-user artifact — markdown content + file metadata."""

    markdown: str
    output_path: str
    generated_at: datetime = datetime.utcnow()
