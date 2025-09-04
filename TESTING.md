Run `just test` to generate prompt files and compare against known-good sources.

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
