# Contributing

Guide for the NTS team. For agent constitution and full structural rules, read `CLAUDE.md` at the repo root first.

---

## Branch Conventions

Branch from `main`:
```
feature/short-description
fix/short-description
docs/short-description
```

Never push directly to `main`. All changes go through a PR.

---

## Commit Messages

Format: `type(scope): description`

```
feat(scanner): add LLDP neighbor discovery
fix(frontend): handle empty topology gracefully
docs: update API reference
chore(docker): bump redis to 7.4
refactor(inference): simplify gateway detection logic
test(scanner): add unit tests for SNMP poller
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
Scopes: `scanner`, `inference`, `graph`, `frontend`, `api`, `docker`, `demo`, `ai`

---

## Where to Put New Code

| What you're adding | Where it goes |
|-------------------|---------------|
| New API endpoint | New file in `backend/app/routers/`, register in `main.py` |
| New business logic | New file in appropriate `backend/app/services/` subdirectory |
| New Pydantic model | `backend/app/models/` |
| New React component | `frontend/src/components/[dashboard\|graph\|layout\|panels\|shared]/` |
| New custom hook | `frontend/src/hooks/` |
| New Zustand store | `frontend/src/stores/` |
| New utility | `frontend/src/lib/` |
| New type definition | `frontend/src/types/` |

---

## Testing Before Submitting

```bash
# Backend tests must pass
cd backend && python -m pytest tests/

# Frontend build must succeed (no TypeScript errors)
cd frontend && npm run build

# If you changed Docker config:
./demo.sh down && ./demo.sh up   # all services must reach healthy state

# If you changed scan logic:
./demo.sh scan   # verify devices and edges appear in the graph
```

---

## Pull Request Process

1. Push your branch: `git push -u origin feature/your-feature`
2. Open a PR against `main`
3. Fill in the description: what changed, why, how to test it
4. Link related issues
5. Request review from a teammate
6. Address review feedback
7. Merge once approved — use squash or merge commit, not rebase

---

## Structural Rules

These are enforced across all contributions — see `CLAUDE.md` for the full list:

- No new top-level directories in `network-topology-mapper/` without team discussion
- No Celery (scheduling uses asyncio in `main.py` lifespan)
- No `network_mode: host` in Docker compose files (breaks Mac)
- Never commit `.env` files
- Never touch `Research-Paper/` without team discussion
