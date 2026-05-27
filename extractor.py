"""Extract financial account data from a PDF using Claude vision + tool use."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from schema import ExtractedAccount, ExtractionResult
from whitelist import ALL_CLASSES, FUZZY_THRESHOLD, WHITELIST, normalize

MODEL = "claude-sonnet-4-6"
TOOL_NAME = "record_extraction"

SYSTEM_PROMPT = f"""You extract financial account data from PDF statements.

For every account or balance you find, return a row with:
- asset_class: choose from the whitelist below
- broker: institution / custodian (e.g. "Fidelity", "Schwab", "Chase")
- account_holder: name on the account
- amount: ending USD balance as a number (no $, no commas)
- notes: optional context (issue year, raw asset class if you weren't sure, etc.)

Whitelist (asset_class MUST be one of these exact strings):
{json.dumps(WHITELIST, indent=2)}

Provider rules:
- Fidelity 401(k) and similar workplace plans: split into separate rows
  by money type. Pre-tax employee -> "401(k)". Employer match -> "401(k) Match".
  After-tax non-Roth -> "After Tax 401(k)". Roth -> "Roth 401(k)".
- Whole Life policies: include policy issue year and term in notes.
- Brokerage accounts: one row per account. Use "Brokerage" unless the
  account holds individual stocks, in which case use "Stock".
- Crypto exchanges (Coinbase, Kraken, etc.): asset_class "Crypto".
- Bank statements: separate rows for checking vs savings.
- If the document is NOT a financial account statement (exec comp,
  benefits charts, etc.), return accounts=[], unmatched=true, and a
  short unmatched_summary describing what the document is.

Always set document_type (e.g. "Fidelity 401(k)", "Chase Checking",
"Coinbase Crypto", "Whole Life Policy").
"""


def _build_tool() -> dict:
    schema = ExtractionResult.model_json_schema()
    return {
        "name": TOOL_NAME,
        "description": "Record the structured extraction result.",
        "input_schema": schema,
    }


def _encode_pdf(pdf_path: Path) -> str:
    return base64.standard_b64encode(pdf_path.read_bytes()).decode("ascii")


def _snap_account(acct: ExtractedAccount) -> tuple[ExtractedAccount, bool]:
    """Snap asset_class to the whitelist. Returns (account, was_low_confidence)."""
    raw = acct.asset_class
    if raw in ALL_CLASSES:
        return acct, False

    match, score = normalize(raw)
    if match is None or score < FUZZY_THRESHOLD:
        note_bits = [f"unmatched asset_class={raw!r}"]
        if acct.notes:
            note_bits.append(acct.notes)
        snapped = acct.model_copy(
            update={"asset_class": raw, "notes": "; ".join(note_bits)}
        )
        return snapped, True

    note_bits = []
    if score < 100:
        note_bits.append(f"normalized from {raw!r} (conf={score})")
    if acct.notes:
        note_bits.append(acct.notes)
    snapped = acct.model_copy(
        update={
            "asset_class": match,
            "notes": "; ".join(note_bits) if note_bits else None,
        }
    )
    return snapped, score < FUZZY_THRESHOLD


def extract_from_pdf(pdf_path: str | Path) -> ExtractionResult:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to .env and re-run."
        )

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    client = Anthropic(api_key=api_key)
    tool = _build_tool()

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[tool],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": _encode_pdf(pdf_path),
                        },
                    },
                    {
                        "type": "text",
                        "text": "Extract every financial account in this document. "
                        "Follow the provider rules from the system prompt.",
                    },
                ],
            }
        ],
    )

    tool_block = next(
        (b for b in response.content if getattr(b, "type", None) == "tool_use"),
        None,
    )
    if tool_block is None:
        raise RuntimeError(
            f"Model did not return a tool_use block. stop_reason={response.stop_reason}"
        )

    result = ExtractionResult.model_validate(tool_block.input)

    snapped: list[ExtractedAccount] = []
    for acct in result.accounts:
        snapped_acct, _ = _snap_account(acct)
        snapped.append(snapped_acct)
    result.accounts = snapped

    return result
