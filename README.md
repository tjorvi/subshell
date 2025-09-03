# Subshell

Directory-aware prompt prefix line that renders above your existing prompt (or just below a leading blank line if your prompt starts with one). It’s lightweight, portable, and plays nicely with your current theme.


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

## Usage

- subshell                                 # label defaults to "subshell"
- SUBSHELL_PROMPT="[dev] " subshell        # custom label via env var
- SUBSHELL_PROMPT="🔧 debug-mode " subshell

Quote the env var value if it contains spaces or emoji, e.g. SUBSHELL_PROMPT="🔧 debug-mode " subshell.

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
