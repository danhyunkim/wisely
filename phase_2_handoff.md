# Phase 1 → Phase 2 Handoff

## Phase 1 exit criteria (you're here)

Before starting Phase 2, ALL of these should be true:

- [ ] Extractor passes 95%+ on Joyce's real samples (not just mocks)
- [ ] Joyce has used the CSV output for at least 1 real client
- [ ] She has explicitly told you "this saves me time" (or words to that effect)
- [ ] You have a decision from her on Path A vs Path B (see below)

If any of these aren't true, **don't start Phase 2.** Go back and finish them.

## The Phase 2 decision

Two paths to merging the extractor with her planning spreadsheet. Joyce should pick.

### Path A — Extend her existing spreadsheet (faster, lower ceiling)
- Tool generates a CSV with the 5 fields + a `client_id` column
- Joyce pastes into the "Current Assets" tab of a client's copy of the master sheet
- Optional: Google Sheets API integration that appends rows directly to a client's sheet
- **Pros:** Zero workflow change. Joyce keeps using Excel/Sheets exactly as she does today.
- **Cons:** File-per-client is messy, no audit trail, hard to scale past ~50 clients.
- **Time estimate:** 1-2 days

### Path B — Replace the spreadsheet with a webapp (slower, higher ceiling)
- Build out the 3 input tabs as Supabase tables, 3 output tabs as live-rendered views
- Joyce drags items between Aggressive/Conservative buckets in the UI
- Generates the client presentation as a PDF or shareable link
- **Pros:** Multi-client management, version history, audit trail, can layer Phase 3 agent on top cleanly.
- **Cons:** Joyce has to learn a new tool. If she resists, you've wasted weeks.
- **Time estimate:** 2-3 weeks

### What I'd recommend

Default to **Path A** unless Joyce is excited about Path B. The whole bias toward action means proving value before building infrastructure. Path A also tells you whether she'll actually adopt the tool at all — if she won't paste a CSV, she sure won't switch to a webapp.

## Phase 2 build plan (assuming Path A)

### Step 1 — Multi-client structure (½ day)
- Add a `client_id` field to every extraction
- Set up a Supabase table `extractions` with: id, client_id, source_filename, asset_class, broker, account_holder, amount, notes, raw_llm_output, confidence, created_at
- CLI gets a `--client` flag: `python extract.py statement.pdf --client kim-family --csv`

### Step 2 — Upload UI (½ day)
- Spin up a v0/Lovable React app on Vercel with one route
- Drag-drop multi-file upload
- Server-side: receives PDFs, calls extractor, returns aggregated CSV
- No auth yet — gate behind a single password Joyce shares with her team

### Step 3 — Google Sheets sync (1 day, optional)
- If Joyce has her master sheet in Google Sheets (not Excel), use Sheets API
- "Sync to sheet" button: appends extracted rows to the "Current Assets" tab of a specific sheet by URL
- Watch out for: formula propagation (her existing formulas in rows below should auto-fill the new rows), and column ordering must match exactly

### Step 4 — Per-provider quirks library
- As Joyce uses the tool, she'll find statements that fail in interesting ways
- Build a small "provider hints" system where each provider can have additional extraction notes
- Keep this in a YAML or JSON file so non-engineers (Joyce, Adrienne) can add hints

## Phase 3 preview — the agent

Only start Phase 3 when you have **20+ completed plans** stored from Phase 2. That's roughly when pattern-matching becomes useful.

The minimum viable agent:
- Stores each completed plan as a structured record (client demographics, assets, what Joyce recommended, what bucket/order she chose)
- When a new plan starts, retrieves the 3-5 most similar past plans via embedding similarity
- Surfaces those past plans as suggestions in the UI: "You had 3 similar clients last year — here's what you did"
- Does NOT auto-decide anything. Joyce stays in control.

The key insight from her call: she wants the tool to **learn her**, not to **replace her judgment**. Build for augmentation, not automation.

## Anti-patterns to avoid

1. **Building UI before the extractor is reliable.** A pretty UI on top of a broken extractor is worse than a CLI on top of a working one.
2. **Adding ML/embeddings/RAG before there's data.** Without 20+ real plans, the agent has nothing to learn from.
3. **Building multi-tenant before single-tenant works.** Joyce's firm is one user. Don't over-architect for SaaS.
4. **Scope creeping from Joyce.** She'll have ideas as she uses it. Capture them, but don't build them mid-iteration. Finish what you started first.
5. **Showing her the code/tech stack.** She doesn't care. Show her the output. The CSV is the product to her, not the Python.
