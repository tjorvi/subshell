# Subshell

![Subshell Demo](verified-prompts/test-zsh-default.svg)

Directory-aware contextual subshell indicator. Adds a clearly styled prefix line (or inline segment via prompt frameworks) when you launch a purposeful subshell and (optionally) loads environment variables from declarative files. Zero‑config by default; integrates cleanly with zsh, fish, and Starship without replacing your existing prompt.

**Status:** Development (APIs & env vars may evolve; core behavior is stabilizing)

## Why This Exists

Have you ever:
- Run `aws-vault exec prod-account` and later forgotten you were still in a credentialed session?
- Dropped into `nix develop`, `poetry shell`, or a container shell and lost track of where secrets / versions came from?
- Switched `kubectl` context and wished the shell itself warned you it was “staging” not “prod”?

Most tools that mutate your env do it invisibly — your prompt still looks normal. Then muscle memory fires and you run the “just checking something” command in the shell that still has prod creds. This exists to make that harder.

`subshell` is a lightweight companion you wrap around those commands to make context explicit.

### Common Companions
Cloud & infra:
- `aws-vault exec …`
- `kubectl config use-context …`
- `gcloud auth activate-service-account …`
- `terraform workspace select …`

Dev environments:
- `nix develop` / `nix-shell`
- `poetry shell`, `pipenv shell`, `conda activate`, `pyenv shell`
- `rbenv shell`, `nvm use`
- `docker run -it`, `podman run -it`, `vagrant ssh`

Project/service prep:
- `docker compose up -d …`
- “dev shell” tasks that start databases, queues, sidecars

### The Value
Visual separation = fewer destructive mistakes, faster orientation when you return to a terminal, and a safer place to load ephemeral/local secrets.

## Quick Start

```bash
# Basic usage (prefix defaults to "subshell")
subshell

# AWS credentials session, make it very loud
aws-vault exec prod -- SUBSHELL_PROMPT="🔴 PROD AWS " subshell

# Project dev shell with services
docker compose up -d && \
  SUBSHELL_PROMPT="[myproj dev] " SUBSHELL_ROOT=. subshell ; \
  docker compose down

# Python project virtual env (poetry) with contextual label
poetry shell && SUBSHELL_PROMPT="📦 $(basename "$PWD") " subshell

# Kubernetes context clarity
kubectl config use-context staging && SUBSHELL_PROMPT="☸️  staging " subshell
```

### But I'm running a very customised prompt configuration that makes all my dreams come true
We've got you covered! Set `SUBSHELL_PROMPT=""` (empty) to suppress the visual prefix while still exporting `$SUBSHELL_PROMPT` and `$SUBSHELL_OUTSIDE` for you to integrate
into your own prompts.

## Features (High-Level)
- Clear contextual prefix (line above or inlined via prompt framework integration)
- Inside/outside project root detection (`SUBSHELL_ROOT`)
- Optional, ordered loading of environment/secret files via `.subshell`
- Ephemeral Starship config injection (unified zsh/fish behavior) with opt-outs
- Zero modification of your base prompt theme; reversible and isolated

## Configuration (Environment Variables)
| Variable | Purpose | Notes |
|----------|---------|-------|
| `SUBSHELL_PROMPT` | The label/prefix text. | Default `subshell`. Empty string disables visual prefix but keeps logic vars. |
| `SUBSHELL_ROOT` | Absolute/relative path establishing an “inside” tree. | Auto-set if a `.subshell` file is in `$PWD` and not already set. |


## `.subshell` File & Secrets Loading
Place a `.subshell` file at (or beneath) your project root. It may contain lines like:

```
environment=dev
environment=./secrets.local
environment=config:overrides
```

Resolution rules (processed top→bottom; later overrides earlier):
1. Bare name (no slash) → `${XDG_CONFIG_HOME:-~/.config}/subshell/<name>`
2. Path-like (`./`, `../`, `~/`, `/`, or contains `/`) → treat as file path; relative paths resolve against `SUBSHELL_ROOT` (or the directory containing the `.subshell` if root inferred).
3. Optional prefixes (case-insensitive): `config:NAME` (force config lookup), `file:PATH` (force path semantics).

Behavior:
- Missing files: warned (non-fatal) so you see what didn’t load.
- Duplicate keys: later file wins.
- Safe: No mutation of your existing prompt scripts required.

## Supported Shells & Prompt Frameworks
Shells:
- zsh
- fish (3.6+)

Framework / theme integration:
- Starship (zsh & fish)
- Oh-my-zsh (zsh)
- Powerlevel10k (zsh)

### Starship Integration Details
When Starship is present, subshell writes a minimal temporary config and points `STARSHIP_CONFIG` at it (unless disabled). It:
- Splices the custom modules ahead of first `$all` (or start of `format` if `$all` absent) when you have not referenced them yourself.
- Leaves your config untouched if you already reference either module.
- Relies on `$SUBSHELL_OUTSIDE` so modules work even in Starship-executed subshell commands.
- Can be disabled (`SUBSHELL_NO_EPHEMERAL_STARSHIP=1`) or made lazy (`SUBSHELL_LAZY_STARSHIP=1`).

Result: no duplicate top prefix line; visual status appears inline like any other segment.

## Advanced Usage Patterns
Inline custom logic in your own prompt (zsh example):
```zsh
if [[ -n $SUBSHELL_OUTSIDE ]]; then
  PS1="‼️  outside ($SUBSHELL_ROOT) ‼️ $PS1"
fi
```

Suppress built-in prefix but keep state:
```bash
SUBSHELL_PROMPT="" subshell
```

Project-local helper script pattern:
```bash
# dev-shell.sh
#!/usr/bin/env bash
set -euo pipefail
docker compose up -d
SUBSHELL_PROMPT="[backend dev] " SUBSHELL_ROOT=. subshell
docker compose down
```

## Visual Examples
zsh (inside root):
```
📂 subshell
user@host ~/repo %
```
zsh (outside root):
```
‼️  subshell is outside project root (/path/to/root) ‼️
user@host ~/repo %
```
fish (inside root):
```
📂 subshell
user@host ~/repo>
```
fish (outside root):
```
‼️  subshell is outside project root (/path/to/root) ‼️
user@host ~/repo>
```

## Contributor / AI Assistant Guide
Please read before submitting changes:
- `TESTING.md` – Verification rules & diff discipline
- `DEVELOPING.md` – Local workflow & build info
- `SPEC.md` – Core behavior & OOTB requirements
- `DESIGN_DECISIONS.md` – Rationale & trade‑offs

Preferred contribution style:
1. Add/adjust tests first when altering visible behavior.
2. Keep shell logic minimal & portable (avoid unnecessary external deps).
3. Maintain deterministic ordering for anything written to disk (important for tests).

## License
See `LICENSE` for details.


**Happy contextual hacking! 🐚**
