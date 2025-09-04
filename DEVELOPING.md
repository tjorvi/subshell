# Developing

This project uses `just` recipes plus `uv` for dependency management and test execution.

## Environment

Install `just` and `uv` if you don't have them:

```
brew install just
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install dev dependencies (first run only):

```
uv sync --all-extras --dev
```

## Running the App Quickly

```
just test-fish   # Launch subshell using fish
just test-zsh    # Launch subshell using zsh
```

## Test Suite

```
just test-all          # Run all tests (quiet)
just test-screenshots  # Run only screenshot regression tests
```

### Updating Screenshot Baselines

The prior hash approval layer was removed. Baselines are managed solely by `pytest-regressions`.

To force-regenerate all screenshot baselines after an intentional visual change:

```
uv run pytest --force-regen -k test_prompt_screenshots -q
```

Then commit the updated files under `tests/test_screenshots/`.

### Adding a New Screenshot

1. Add the new PNG's expected filename to `EXPECTED_IMAGES` in `tests/test_screenshots.py`.
2. Run `just test-screenshots` once; a baseline is created automatically.
3. Commit the new baseline file.

### Rebuilding Bundle (Legacy)

A self-contained script can be regenerated (legacy flow):

```
just bundle-rebuild
```

> Note: This may be replaced with a standard console entry point in future refactors.

## Notes

- Use `--force-regen` cautiously—review diffs in your git staging area before committing.
- If Docker-based screenshot generation is slow, consider pruning images or using `make screenshots` separately before running tests.
