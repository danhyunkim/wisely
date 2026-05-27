# Post-Scaffold Runbook — What to do after Claude Code finishes

## Estimated time: 60-90 minutes total

---

## Step 1 — Verify the scaffold (5 min)

Claude Code should report back when done. Before doing anything else, check:

```bash
cd ~/joyce-extractor  # or wherever it set up
ls -la
```

You should see: `whitelist.py`, `schema.py`, `extractor.py`, `extract.py`, `.env.example`, `.gitignore`, `tests/`, `samples/`, `README.md`, and a git repo.

Quick sanity checks:
```bash
git log --oneline          # Should show multiple commits, one per file
cat whitelist.py | head    # Should have the WHITELIST dict
pytest tests/              # Normalizer tests should all pass
```

**If anything's missing or wrong, fix it before moving on.** Don't iterate on a broken scaffold.

---

## Step 2 — Add your API key (1 min)

```bash
cp .env.example .env       # if not done already
# Open .env and paste your Anthropic API key
```

---

## Step 3 — Replace the system prompt with the tuned version (5 min)

Claude Code wrote a generic system prompt. I've written a more carefully-tuned one — see `extractor_system_prompt.md` in this folder. Open `extractor.py`, find the system prompt string, and replace it with the contents of that file.

Commit it:
```bash
git add extractor.py
git commit -m "Replace system prompt with tuned version"
```

---

## Step 4 — Drop in the additional test samples (2 min)

Claude Code generated one mock Fidelity 401(k) PDF. I've created two more in this folder for broader coverage:
- `samples/mock_schwab_brokerage.pdf` — single-account brokerage
- `samples/mock_chase_bank.pdf` — checking + savings (tests multi-row split for bank)

Copy them into `samples/` in your repo.

---

## Step 5 — Run the first real test (5 min)

```bash
python extract.py samples/mock_fidelity_401k.pdf --csv
python extract.py samples/mock_schwab_brokerage.pdf --csv
python extract.py samples/mock_chase_bank.pdf --csv
```

Open `evaluation_tracker.xlsx` (in this folder) and log results for each:
- Did it extract the right number of rows?
- Did all asset_class values match the whitelist exactly?
- Are amounts numeric and correct?
- Any low-confidence warnings on stderr?

---

## Step 6 — First iteration loop (30-60 min)

This is where the real work is. Follow `iteration_guide.md`.

The TL;DR: for each error in the eval tracker, add a more specific rule or example to the system prompt, re-run, log results. Aim for ~95% accuracy across the 3 mock samples before stopping.

---

## Step 7 — Commit and push (2 min)

```bash
git add .
git commit -m "Tuned prompt to pass all 3 mock samples"
git push origin main
```

If `gh` wasn't available earlier:
```bash
gh repo create joyce-extractor --public --source=. --push
```

---

## Step 8 — Email Joyce for real samples (1 min)

Send her the email I drafted (you have two versions). The mock samples got you to a working tool; her real samples are what get you to a *useful* tool.

---

## Step 9 — Stop. Don't build Phase 2 yet.

When you've passed Step 7, you have a working Phase 1 scaffold. **Resist the urge to build the populator, the UI, or anything else until Joyce has actually used the CSV output on a real client.**

The next thing on the critical path is *her samples*, not more code.

See `phase_2_handoff.md` for what comes after Joyce gives the green light.
