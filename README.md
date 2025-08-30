# Subshell

Run a subshell with a given prompt prefix.

Usage:
 - subshell                # defaults to prefix "[subshell] "
 - subshell -p "[dev] "    # set a custom prefix
 - subshell --prefix "🔧 debug-mode "
 - subshell activate [zsh|fish] [-p PREFIX]  # print an activation snippet for your current shell

Examples:
 - subshell
 - subshell -p feature/XYZ
 - subshell -p "[dev] "
 - subshell --prefix "🔧 debug-mode "
 - eval "$(subshell activate zsh -p \"[dev]\" )"  # prefix current zsh session

## Supported shells
- fish
- zsh

## What your prompt will look like

Below are approximate examples of how common default prompts get prefixed. Colors and theming are omitted.

- zsh (typical default):
	- Original: `tjorvi@host ~/repo % `
	- With `subshell -p "[dev] "`: `[dev] tjorvi@host ~/repo % `
	- With `subshell -p feature/XYZ`: `feature/XYZ tjorvi@host ~/repo % `
	- With `subshell` (no args): `[subshell] tjorvi@host ~/repo % `

- fish (typical default):
	- Original: `tjorvi@host ~/repo> `
	- With `subshell -p "[dev] "`: `[dev] tjorvi@host ~/repo> `
	- With `subshell --prefix "🔧 debug-mode "`: `🔧 debug-mode tjorvi@host ~/repo> `
	- With `subshell` (no args): `[subshell] tjorvi@host ~/repo> `

Notes:
- Prefix can include spaces and emoji. Quote it when it contains spaces: `subshell -p "[dev env] "`.
- The prefix is added in front of your existing prompt; closing the subshell restores your original prompt.

## Activate mode (prefix your current shell)

Use `subshell activate` when you want to prefix the prompt of your current shell session instead of launching a nested subshell. It prints a small snippet to stdout; apply it with `eval` or `source` so it affects your current shell.

General usage:
- Detect from $SHELL: `subshell activate -p "[dev] "`
 - Specify shell: `subshell activate zsh -p "[dev] "` or `subshell activate fish -p "[dev] "`

zsh examples:
- eval: `eval "$(subshell activate zsh -p "[dev] ")"`
- source via process substitution: `source <(subshell activate zsh -p "[dev] ")`

fish examples:
- eval: `eval (subshell activate fish -p "[dev] ")`
- source via psub: `source (subshell activate fish -p "[dev] " | psub)`

Notes for activate:
- If you omit the shell name, `subshell activate` detects it from `$SHELL`.
- Quote prefixes that contain spaces or emoji, e.g. `-p "🔧 debug-mode "`.
- To undo: in zsh, `source ~/.zshrc` restores your prompt; in fish, start a new shell or run `functions -e fish_prompt; functions -c _fish_prompt fish_prompt`.
