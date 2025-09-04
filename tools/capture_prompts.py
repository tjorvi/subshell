#!/usr/bin/env python3

from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass

from prompter import capture_session

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'assets'
DEMO = ROOT / 'demo'
DOCKERFILE = DEMO / 'Dockerfile.demo'
IMAGE = 'subshell-demo-tools'
BUNDLE = ROOT / 'bundle.py'

# Reuse matrix matching screenshots.py for consistency
SCENARIOS = [
    ('zsh','default',False),
    ('zsh','default',True),
    ('fish','default',False),
    ('fish','default',True),
    ('zsh','starship',False),
    ('fish','starship',False),
    ('zsh','ohmyzsh',False),
    ('zsh','ohmyzsh',True),
    ('zsh','powerlevel10k',False),
]

THEME_USER = {
    'default': 'demo',
    'starship': 'demo-starship',
    'ohmyzsh': 'demo-oh-my-zsh',
    'powerlevel10k': 'demo-oh-my-zsh-p10k',
}

def name_for(shell: str, theme: str, blank: bool) -> str:
    base = f'test-{shell}-{theme}'
    if blank:
        base += '-blankline'
    return base

def ensure_bundle():
    subprocess.run([sys.executable, str(BUNDLE)], check=True)

def ensure_image():
        subprocess.run(['make', 'image'], check=True)

def capture_one(shell: str, theme: str, blank: bool, force: bool) -> bool:
    name = name_for(shell, theme, blank)
    user = THEME_USER[theme]
    if blank:
        user += '-blankline'
    test_script = [
        'subshell',
        'cd demo-subdir',
        'cd /tmp/outside',
    ]
    import asyncio
    output = asyncio.run(capture_session(user, shell, test_script))
    (ASSETS / (name + '.ansi')).write_bytes(output)
    return True

def iter_needed(force: bool):
    for shell, theme, blank in SCENARIOS:
        base = name_for(shell, theme, blank)
        if force or not (ASSETS / f'{base}.ansi').exists():
            yield shell, theme, blank


def main():
    force = '--force' in sys.argv
    ensure_image()
    ASSETS.mkdir(exist_ok=True)
    needed = list(iter_needed(force))
    if not needed:
        print('[done] no captures needed')
        return
    ok = True
    for shell, theme, blank in needed:
        base = name_for(shell, theme, blank)
        print(f'[capture] {base}')
        if not capture_one(shell, theme, blank, force):
            ok = False
    if not ok:
        sys.exit(1)
    print('[done] captured prompt states')

if __name__ == '__main__':
    main()
