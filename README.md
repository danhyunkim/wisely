# wisely

Python CLI that extracts financial account data from PDF statements using Claude vision + tool use.

## What it does

Point it at a PDF statement (Fidelity 401(k), Schwab brokerage, Chase bank, Coinbase, a life insurance policy, etc.) and it returns one normalized row per account.

Each row has five fields:

| Field            | Description                                                  |
| ---------------- | ------------------------------------------------------------ |
| `ASSET CLASS`    | Canonical class from the whitelist (e.g. `401(k)`, `Roth IRA`, `Brokerage`) |
| `BROKER`         | Custodian / institution                                      |
| `ACCOUNT HOLDER` | Name on the account                                          |
| `AMOUNT`         | Ending balance in USD                                        |
| `Notes`          | Optional context (issue year, raw class if low-confidence, etc.) |

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install anthropic python-dotenv pydantic rapidfuzz reportlab pytest
```

Then set your API key:

```bash
cp .env.example .env
# edit .env and paste your ANTHROPIC_API_KEY
```

## Run

```bash
# Pretty print
python extract.py samples/mock_fidelity_401k.pdf

# CSV (5 columns)
python extract.py samples/mock_fidelity_401k.pdf --csv

# Raw JSON
python extract.py samples/mock_fidelity_401k.pdf --json
```

Low-confidence asset-class normalizations are logged to **stderr** so the CSV/JSON on stdout stays clean for piping.

## Tests

```bash
pytest tests/
```

Covers the fuzzy normalizer (`whitelist.normalize`) — the LLM path is exercised by the end-to-end run against `samples/mock_fidelity_401k.pdf`.

## Layout

- `whitelist.py` — canonical asset-class whitelist + `normalize()` (rapidfuzz, threshold 80)
- `schema.py` — pydantic `ExtractedAccount` / `ExtractionResult`
- `extractor.py` — Claude Messages API call with forced tool-use schema
- `extract.py` — argparse CLI
- `scripts/make_mock_pdf.py` — reportlab generator for the test fixture
