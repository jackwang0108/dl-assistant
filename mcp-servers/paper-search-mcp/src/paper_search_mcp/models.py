"""Validated public inputs. Provider records remain independent JSON observations."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Source = Literal["arxiv", "semantic_scholar", "scholar", "openalex"]
CachePolicy = Literal["prefer", "refresh", "only"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Budget(Input):
    max_requests: int = Field(default=8, ge=1, le=100)
    max_items: int = Field(default=40, ge=1, le=1000)
    max_seconds: float = Field(default=45, gt=0, le=300)
    max_download_bytes: int = Field(default=50_000_000, ge=1, le=500_000_000)


class DateRange(Input):
    date_type: Literal["first_submitted", "updated", "published"]
    start: date | None = None
    end: date | None = None

    @model_validator(mode="after")
    def ordered(self):
        if self.start is None and self.end is None:
            raise ValueError("A date bound is required")
        if self.start and self.end and self.start > self.end:
            raise ValueError("Date start must not exceed end")
        return self


class PaperFilters(Input):
    date_range: DateRange | None = None
    venues: list[str] | None = None
    publication_types: list[str] | None = None
    categories: list[str] | None = None
    languages: list[str] | None = None
    open_access: bool | None = None
    unsupported: Literal["error", "report"] = "error"


class PublicationYearRange(Input):
    start: int | None = Field(default=None, strict=True, ge=1000, le=2200)
    end: int | None = Field(default=None, strict=True, ge=1000, le=2200)

    @model_validator(mode="after")
    def ordered(self):
        if self.start is None and self.end is None:
            raise ValueError("A publication year bound is required")
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("Publication year start must not exceed end")
        return self


class PaperQuery(Input):
    text: str = Field(min_length=1, max_length=4000)
    sources: list[Source] | None = Field(default=None, min_length=1)
    syntax: Literal["text", "source_native"] = "text"

    @model_validator(mode="after")
    def native_source(self):
        if self.syntax == "source_native" and (not self.sources or len(self.sources) != 1):
            raise ValueError("source_native requires exactly one source")
        return self


class PaperLookup(Input):
    identifier: str | None = Field(default=None, min_length=1)
    title: str | None = Field(default=None, min_length=1)
    authors: list[str] | None = None
    year: int | None = Field(default=None, ge=1000, le=2200)

    @model_validator(mode="after")
    def one_input(self):
        if bool(self.identifier) == bool(self.title):
            raise ValueError("Provide identifier or title, not both")
        return self
