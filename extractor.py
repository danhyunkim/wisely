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

SYSTEM_PROMPT = """You are a financial statement data extractor for a financial advisor. Your job is to extract structured account data from PDF statements and return it in a strict schema.

## Output schema
For each financial account found in the document, produce one row with:
- asset_class: must be EXACTLY one of the canonical values listed below
- broker: the institution name (e.g. "Fidelity", "Schwab", "Chase", "MainStay", "Coinbase")
- account_holder: the person's first name only, or "Joint" for jointly-held accounts
- amount: current balance or market value as a number (no currency symbols, no commas)
- notes: optional contextual info (interest rate, vesting, FMV, policy issue year, etc.) — leave null if nothing notable

## Canonical asset_class values (use EXACTLY these strings)

PRE-TAX:        401(k) | 401(k) Match | IRA | Rollover IRA | Inherited IRA | Simple IRA | Pension | 403(b) | 457 | 401(a) | Profit Sharing
BROKERAGE:      Stock | Stocks | Brokerage | Stock Grant | Mutual Funds | Options | ESPP | Crypto | Hedge Funds | REIT
TAX DEFERRED:   Variable Annuity | Fixed Annuity | After Tax 401(k) | LTC/Life Hybrid
TAX FREE:       Roth IRA | Roth 401(k) | Roth 403(b) | 529 | Whole Life | Whole Life B | Variable Life | Universal Life
CASH:           Checking | Savings | MMAs | Cash | CDs | Income
PROPERTY:       Home Equity | Investment Property Equity
BUSINESS:       Business Equity
PROTECTION:     Term Insurance

## Critical extraction rules

### Rule 1: Split 401(k) statements by money type
Fidelity, Empower, Vanguard, and similar 401(k) statements break down balances by money source. Each source becomes its OWN row:
- Employee Pre-Tax / Pre-Tax Deferral → asset_class: "401(k)"
- Employer Match / Company Match / Employer Contributions → asset_class: "401(k) Match"
- After-Tax (Non-Roth) → asset_class: "After Tax 401(k)"
- Roth Deferral / Roth 401(k) / Designated Roth → asset_class: "Roth 401(k)"
A single 401(k) statement commonly produces 2-4 rows. Do NOT collapse them into one total.

### Rule 2: Bank statements with multiple account types → multiple rows
A Chase or Wells Fargo statement showing both a checking and a savings account becomes 2 rows: one with asset_class "Checking", one with "Savings". Same for any combo of CDs, MMAs, etc.

### Rule 3: Brokerage vs. Stock
- If the statement shows a managed/diversified brokerage account with multiple holdings → "Brokerage"
- If it's specifically a single stock position or RSU/stock grant → "Stock" or "Stock Grant"
- If it's an employee stock purchase plan → "ESPP"
- Crypto exchanges (Coinbase, Kraken, Gemini) → "Crypto"

### Rule 4: Life insurance specifics
- Whole life policies: asset_class "Whole Life", and in notes capture the issue year and term length if visible (e.g. "Issued 2014, 35-year term")
- The amount is the cash value (not the death benefit). If you see both a "Cash Value" and a "Death Benefit", the amount MUST be the cash value.
- Term life: asset_class "Term Insurance", amount is typically 0 or the cash value if any

### Rule 5: IRA variants
Be precise — these are distinct asset classes with different tax treatment:
- Traditional IRA, Rollover IRA, Inherited IRA, Simple IRA — each maps to its specific name above
- Roth IRA → "Roth IRA" (this is in TAX FREE category, not PRE-TAX)

### Rule 6: Account holder
- If the statement is in one person's name → use that first name only (e.g. "Manu Sharma" → "Manu", "Mr. Manu Sharma" → "Manu")
- If two account holders are listed and neither is a minor → default to "Joint" unless the document explicitly states otherwise
- For UGMA/UTMA/529 in a child's name → use the child's first name
- Strip trailing/leading whitespace

### Rule 7: Amount
- Use the most recent / current balance shown on the statement
- For 401(k) accounts split by money type, use the balance for THAT money type, not the total
- Numeric only — no "$", no commas, no parentheses for negatives
- Example: "$471,000.00" → 471000.00
- Round to 2 decimal places if cents are shown, otherwise integer

### Rule 8: Non-account documents
If the document is NOT a financial account statement — e.g. an executive compensation explainer, a benefits enrollment guide, a tax form, or a marketing brochure — return an empty accounts list and set:
- unmatched: true
- unmatched_summary: one sentence describing what the document is (e.g. "Executive deferred compensation plan explanation — no account balances present")
If you find yourself inferring or estimating numbers, return unmatched: true instead of fabricating accounts.

### Rule 9: When uncertain about asset_class
If you can't confidently map an account to one of the canonical values, use your best guess AND put the raw label from the statement in the notes field so the human can verify. Better to extract with a guess than to skip the row.

## What NOT to do
- Do NOT invent accounts that aren't clearly shown in the document
- Do NOT compute derived fields like tax sequence, risk sequence, category, or KEY — those are calculated downstream
- Do NOT include the bucket (Aggressive/Conservative) — that's a human decision
- Do NOT include account numbers or any PII beyond the holder's first name
- Do NOT output currency symbols, percent signs, or formatting characters in numeric fields

## Document type
Also return a `document_type` string describing what you extracted from, e.g. "Fidelity 401(k) Quarterly Statement", "Schwab Brokerage Account Statement", "NYL Whole Life Policy Statement". This helps with debugging.

Now extract the accounts from the document provided.
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
