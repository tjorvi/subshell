# Subshell

Run a subshell with a given prompt prefix.

Usage:
 - subshell                # defaults to prefix "subshell"
 - subshell <args...>      # joins all args into the prefix

Examples:
 - subshell
 - subshell feature/XYZ
 - subshell "[dev] "
 - subshell 🔧 debug-mode

## Supported shells
- fish
- zsh

## What your prompt will look like

Below are approximate examples of how common default prompts get prefixed. Colors and theming are omitted.

- zsh (typical default):
	- Original: `tjorvi@host ~/repo % `
	- With `subshell "[dev] "`: `[dev] tjorvi@host ~/repo % `
	- With `subshell feature/XYZ`: `feature/XYZ tjorvi@host ~/repo % `
	- With `subshell` (no args): `[subshell] tjorvi@host ~/repo % `

- fish (typical default):
	- Original: `tjorvi@host ~/repo> `
	- With `subshell "[dev] "`: `[dev] tjorvi@host ~/repo> `
	- With `subshell 🔧 debug-mode`: `🔧 debug-mode tjorvi@host ~/repo> `
	- With `subshell` (no args): `[subshell] tjorvi@host ~/repo> `

Notes:
- Prefix can include spaces and emoji. Quote it when it contains spaces: `subshell "[dev env] "`.
- The prefix is added in front of your existing prompt; closing the subshell restores your original prompt.
