# TAC Plan: Build a Working Jira System in `scripts/` (Dry-Run Validated)

## TAC Analysis

| Dimension | Assessment |
|-----------|------------|
| Agentic Layer | Class 2: Out-Loop (autonomous scripts + CI workflows) |
| Primary Framework | PITER (Plan → Implement → Test → Evaluate → Refine) |
| ADW Pattern | Test-First Agentic + Plan-Build-Validate |
| Key Tactics | 4 (Stay Out of the Loop), 5 (Feedback Loops), 7 (Zero-Touch), 8 (Prioritize Agentics) |
| Anti-patterns to avoid | Manual test steps, missing validation, live API calls during dev |

## Current State Assessment

### What exists
| File | Status | Notes |
|------|--------|-------|
| `scripts/jira_connect.py` | Functional | Bearer PAT auth, CRUD ops (connect, projects, search, comment, create) |
| `scripts/jira_commits_sync.py` | Functional | `--dry-run` flag, author filter, weekly issue, JQL lookup |
| `.github/workflows/jira-commits-sync.yml` | Untested | Nightly cron, cache-based SHA tracking |
| `.github/workflows/jira-commits-sync-agentic.yml` | Untested | Claude Code Action variant |
| `.env` | Present | `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` |

### What's broken/missing
1. **No test harness** — Can't validate scripts without hitting live Jira
2. **No dry-run for `jira_connect.py`** — Only `jira_commits_sync.py` has `--dry-run`
3. **No validation script** — No way to run all scripts end-to-end in dry mode
4. **No CLI entrypoint** — Each script runs independently, no unified `jira_cli.py`
5. **Auth mismatch clarity** — `.env` has `JIRA_EMAIL` but `jira_connect.py` only uses Bearer token (email unused)

## Implementation Plan

### Step 1: Add dry-run test harness for `jira_connect.py`
- **TAC tactic**: 5 (Feedback Loops) — validation must be built in
- **Details**: Add a `--dry-run` mode to `jira_connect.py` that validates env vars, builds request URLs, and prints what _would_ be called without making HTTP requests
- **Validation**: `python scripts/jira_connect.py --dry-run` exits 0 and prints connection details

### Step 2: Create `scripts/jira_test.py` — unified dry-run validation
- **TAC tactic**: 4 (Stay Out of the Loop) — one command tests everything
- **Details**: A test script that:
  - Validates `.env` is loaded and all required vars are set
  - Validates URL format (`JIRA_BASE_URL` is reachable or valid)
  - Dry-runs `jira_connect.py` functions (shows what would be called)
  - Dry-runs `jira_commits_sync.py` with recent commits
  - Reports pass/fail for each check
- **Validation**: `python scripts/jira_test.py` exits 0 with clear status output

### Step 3: Fix unused `JIRA_EMAIL` and document auth pattern
- **TAC tactic**: 2 (Adopt Agent's Perspective) — clear context for future runs
- **Details**: Either use `JIRA_EMAIL` in basic auth (some Jira instances need it) or remove it from `.env` to avoid confusion. Document the auth pattern (Bearer PAT for self-hosted NCI Jira)
- **Validation**: No unused env vars, clear docstring in `jira_connect.py`

### Step 4: Run all dry-run validations
- **TAC tactic**: 5 (Feedback Loops) — execute and verify
- **Details**: Run the full validation suite:
  ```bash
  python scripts/jira_test.py
  python scripts/jira_commits_sync.py --dry-run --since 7days --project EAGLE
  ```
- **Validation**: All scripts exit 0, output is coherent

### Step 5: Validate GitHub Actions workflow syntax
- **TAC tactic**: 7 (Zero-Touch Deployment)
- **Details**: Lint both workflow YAML files for syntax correctness
- **Validation**: `python -c "import yaml; yaml.safe_load(open(...))"` or `actionlint`

## Files to Create/Modify

| File | Action | Layer |
|------|--------|-------|
| `scripts/jira_connect.py` | Edit — add `--dry-run` CLI mode | Class 2 |
| `scripts/jira_test.py` | Create — unified dry-run test harness | Class 2 |
| `scripts/jira_commits_sync.py` | Minor — verify dry-run path works | Class 2 |
| `.env` | Review — clarify JIRA_EMAIL usage | Class 1 |

## Validation Strategy

- [ ] `python scripts/jira_connect.py --dry-run` — validates env + prints auth info (Tactic 5)
- [ ] `python scripts/jira_test.py` — full dry-run suite passes (Tactic 5)
- [ ] `python scripts/jira_commits_sync.py --dry-run --since 7days` — shows commits without API calls (Tactic 5)
- [ ] No secrets printed in plain text during dry-run (security check)
- [ ] Workflow YAML files parse correctly (Tactic 7)

## TAC Compliance Checklist

- [x] Agent does the work, not human (Tactic 1) — all implementation via Claude
- [x] Agent can complete without interruption (Tactic 4) — dry-run means no live API needed
- [x] Validation built into workflow (Tactic 5) — test harness + dry-run flags
- [x] Single-purpose prompts where applicable (Tactic 6) — each script has one job
- [x] Automated end-to-end where possible (Tactic 7) — CI workflows already defined
- [ ] Self-improve step included (ACT-LEARN-REUSE) — update after dry-run results

## Dry-Run Execution Plan

After build, run these commands to validate (NO live Jira calls):

```bash
# 1. Unit validation - env + auth
python scripts/jira_connect.py --dry-run

# 2. Full test suite
python scripts/jira_test.py

# 3. Commits sync dry-run (last 7 days)
python scripts/jira_commits_sync.py --dry-run --since "7 days ago" --project EAGLE --weekly-summary "greg dev"

# 4. Commits sync dry-run (specific author)
python scripts/jira_commits_sync.py --dry-run --since "7 days ago" --project EAGLE --author "gblack686,blackga-nih"
```
