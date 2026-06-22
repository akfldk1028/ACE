# Multi-Repo Push Memo - 2026-06-22

## Verified independent Git repositories

Verified with `git rev-parse --show-toplevel`, `git remote -v`, branch,
latest commit, and `git status --short --branch`.

| Project | Path | Remote | Branch | Latest pushed commit | Status |
|---|---|---|---|---|---|
| ACE root | `D:\Data\25_ACE` | `https://github.com/akfldk1028/ACE.git` | `DK-BB` | `4b86d53 Record nested project updates` | clean vs origin |
| ARR | `D:\Data\25_ACE\ARR` | `https://github.com/akfldk1028/ARR.git` | `master` | `767963d Update ARR workspace assets` | clean vs origin |
| AUA | `D:\Data\25_ACE\AUA` | `https://github.com/akfldk1028/AUA.git` | `main` | `2214165 Add packing reference artifact` | clean vs origin |
| AG | `D:\Data\25_ACE\AG` | `https://github.com/akfldk1028/AG.git` | `master` | `179fe49 Update AG research and A2A workspace` | pushed; generated web UI files remain modified locally |
| ARG | `D:\Data\25_ACE\AG\agent` | `https://github.com/akfldk1028/ARG.git` | `master` | `4f87946 Update law domain A2A agents` | clean vs origin |
| korean-law-mcp | `D:\Data\25_ACE\korean-law-mcp` | `https://github.com/chrisryugj/korean-law-mcp.git` | `main` | `6150e13 chore: update description and keywords for v3.0.0` | clean vs origin |

## Boundary notes

- `AG-light` is not a separate Git repository. It belongs to the ACE root repo.
- `AUA` and `korean-law-mcp` are recorded in ACE as gitlinks (`160000` entries).
- `ACE` currently has no `.gitmodules`, so `git submodule status` fails with
  `no submodule mapping found in .gitmodules for path 'AUA'`.
- `ARR` and `AG` are independent nested Git repositories, but ACE also has many
  regular tracked files under those directories. Treat this as mixed legacy
  structure, not a clean submodule-only layout.
- Do not use `git add .` in this workspace. Stage explicit paths only.
- Filtered/excluded during push: generated web UI output, `.wrangler`, `NUL`,
  large embedding JSON, venvs, local caches, db files, security key files, and
  local reference clones.
