"""CLI entry point: extract financial accounts from a PDF statement."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from extractor import extract_from_pdf
from schema import ExtractionResult

CSV_HEADERS = ["ASSET CLASS", "BROKER", "ACCOUNT HOLDER", "AMOUNT", "Notes"]


def _warn_low_confidence(result: ExtractionResult) -> None:
    for acct in result.accounts:
        if acct.notes and ("unmatched asset_class" in acct.notes or "normalized from" in acct.notes):
            print(
                f"warn: low-confidence asset_class for {acct.broker} / "
                f"{acct.account_holder}: {acct.notes}",
                file=sys.stderr,
            )


def _emit_csv(result: ExtractionResult) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(CSV_HEADERS)
    for acct in result.accounts:
        writer.writerow(
            [
                acct.asset_class,
                acct.broker,
                acct.account_holder,
                f"{acct.amount:.2f}",
                acct.notes or "",
            ]
        )


def _emit_json(result: ExtractionResult) -> None:
    print(json.dumps(result.model_dump(), indent=2))


def _emit_pretty(result: ExtractionResult) -> None:
    print(f"Document type: {result.document_type}")
    if result.unmatched:
        print(f"Unmatched: {result.unmatched_summary or '(no summary)'}")
        return
    if not result.accounts:
        print("No accounts extracted.")
        return
    for i, acct in enumerate(result.accounts, 1):
        print(
            f"  {i}. {acct.asset_class}  |  {acct.broker}  |  {acct.account_holder}  "
            f"|  ${acct.amount:,.2f}"
        )
        if acct.notes:
            print(f"     notes: {acct.notes}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract financial account data from a PDF statement."
    )
    parser.add_argument("pdf_path", type=Path, help="Path to the PDF statement.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--csv", action="store_true", help="Emit CSV.")
    group.add_argument("--json", action="store_true", help="Emit raw JSON.")
    args = parser.parse_args()

    try:
        result = extract_from_pdf(args.pdf_path)
    except FileNotFoundError as e:
        print(f"error: file not found: {e}", file=sys.stderr)
        return 2
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    _warn_low_confidence(result)

    if args.csv:
        _emit_csv(result)
    elif args.json:
        _emit_json(result)
    else:
        _emit_pretty(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
