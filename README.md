# Subshell

Directory-aware prompt prefix line that manages l- SUBSHELL_PROMPT: The label to display. Defaults to `subshell` if unset. If set to an empty string, no prefix is injected but `$SUBSHELL_OUTSIDE` is still exported for custom prompt logic.
- SUBSHELL_ROOT: Optional project root. Resolved to an absolute path. You're "inside" when `$PWD` equals or is under this root; otherwise "outside". If `SUBSHELL_ROOT` is unset and a `.subshell` file exists in `$PWD`, then `$PWD` is used as the root for this session and `SUBSHELL_ROOT` is set in the launched subshell.al secrets and renders a reminder above your existing prompt (or just below a leading blank line if your prompt starts with one). It's lightweight, portable, and plays nicely with your current theme.

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

It coexists cleanly with supported prompt frameworks; your base prompt remains untouched and continues to update normally.

### Prompt framework support

- **Starship** (zsh & fish): Injects custom modules via ephemeral config
- **Fish default prompt**: Wraps prompt function to inject prefix
- **Zsh default prompt**: Hooks into prompt rendering
- **Powerline10k**: Planned (see DESIGN_DECISIONS.md)

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

Quote the env var value if it contains spaces or emoji. Set to empty string to disable the prefix (exposes `$SUBSHELL_OUTSIDE` for custom prompt integration).

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

## Testing

Run `just test` to generate prompt files and compare against known-good sources in the `verified-prompts/` directory.

**CRITICAL**: When tests fail with "Mismatched files", first examine the diff to determine if changes are intentional improvements or regressions. Only update verified files after confirming changes are improvements. See `TESTING.md` for detailed procedures.

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

📂 subshell
tjorvi@host ~/repo % 

zsh default prompt that begins with a blank line (prefix is placed below the blank line):


📂 subshell
tjorvi@host ~/repo % 

zsh default prompt, outside project root (with SUBSHELL_ROOT=/Users/me/proj):

‼️  subshell is outside project root (/Users/me/proj) ‼️
tjorvi@host ~/repo % 

fish default prompt, inside project root:

📂 subshell
tjorvi@host ~/repo> 

fish default prompt, outside project root:

‼️  subshell is outside project root (/Users/me/proj) ‼️
tjorvi@host ~/repo> 
