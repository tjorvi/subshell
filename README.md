# Subshell

Directory-aware prompt prefix line that manages local secrets and renders a reminder above your existing prompt (or just below a leading blank line if your prompt starts with one). It's lightweight, portable, and plays nicely with your current theme.

## For Contributors/AI Assistants

⚠️ **REQUIRED READING before making changes:**
- `TESTING.md` - Testing procedures and critical verification rules
- `DEVELOPING.md` - Development workflow  
- `SPEC.md` - Core requirements (especially OOTB requirement)

## Status

**Development**

Directory-aware prompt prefix line that manages local secrets and renders a reminder above your existing prompt (or just below a leading blank line if your prompt starts with one). It’s lightweight, portable, and plays nicely with your current theme.

Extreme simplicity is the current goal above production readyness or bells and
whistles.


## Status

**Development**

Features and configuration keys are under steady development.

## Why would I ever want that? What is it really for?

Many tools run a shell with a special environment activated somehow. `aws-vault` for one can spawn a subshell with AWS credentials loaded in the environment. But these subshells look and feel exactly like your normal shell so it can get confusing.
`SUBSHELL_PROMPT="AWS vault" subshell` will fix that.

Does your development project have prerequisites that need to be running in the development environment? Maybe databases or other services?

Something along the lines of `docker compose up -d && SUBSHELL_ROOT=. SUBSHELL_PROMPT="[$(pwd | basename) dev shell]" subshell ; docker compose down` will help beautifully with that.

## Environment & secrets management

Subshell can load local secrets into your shell environment safely and portably, without touching your prompt scripts.

Why this matters:
- Share one set of local secrets across multiple projects (no duplication).
- Stop leaking .env files to LLMs/agents: moving secrets out of your project directory prevents accidental uploads.

Quick how:
- Add `environment=...` lines to a `.subshell` in your project root.
- Use config names (shared across projects) or file paths (project-local). Later entries override earlier ones.
- Missing files print a prominent warning and the subshell still starts.

Quick example:

`.subshell` (in your project root):

environment=dev
environment=./secrets.local
environment=config:overrides

Then run `subshell` and your environment will include variables from those files.

## Configuration

- SUBSHELL_PROMPT: The label to display. Defaults to `subshell` if unset. If set to an empty string, no prefix is injected (you can still use `$SUBSHELL_OUTSIDE` in your own prompt logic).
- SUBSHELL_ROOT: Optional project root. Resolved to an absolute path. You’re “inside” when `$PWD` equals or is under this root; otherwise “outside”. If `SUBSHELL_ROOT` is unset and a `.subshell` file exists in `$PWD`, then `$PWD` is used as the root for this session and `SUBSHELL_ROOT` is set in the launched subshell.

## Supported shells

- zsh
- fish (3.6+)

It coexists cleanly with frameworks like oh-my-zsh and Starship; your base prompt remains untouched and continues to update normally.

### Starship integration (zsh & fish parity)

When Starship is present subshell now injects two custom modules (`$custom.subshell_inside`, `$custom.subshell_outside`) via a lightweight *ephemeral* Starship config file generated in your temp directory. Behavior is identical across zsh and fish:

- Zero‑config: if your existing `format` does not reference the modules, subshell splices them in ahead of the first `$all` (or at the beginning if `$all` is absent).
- Non‑intrusive: if you already reference either module in your own config nothing is changed – you keep full control.
- Outside vs inside logic is driven by the exported `$SUBSHELL_OUTSIDE` env var so the modules work even when Starship executes commands in a subshell.
- Disabling: set `SUBSHELL_NO_EPHEMERAL_STARSHIP=1` before launching the subshell to opt out (you can then manually add the modules to your own config if desired).
 - Lazy generation: set `SUBSHELL_LAZY_STARSHIP=1` to delay generating (and pointing `STARSHIP_CONFIG` at) the ephemeral config until Starship is actually initialized (session key present). This keeps your environment entirely untouched if Starship never loads during the subshell session.

Result: no duplicate prefix line; the visual indicator is rendered inline by Starship itself (mirrors the zsh strategy). Fish previously used a manual prefix line with Starship; that path is deprecated in favor of this unified module approach.

## Usage

- subshell                                 # label defaults to "subshell"
- SUBSHELL_PROMPT="[dev] " subshell        # custom label via env var
- SUBSHELL_PROMPT="🔧 debug-mode " subshell

Quote the env var value if it contains spaces or emoji, e.g. SUBSHELL_PROMPT="🔧 debug-mode " subshell.

## Screenshots & Demo Assets

The images under `assets/` (e.g. `test-zsh-starship.png`) are generated via lightweight VHS tapes built by `demo/generate_tapes.py` and executed inside a purpose-built container (`make image && make screenshots`).

Key implementation notes:
- Each prompt framework/theme (default, oh-my-zsh, powerlevel10k, starship) is represented by a distinct user layer in the demo image to ensure authentic initialization.
- The tape generator no longer forces a synthetic `PROMPT`; instead it lets the user’s real configuration (e.g. powerlevel10k segments, starship modules, fish prompt) render naturally before taking a screenshot.
- A short stabilization sleep is applied per theme so slower initializations (like starship’s first render) appear correctly.
- Screenshots are taken while still inside the launched subshell so the injected prefix line is visible along with the themed prompt.

To regenerate assets locally (requires Docker and access to the daemon):

```
make screenshots
```

If you are iterating on the activation scripts under `src/scripts/`, regenerate the bundled executable used inside the demo containers:

```
just bundle-rebuild   # or: python bundle.py
```

Then re-run screenshots to ensure containers see the latest prompt logic.

This will (re)build the demo image, generate or refresh tape files under `demo/tmp/tapes`, and run them to produce fresh PNGs and MP4 demo clips in `assets/`.

If a required screenshot fails to render the Make target will exit non‑zero and list which expected file was missing.

### Screenshot Regression Tests

Automated image snapshot tests guard against unintentional visual regressions in prompt rendering.

How it works:
- A pytest suite (`tests/test_screenshots.py`) invokes `make screenshots` lazily (only when an expected PNG is absent) and then compares each PNG in a curated allow‑list against a stored baseline using `pytest-regressions`' `image_regression` fixture.
- Baselines are committed under `tests/test_screenshots/` (created automatically on the first run or when forced to refresh).
- A helper test asserts that every PNG under `assets/` (excluding demo lifecycle images) is explicitly listed so additions are intentional.

Running the tests locally (requires Docker):

```
uv run -m pytest -k test_prompt_screenshots
```

Convenience commands (Just recipes):

```
just test-all          # run full pytest suite (uv run pytest -q)
just test-screenshots  # only screenshot regression tests
just bundle-rebuild    # rebuild bundled dist/bin/subshell after script edits
```

Regenerating (approving) new baselines after an intentional visual change:

```
uv run -m pytest --force-regen -k test_prompt_screenshots
git add tests/test_screenshots
```

CI Recommendation:
- Run `make screenshots` + `pytest -k test_prompt_screenshots` on pushes affecting `src/**`, `demo/**`, `Makefile`, or `assets/**`.
- Upload diff artifacts on failure so changed images can be inspected easily.

Adjusting sensitivity:
- Currently the comparison threshold is exact (`diff_threshold=0`). If minor, non‑deterministic pixel noise appears (e.g. font raster differences across platforms) raise the threshold or add a perceptual hash prefilter.

### Screenshot Approval Gating

In addition to the pixel baselines managed by `pytest-regressions`, a separate hash approval manifest (`tests/screenshot_approvals.json`) enforces an explicit acknowledge step for any visual change:

Workflow:
1. You (or CI) run the screenshot test suite.
2. If an image's SHA256 hash differs from the approved hash (or it's new) the test fails immediately (before pixel diff) and copies the current image into `tests/pending/` for inspection.
3. After manual review, re‑run with `--approve-screenshots` to update the manifest.

Commands:

```
# Run full suite (fails fast on unapproved changes)
uv run -m pytest -k test_prompt_screenshots

# Approve all current changes (after manual review)
uv run -m pytest -k test_prompt_screenshots --approve-screenshots

# Iterate quickly: skip already approved & unchanged images
uv run -m pytest -k test_prompt_screenshots --only-unapproved

# List any unapproved / changed images without running full tests
uv run python scripts/list_unapproved.py

# Makefile wrappers (regenerates images if needed first)
make approve-screenshots
make list-unapproved
make pending-screenshots
```

Artifacts:
- `tests/screenshot_approvals.json`: authoritative approved hashes.
- `tests/pending/`: current unapproved variants (overwritten on each failing run).

CI Recommendation:
- Run without `--approve-screenshots` so any change remains red until a human approves.
- Optionally archive `tests/pending/` on failure for direct download.

Rationale:
- Prevents accidental silent acceptance caused by re-generated pixel baselines.
- Keeps an auditable, code‑reviewable record of deliberate visual changes (hash diff in git).

Adding a new screenshot:
1. Add it to the generation pipeline (tape + make target ensures it appears in `assets/`).
2. Append its filename to `EXPECTED_IMAGES` in `tests/test_screenshots.py`.
3. Run the test once to create the baseline, then commit.

## Environment & secrets — details

How it works:
- Put `environment=...` lines in a `.subshell` file at your project root.
- Each line names a dotenv file to load, either by logical name in your config dir or by a file path:
	- Bare name (no slash) → `${XDG_CONFIG_HOME:-~/.config}/subshell/{name}`
	- Path-like (`./`, `../`, `~/`, `/`, or contains `/`) → treated as a file path; relative paths resolve against `SUBSHELL_ROOT`.
	- Optional prefixes for clarity (case-insensitive):
		- `config:NAME` → force lookup in config dir
		- `file:PATH` → force file semantics
- Lines are processed in order; later files override earlier variables on key conflicts.
- Missing files are reported prominently at startup but do not block the subshell.

Example resolution:
- `.subshell` contains:
	- `environment=dev`
	- `environment=./secrets.local`
	- `environment=config:overrides`
- Files resolved as:
	- `${XDG_CONFIG_HOME:-~/.config}/subshell/dev`
	- `$SUBSHELL_ROOT/secrets.local`
	- `${XDG_CONFIG_HOME:-~/.config}/subshell/overrides`

## Examples (approximate)

zsh default prompt, inside project root:

📂 %F{33}feature/XYZ%f
tjorvi@host ~/repo % 

zsh default prompt that begins with a blank line (prefix is placed below the blank line):


📂 %F{33}feature/XYZ%f
tjorvi@host ~/repo % 

zsh default prompt, outside project root (with SUBSHELL_ROOT=/Users/me/proj):

‼️  %F{196}feature/XYZ is outside project root (/Users/me/proj)%f ‼️
tjorvi@host ~/repo % 

fish default prompt, inside project root:

📂 feature/XYZ
tjorvi@host ~/repo> 

fish default prompt, outside project root:

‼️  feature/XYZ is outside project root (/Users/me/proj) ‼️
tjorvi@host ~/repo> 

nu default prompt, inside project root:

📂 feature/XYZ
> 
