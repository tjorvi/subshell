# Subshell Prompt Prefix — Core Requirements

1. **Project root**
   - Optional `SUBSHELL_ROOT` env var, resolved to absolute path.
   - If `SUBSHELL_ROOT` is unset and a `.subshell` file exists in `$PWD`, then `$PWD` is treated as the project root for this session and `SUBSHELL_ROOT` is set accordingly in the launched subshell.
   - *Inside* if `$PWD` equals or is under root, *Outside* otherwise.

2. **Customizable label**
   - `SUBSHELL_PROMPT` env var
   - defaults to `subshell` if unset.
   - if empty string then show no prompt, just expose shell variable to
     expose inside vs outside logic. This is intended for powerusers
     who want to incorporate this information into their own prompts.

3. **Visual styling**
   - Always show a prefix line above the base prompt.
   - If the users prompt starts with an empty line then place the
     prompt prefix _below_ the empty line.
   - Must be visually distinct from command output.
   - When inside root: 📂 %F{33}${msg}%f
   - When outside: ‼️  %F{196}${msg} is outside project root (${root})%f ‼️
     - Note, the double-space at the beginning and single space at the end are
       intentional. it looks more balanced this way. maybe because of the
       parenthesis at the end?
  
4. **Prompt integrity**
   - Preserve base prompt, don’t freeze it.
   - Idempotent injection (no stacking).
   - Rebuild on each render.

5. **Portability**
   - Core spec portable across shells.
   - Implement separately for zsh, fish (3.6+), nushell.
   - Must coexist cleanly with frameworks like oh-my-zsh and Starship.
   - Must work out-of-the-box with zero configuration on the users machine or profile
   

6. **Secrets management**
    - Secrets can be provided from either the user config directory or local files.
    - Config directory: use XDG config if available, else fallback to home config.
       - Base dir = `${XDG_CONFIG_HOME:-~/.config}/subshell`
    - In `$SUBSHELL_ROOT/.subshell`, lines of the form `environment=VALUE` are processed in order.
       - Bare name (no slash) → load `${CONFIG_DIR}/{name}`
       - Path-like value (contains `/` or starts with `./`, `../`, `~/`, or `/`) → treat as file path
          - Relative paths are resolved against `SUBSHELL_ROOT`.
          - `~/` expands to `$HOME`.
       - Optional explicit prefixes (case-insensitive):
          - `config:NAME` → force lookup in `${CONFIG_DIR}/{NAME}`
          - `file:PATH` → force file path semantics
    - Multiple `environment=` lines are allowed; later files override earlier variables on key conflicts.
    - If any referenced file does not exist (whether config or local), it is an error. The subshell may still be started, but it should print that error prominently on start.

