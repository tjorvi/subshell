# Subshell Prompt Prefix — Core Requirements

1. **Project root**
   - Optional `SUBSHELL_ROOT` env var, resolved to absolute path.
   - *Inside* if `$PWD` equals or is under root, *Outside* otherwise.

2. **Customizable label**
   - `SUBSHELL_PROMPT` env var, defaults to `subshell`.

3. **Visual styling**
   - Always show a prefix line above the base prompt.
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
   - Implement separately for zsh, fish, nushell.
   - Must coexist cleanly with frameworks like oh-my-zsh and Starship.
