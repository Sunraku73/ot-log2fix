"""Validazione della risposta e delle evidenze rispetto al log analizzato."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

SENTINEL = "NON HO ABBASTANZA CONTESTO"


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status: Literal["ok", "insufficient_context"]
    root_cause: str = Field(min_length=1)
    confidence: Literal["high", "medium", "low"]
    evidence: list[str] = Field(min_length=1, max_length=5)
    fix_steps: list[str] = Field(min_length=3, max_length=3)
    missing_context: list[str]
    injection_detected: bool
    notes: str

    @field_validator("evidence")
    @classmethod
    def check_evidence(cls, evidence: list[str], info: ValidationInfo) -> list[str]:
        if not isinstance(info.context, dict) or "log" not in info.context:
            raise ValueError("Log necessario per verificare le evidenze")
        log_lines = [line.strip() for line in info.context["log"].splitlines()]
        for item in evidence:
            value = item.strip()
            if not value or len(item) > 200 or len(value.splitlines()) != 1:
                raise ValueError("Evidenza vuota, multilinea o oltre 200 caratteri")
            if not any(line.startswith(value) for line in log_lines):
                raise ValueError("Evidenza non presente nel log redatto")
        return evidence

    @model_validator(mode="after")
    def check_status(self) -> "AnalysisResult":
        insufficient = self.status == "insufficient_context"
        if insufficient != (self.root_cause == SENTINEL):
            raise ValueError("Sentinella e status non coerenti")
        if insufficient and self.confidence != "low":
            raise ValueError("La confidence deve essere low per insufficient_context")
        return self
