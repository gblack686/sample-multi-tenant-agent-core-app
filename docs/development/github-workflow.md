# GitHub Workflow & Best Practices

## Branch Strategy

```
main              ← production-ready, protected
  └── dev/greg    ← Greg's feature work
  └── dev/hoque   ← Hoque's feature work
```

- **Never push directly to `main`** — always use PRs
- Each dev works on their own branch, PRs into `main`
- Keep branches short-lived (days, not weeks)

## Daily Workflow

```bash
# Start of day — sync with main
git fetch origin
git rebase origin/main

# Work on your feature, commit often
git add <files>
git commit -m "feat: add subscription tier validation"

# Push and open PR when ready
git push -u origin dev/greg
gh pr create --title "Add subscription validation"
```

## PR Rules

1. **Small PRs** — easier to review, fewer conflicts
2. **One concern per PR** — don't mix a bug fix with a new feature
3. **Require 1 approval** before merge
4. **Use squash merge** into main — keeps history clean

## Branch Protection (GitHub Settings)

```
Settings → Branches → Add rule for "main":
  ✓ Require pull request before merging
  ✓ Require 1 approval
  ✓ Require status checks (CI passes)
  ✓ Require branch is up to date
```

## Commit Message Convention

```
feat:     add new capability
fix:      correct a bug
refactor: restructure without behavior change
docs:     documentation only
chore:    build, CI, dependencies
```

## Avoiding Conflicts

- **Communicate** — "I'm working on the backend routes today"
- **Pull often** — rebase on main daily
- **Don't both edit the same file** — split work by module

## Suggested Work Split

| Greg | Hoque | Why |
|------|-------|-----|
| Backend / CDK / Plugin | Frontend / UI | Minimal file overlap |
| `server/`, `infrastructure/`, `eagle-plugin/` | `client/` | Natural boundary |

## Development Workflow

| Stage | Purpose | Speed |
|-------|---------|-------|
| Local (no Docker) | Code + debug | Seconds |
| Local Docker | Validate containers | Minutes |
| Fargate (dev) | Integration / demos | CI/CD pipeline |

### Local Development (no Docker)

```bash
# Backend
cd server && uvicorn app.main:app --reload --port 8000

# Frontend
cd client && npm run dev
```

### Local Docker (pre-push validation)

```bash
docker compose -f deployment/docker-compose.dev.yml up --build
```

### Deploy to Fargate

Push to your branch → open PR → merge to main → CI/CD auto-deploys.
