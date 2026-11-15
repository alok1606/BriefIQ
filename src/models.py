from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Meeting(StrictModel):
    target_type: Literal["Company", "Person"]
    name: str = Field(min_length=2, max_length=120)
    when: datetime
    timezone: str
    purpose: str = Field(default="", max_length=400)


class Window(StrictModel):
    start: datetime
    end: datetime
    researched_at: datetime
    notes: list[str] = Field(default_factory=list)


class Source(StrictModel):
    id: str
    title: str
    url: str
    excerpt: str
    published: str | None = None
    date_status: Literal["in_window", "undated", "boundary_uncertain"]


class Evidence(StrictModel):
    sources: list[Source] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    queries: list[str] = Field(default_factory=list)


class Claim(StrictModel):
    text: str = Field(min_length=1, max_length=300)
    citation_ids: list[str] = Field(default_factory=list, max_length=3)
    evidence: Literal["source_backed", "uncertain"] = "uncertain"


class Development(Claim):
    why_it_matters: str = Field(min_length=1, max_length=200)
    discussion_point: str = Field(min_length=1, max_length=180)


class Draft(StrictModel):
    summary: list[Claim] = Field(max_length=3)
    developments: list[Development] = Field(max_length=5)
    questions: list[str] = Field(min_length=3, max_length=5)
    uncertainty: list[str] = Field(default_factory=list, max_length=6)


class Briefing(StrictModel):
    meeting: Meeting
    window: Window
    evidence: Evidence
    draft: Draft
    demo: bool
    metadata: dict = Field(default_factory=dict)
