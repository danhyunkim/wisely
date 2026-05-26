# Handoff 1 — wisely

Python CLI scaffold for extracting financial account data from PDF statements via Claude vision + tool use.

## What's been built (3 commits, pushed to `main`)

- `ab2c79b` — `.gitignore`, `.env.example`, `scripts/make_mock_pdf.py`, `samples/mock_fidelity_401k.pdf` (reportlab-generated Fidelity 401(k) statement with pre-tax, employer match, after-tax, Roth balances)
- `620b97e` — `whitelist.py`: `WHITELIST` dict (8 categories), `ALL_CLASSES`, `CATEGORY_FOR()`, `normalize()` using `rapidfuzz.fuzz.token_set_ratio` + `rapidfuzz.utils.default_process` at threshold 80. Verified manually against the 5 spec test cases.
- `4fc68cd` — `schema.py`: `ExtractedAccount` (asset_class, broker, account_holder, amount, notes) + `ExtractionResult` (accounts, document_type, unmatched, unmatched_summary)

Remote: `https://github.com/danhyunkim/wisely` (HTTPS — SSH key wasn't set up).

## Local-only state (won't transfer)

- `.venv/` — recreate with `python3 -m venv .venv && source .venv/bin/activate && pip install anthropic python-dotenv pydantic rapidfuzz reportlab pytest`
- `.env` — has the API key locally, gitignored. On another machine: `cp .env.example .env` and paste your `ANTHROPIC_API_KEY`.

## Remaining todos (in order)

1. **`extractor.py`** — `extract_from_pdf(pdf_path) -> ExtractionResult`
   - Base64-encode PDF, send to `claude-opus-4-7` via Messages API with `document` content block (vision handles PDFs natively, no OCR)
   - Force schema with **tool use**: define a single tool whose `input_schema` matches `ExtractionResult.model_json_schema()`, set `tool_choice={"type": "tool", "name": "..."}`
   - System prompt must include the whitelist and these provider rules:
     - Fidelity 401(k): split into separate rows for `401(k)`, `401(k) Match`, `After Tax 401(k)`, `Roth 401(k)` by money type
     - Whole Life: capture issue year + term in notes
     - Brokerage: one row per account, `asset_class = "Brokerage"` unless individual stocks (`"Stock"`)
     - Crypto exchanges → `"Crypto"`
     - Bank: separate rows for checking/savings
     - Non-financial docs (exec comp, benefits charts) → `unmatched=True` + summary
   - Post-LLM: run each `asset_class` through `whitelist.normalize()`, snap to canonical. If confidence < 80, put raw string in `notes` and flag.
   - Note: user said "I have a more carefully-tuned system prompt I'll swap in after you finish — just write a reasonable first version."

2. **`extract.py`** — argparse CLI
   - `python extract.py <pdf_path> [--csv] [--json]`
   - Default: pretty print
   - `--csv`: headers `ASSET CLASS, BROKER, ACCOUNT HOLDER, AMOUNT, Notes`
   - `--json`: raw JSON
   - Low-confidence normalizations → warn to stderr
   - **argparse only — no Click/Typer**

3. **`tests/test_normalize.py`** — 5 cases:
   - `"401k"` → `"401(k)"`
   - `"401 K"` → `"401(k)"`
   - `"Roth IRA"` → exact
   - `"Whole Life Policy"` → `"Whole Life"`
   - `"Random gibberish xyz"` → `(None, 0)`

4. **`README.md`** — brief: what it does, install, run, 5-field schema.

5. **Verify**: `pytest tests/` (normalizer already passes manual checks)

6. **End-to-end run** (don't skip — this is the deliverable):
   ```
   python extract.py samples/mock_fidelity_401k.pdf --csv
   ```
   Expect 4 rows from the mock: Pre-Tax (401(k)), Employer Match (401(k) Match), After-Tax (After Tax 401(k)), Roth 401(k). All broker=Fidelity, account_holder="Jordan A. Sample".

7. **Push final commits**: `git push origin main`

## Hard constraints from the original brief

- Deps allowed: `anthropic`, `python-dotenv`, `pydantic`, `rapidfuzz`, `reportlab` (mock only), `pytest`. Nothing else.
- **No** Click/Typer, async, OCR, web UI, DB, FastAPI/Flask, factories, "extensible architecture". This is a scaffold.
- One commit per file with clear message.
- Synchronous only.

## Style nits learned this session

- `rapidfuzz`'s `token_set_ratio` is case- and punctuation-sensitive by default — must pass `processor=utils.default_process` for `"401 K"` to match `"401(k)"`.
- Exact case-insensitive match short-circuits to confidence 100 in `normalize()` before fuzzy fallback.
