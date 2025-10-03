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
    ('zsh','starship',False),  # No blankline user for starship
    ('fish','starship',False),  # No blankline user for starship
    ('zsh','ohmyzsh',False),
    ('zsh','ohmyzsh',True),
    ('zsh','powerlevel10k',False),  # No blankline user for powerlevel10k
]

# New scenarios for testing SUBSHELL_PROMPT behavior
# Note: 'unset' tests are redundant since base tests already cover SUBSHELL_PROMPT unset
PROMPT_TEST_SCENARIOS = [
    # Test SUBSHELL_PROMPT='' (should disable prompt injection)
    ('zsh', 'default', False, 'empty'),
    ('fish', 'default', False, 'empty'),
    ('zsh', 'starship', False, 'empty'),
    ('fish', 'starship', False, 'empty'),
    ('zsh', 'ohmyzsh', False, 'empty'),
    ('zsh', 'powerlevel10k', False, 'empty'),
    # Test SUBSHELL_PROMPT='custom-name' (should use custom name)
    ('zsh', 'default', False, 'custom'),
    ('fish', 'default', False, 'custom'),
    ('zsh', 'starship', False, 'custom'),
    ('fish', 'starship', False, 'custom'),
    ('zsh', 'ohmyzsh', False, 'custom'),
    ('zsh', 'powerlevel10k', False, 'custom'),
]

THEME_USER = {
    'default': 'demo',
    'starship': 'demo-starship',
    'ohmyzsh': 'demo-oh-my-zsh',
    'powerlevel10k': 'demo-oh-my-zsh-p10k',
}

def name_for(shell: str, theme: str, blank: bool, prompt_test: str = None) -> str:
    base = f'test-{shell}-{theme}'
    if blank:
        base += '-blankline'
    if prompt_test:
        base += f'-prompt-{prompt_test}'
    return base

def ensure_bundle():
    subprocess.run([sys.executable, str(BUNDLE)], check=True)

def ensure_image():
        subprocess.run(['make', 'image'], check=True)

def capture_one(shell: str, theme: str, blank: bool, force: bool, prompt_test: str = None) -> bool:
    name = name_for(shell, theme, blank, prompt_test)
    user = THEME_USER[theme]
    if blank:
        user += '-blankline'
    test_script = [
        'subshell',
        'cd demo-subdir',
        'cd /tmp/outside',
    ]
    
    # Set up environment variables for prompt testing
    env_vars = {}
    if prompt_test == 'empty':
        env_vars['SUBSHELL_PROMPT'] = ''
    elif prompt_test == 'custom':
        env_vars['SUBSHELL_PROMPT'] = 'mycustom'
    
    import asyncio
    output = asyncio.run(capture_session(user, shell, test_script, env_vars))
    (ASSETS / (name + '.ansi')).write_bytes(output)
    return True

def iter_needed(force: bool):
    # Original scenarios
    for shell, theme, blank in SCENARIOS:
        base = name_for(shell, theme, blank)
        if force or not (ASSETS / f'{base}.ansi').exists():
            yield shell, theme, blank, None
    
    # New prompt test scenarios
    for shell, theme, blank, prompt_test in PROMPT_TEST_SCENARIOS:
        base = name_for(shell, theme, blank, prompt_test)
        if force or not (ASSETS / f'{base}.ansi').exists():
            yield shell, theme, blank, prompt_test


def main():
    force = '--force' in sys.argv
    ensure_image()
    ASSETS.mkdir(exist_ok=True)
    needed = list(iter_needed(force))
    if not needed:
        print('[done] no captures needed')
        return
    ok = True
    for shell, theme, blank, prompt_test in needed:
        base = name_for(shell, theme, blank, prompt_test)
        print(f'[capture] {base}')
        if not capture_one(shell, theme, blank, force, prompt_test):
            ok = False
    if not ok:
        sys.exit(1)
    print('[done] captured prompt states')

if __name__ == '__main__':
    main()
