# Iteration Guide — How to systematically improve the extractor

## The mindset

Prompt engineering is **diagnosis, not authorship**. You're not "writing a better prompt" — you're finding the specific failure mode in the current prompt and patching it with the smallest possible change. Big rewrites tend to introduce new failures.

## The loop

```
1. Run extraction on all samples
2. Log results in evaluation_tracker.xlsx
3. Identify the SINGLE most impactful failure
4. Add ONE rule/example/clarification to the system prompt to fix it
5. Re-run
6. Confirm the fix worked AND nothing regressed
7. Commit the prompt change with a message describing what you fixed
8. Repeat until ~95% pass rate
```

**Important:** one change per iteration. If you change three things at once and accuracy goes up, you don't know which change helped. If it goes down, you don't know which change hurt.

## Common failure modes and how to fix them

### Failure: asset_class is close but not exact (e.g. "401K" instead of "401(k)")
**Why it happens:** the LLM is paraphrasing the canonical string.
**Fix:** the normalizer should already catch this. If it's not, lower the rapidfuzz threshold from 80 to 70 in `whitelist.py`. If still missing, add the variant explicitly to a SYNONYMS dict in `whitelist.py`.

### Failure: 401(k) statement returns 1 row instead of 4
**Why it happens:** the LLM is collapsing money types into a total.
**Fix:** Strengthen Rule 1 with an explicit example showing the input table and the expected 4-row output. Few-shot examples are very effective here.

### Failure: account_holder includes last name or is "Manu Sharma" instead of "Manu"
**Why it happens:** Rule 6 isn't being followed.
**Fix:** Add a concrete example to Rule 6: "If statement shows 'Manu Sharma' or 'Mr. Manu Sharma', extract 'Manu'."

### Failure: amount has commas, dollar signs, or comes through as a string
**Why it happens:** structured outputs schema is too loose, OR the LLM is being overly faithful to the source format.
**Fix:** First check `schema.py` — `amount` must be `float`, not `str`. Then strengthen Rule 7 with a transformation example: "$471,000.00 → 471000.00".

### Failure: For Whole Life, amount is the death benefit instead of cash value
**Why it happens:** LLM picks the bigger/more prominent number.
**Fix:** Make Rule 4 more explicit: "If you see both a 'Cash Value' and a 'Death Benefit' on a whole life policy, the amount MUST be the cash value."

### Failure: Joint account becomes one of the spouse's names instead of "Joint"
**Why it happens:** Statement may list both names without explicitly saying "joint."
**Fix:** Update Rule 6: "If two account holders are listed and neither is a minor, default to 'Joint' unless the document explicitly states otherwise."

### Failure: Non-account documents return fabricated accounts
**Why it happens:** LLM is trying to be helpful even when there's nothing to extract.
**Fix:** Strengthen Rule 8 with examples of non-account docs (benefits guide, exec comp explainer, tax form). Add: "If you find yourself inferring or estimating, return unmatched: true instead."

## Diminishing returns checkpoint

Once you've passed all 3 mock samples reliably, **stop iterating on mocks and wait for Joyce's real samples**. The mocks are clean and structured; her real PDFs will expose new patterns the mocks can't predict.

If you hit ~80% on mocks but can't get to 95%, that's usually a sign the failure is in:
- The schema (try making fields more constrained)
- The model (try switching to a different model temporarily to see if it's a capability gap)
- The PDF rendering (some PDFs are scanned images, requiring different handling)

## Regression testing

Every time you change the prompt, re-run **all** samples, not just the one you were fixing. If a fix for the Fidelity case breaks the Chase case, you've made things worse.

The eval tracker spreadsheet is built for this — keep iteration history so you can roll back if needed.

## When to stop

You're done with Phase 1 prompt tuning when:
- All mock samples pass on a clean run
- 3-5 of Joyce's real samples pass with no manual correction needed
- Joyce confirms the CSV output drops into her sheet cleanly

That's the bar. Don't keep tuning beyond it — your time is better spent on Phase 2 once she's actually using the tool.
