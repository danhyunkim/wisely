"""Pydantic models for the extraction result."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedAccount(BaseModel):
    asset_class: str = Field(..., description="Canonical asset class from the whitelist.")
    broker: str = Field(..., description="Brokerage / custodian / institution name.")
    account_holder: str = Field(..., description="Name of the account holder.")
    amount: float = Field(..., description="Account balance in USD.")
    notes: str | None = Field(
        default=None,
        description="Optional context: issue year/term, raw asset class if normalization "
        "was low-confidence, money-type split details, etc.",
    )


class ExtractionResult(BaseModel):
    accounts: list[ExtractedAccount] = Field(default_factory=list)
    document_type: str = Field(..., description="Detected document type, e.g. 'Fidelity 401(k)'.")
    unmatched: bool = Field(
        default=False,
        description="True when the document is not a financial account statement.",
    )
    unmatched_summary: str | None = Field(
        default=None,
        description="When unmatched=True, a short description of what the document is.",
    )
