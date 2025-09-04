#!/usr/bin/env python3
"""
⚠️  BEFORE UPDATING VERIFIED FILES: Read TESTING.md for proper procedure!
Never blindly copy assets/* to verified-prompts/ without analysis.

This script compares generated test files with verified baselines to detect regressions.
"""
from pathlib import Path
import sys

VERIFIED = Path('verified-prompts')
UNVERIFIED = Path('assets')

inputFiles = set(f.name for f in UNVERIFIED.glob('test-*.svg'))
outputFiles = set(f.name for f in VERIFIED.glob('test-*.svg'))

missing = inputFiles - outputFiles
extra = outputFiles - inputFiles
common = inputFiles & outputFiles
mismatch = [f for f in common if (UNVERIFIED / f).read_bytes() != (VERIFIED / f).read_bytes()]

if missing:
    print("Missing verified files:")
    for f in sorted(missing):
        print("  ", f)

if extra:
    print("Extra verified files:")
    for f in sorted(extra):
        print("  ", f)

if mismatch:
    print("Mismatched files:")
    for f in sorted(mismatch):
        print("  ", f)

if missing or extra or mismatch:
    sys.exit(1)
else:
    sys.exit(0)
