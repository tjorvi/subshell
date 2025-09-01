# Subshell

Directory-aware prompt prefix line that renders above your existing prompt (or just below a leading blank line if your prompt starts with one). It’s lightweight, portable, and plays nicely with your current theme.

## Why would I ever want that? What is it really for?

Many tools run a shell with a special environment activated somehow. `aws-vault` for one can spawn a subshell with AWS credentials loaded in the environment. But these subshells look and feel exactly like your normal shell so it can get confusing.
`SUBSHELL_PROMPT="AWS vault" subshell` will fix that.

Does your development project have prerequisites that need to be running in the development environment? Maybe databases or other services?

Something along the lines of `docker compose up -d && SUBSHELL_ROOT=. SUBSHELL_PROMPT="[$(pwd | basename) dev shell]" subshell ; docker compose down` will help beautifully with that.

## Configuration

- SUBSHELL_PROMPT: The label to display. Defaults to `subshell` if unset. If set to an empty string, no prefix is injected (you can still use `$SUBSHELL_OUTSIDE` in your own prompt logic).
- SUBSHELL_ROOT: Optional project root. Resolved to an absolute path. You’re “inside” when `$PWD` equals or is under this root; otherwise “outside”.

## Supported shells

- zsh
- fish (3.6+)

It coexists cleanly with frameworks like oh-my-zsh and Starship; your base prompt remains untouched and continues to update normally.

## Usage

- subshell                                 # label defaults to "subshell"
- SUBSHELL_PROMPT="[dev] " subshell        # custom label via env var
- SUBSHELL_PROMPT="🔧 debug-mode " subshell

Quote the env var value if it contains spaces or emoji, e.g. SUBSHELL_PROMPT="🔧 debug-mode " subshell.

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
