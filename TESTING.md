Run `just test` to generate prompt files and compare against known-good sources.

## Test Cases

The test suite includes scenarios for:

### Standard Shell/Theme Combinations
- Default shell prompts (zsh, fish) with and without blank lines
- Starship integration
- Oh-My-Zsh integration
- Powerlevel10k integration

### SUBSHELL_PROMPT Behavior Tests
- **Empty**: `SUBSHELL_PROMPT=""` → should disable prompt injection, only set env variables  
- **Custom**: `SUBSHELL_PROMPT="mycustom"` → should use custom text instead of "subshell"

Note: Default behavior (when `SUBSHELL_PROMPT` is unset) is already tested by the standard shell/theme combinations above.

These test cases ensure that the prompt injection behavior works correctly in all expected scenarios.

## CRITICAL: Do NOT blindly update verified files

The `verified-prompts/` directory contains the expected baseline outputs. When tests fail with "Mismatched files":

1. **First examine the diff** between `verified-prompts/` and `assets/` files
2. **Determine if changes are intentional** (improvements) or regressions (bugs)
3. **Only update verified files** if changes are confirmed improvements
4. **Document the reason** for updating in commit messages

**Never run `cp assets/* verified-prompts/` without understanding what changed!**

### File types for analysis:
- **`.txt` files**: Quick text comparison, easy to diff and understand changes
- **`.decoded` files**: Human-readable with escape sequences decoded, best for detailed analysis
- **`.svg` files**: Visual representation (these are what get compared by verify script)
- **`.ansi` files**: Raw terminal output with escape sequences

### Investigating test failures:
```bash
# Compare specific files to understand changes
diff -u verified-prompts/test-zsh-default.txt assets/test-zsh-default.txt

# For more detailed analysis with escape sequences
diff -u verified-prompts/test-zsh-default.decoded assets/test-zsh-default.decoded

# Only after confirming changes are intentional improvements:
cp assets/test-zsh-default.* verified-prompts/
```
