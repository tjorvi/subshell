#! /usr/bin/env python3

import os
import argparse
import pty
import sys
from tempfile import TemporaryDirectory
from textwrap import dedent
import subprocess
from pathlib import Path


########################
### System helpers
###

def run_command(cmd, shell=True, capture=False):
    """Run a command and return success status (and stdout if capture=True)."""
    try:
        if capture:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
            return result.returncode == 0, result.stdout
        else:
            result = subprocess.run(cmd, shell=shell)
            return result.returncode == 0
    except Exception:
        return (False, "") if capture else False


def load_script(name):
    scripts = globals().get('_bundled_scripts_')
    if scripts:
        return scripts[name]
    else:
        return (Path(__file__).parent / "scripts" / name).read_text()

########################
### Secrets management
###

def _read_subshell_env_entries(root_path: Path):
    """Read environment entries from a .subshell file in the given root.

    Returns a list of raw values following `environment=` preserving order.
    Comments and blank lines are ignored. Whitespace is trimmed.
    """
    entries = []
    subshell_file = root_path / ".subshell"
    if not subshell_file.is_file():
        return entries
    try:
        for raw in subshell_file.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, val = line.split('=', 1)
            if key.strip() == 'environment':
                v = val.strip()
                if v:
                    entries.append(v)
    except Exception:
        # On parse/read errors, be conservative and return no names.
        return []
    return entries


def _parse_dotenv_file(path: Path):
    """Parse a minimal dotenv file into a dict.

    Supports simple KEY=VALUE lines. Ignores blank lines and comments (# ...).
    Strips surrounding single or double quotes from VALUE if present.
    Does not perform variable expansion or export directives.
    """
    env = {}
    try:
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            # Allow optional leading 'export '
            if line.lower().startswith('export '):
                line = line[7:].lstrip()
            if '=' not in line:
                continue
            key, val = line.split('=', 1)
            key = key.strip()
            # Don't accept empty keys
            if not key:
                continue
            val = val.strip()
            # Strip one layer of matching quotes
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            env[key] = val
    except Exception:
        # On parse errors, treat as empty to avoid crashing the launcher
        return {}
    return env


def _resolve_config_dir(base_env: dict) -> Path:
    xdg = base_env.get('XDG_CONFIG_HOME')
    if xdg:
        return Path(os.path.expanduser(xdg)).expanduser() / 'subshell'
    return Path(os.path.expanduser('~/.config')) / 'subshell'


def _classify_env_value(value: str):
    """Classify an environment value as ('config', name) or ('file', path_str).

    Supports optional prefixes: config:NAME and file:PATH (case-insensitive).
    Without prefix: if it contains a '/', or starts with ./, ../, ~/, or /,
    treat as file; otherwise treat as config name.
    """
    v = value.strip()
    lower = v.lower()
    if lower.startswith('config:'):
        return 'config', v[len('config:'):].strip()
    if lower.startswith('file:'):
        return 'file', v[len('file:'):].strip()

    # Heuristic: path-like => file
    if '/' in v or lower.startswith('./') or lower.startswith('../') or lower.startswith('~/') or v.startswith('/'):
        return 'file', v
    return 'config', v


def _load_secrets_from_root(env: dict):
    """Discover and load secrets based on SUBSHELL_ROOT and .subshell file.

    Returns (updates_dict, errors_list). updates_dict are env vars to merge
    into the launched shell environment. errors_list contains human-readable
    error strings for any missing secret files.
    """
    updates = {}
    errors = []

    root_val = env.get('SUBSHELL_ROOT')
    if not root_val:
        # Fallback: if .subshell exists in current working directory, use PWD
        pwd = Path(env.get('PWD') or os.getcwd())
        if (pwd / '.subshell').is_file():
            root_val = str(pwd)
            # Also propagate this decision to the child environment by updating env
            env['SUBSHELL_ROOT'] = root_val
        else:
            return updates, errors
    # Resolve to absolute path
    root_path = Path(os.path.expanduser(root_val)).resolve()
    entries = _read_subshell_env_entries(root_path)
    if not entries:
        return updates, errors

    config_dir = _resolve_config_dir(env)
    for raw in entries:
        kind, val = _classify_env_value(raw)
        if kind == 'config':
            dotenv_path = config_dir / val
        else:
            # file: resolve relative to root_path, expanduser for ~
            p = val
            # Expand ~ first
            p = os.path.expanduser(p)
            dotenv_path = Path(p)
            if not dotenv_path.is_absolute():
                dotenv_path = (root_path / dotenv_path).resolve()

        if not Path(dotenv_path).is_file():
            errors.append(f"Missing secrets file: {dotenv_path}")
            continue

        data = _parse_dotenv_file(Path(dotenv_path))
        # Later files override earlier ones on key collisions
        updates.update(data)

    return updates, errors

##############
### Shells
###

class FishShell:
    def __str__(self):
        return "fish"

    def run(self, env=None):
        subprocess.run(["fish", "--init-command", f"{__file__} activate fish | source"], env=env)


class ZShell:
    """Launch zsh with custom PS1"""
    def run(self, env=None):
        with TemporaryDirectory() as tmpdirname:
            with open(os.path.join(tmpdirname, '.zshrc'), "w") as f:
                f.write(self._custom_zshrc())

            env_to_use = (env or os.environ.copy()).copy()
            env_to_use['ZDOTDIR'] = tmpdirname
            shell_path = env_to_use.get('SHELL', '/bin/zsh')
            subprocess.run([shell_path], env=env_to_use)

    def __str__(self):
        return "zsh"

    def _custom_zshrc(self):
        current_zdotdir = os.environ.get('ZDOTDIR')
        current_rcpath = os.path.join(current_zdotdir if current_zdotdir else os.environ['HOME'], '.zshrc')

        load_prevrc = f'source {current_rcpath}' if Path(current_rcpath).is_file() else '# No previous .zshrc to source'

        return dedent(f"""
        {load_prevrc}
        eval "$({__file__} activate zsh)"
        {'ZDOTDIR=' + current_zdotdir if current_zdotdir else 'unset ZDOTDIR'}
        """)
        
def detect_shell():
    shell_path = os.environ.get('SHELL', '/bin/bash')
    shell_name = Path(shell_path).name
    
    if shell_name == "fish":
        return FishShell()
    elif shell_name == 'zsh':
        return ZShell()
    
def get_shell_by_name(name: str):
    if not name:
        return None
    name = name.lower()
    if name == 'fish':
        return FishShell()
    if name == 'zsh':
        return ZShell()
    return None


########################
### The Subshell app
###

def run_activate(shell_name):
    shell = get_shell_by_name(shell_name) if shell_name else detect_shell()
    if not shell:
        print("No suitable shell found (fish or zsh).", file=sys.stderr)
        return 1
    script = load_script(f'activate.{shell}')
    # Print without adding an extra newline; fish snippet already ends with one
    print(script, end='' if script.endswith('\n') else '')
    return 0


def run_launch():
    shell = detect_shell()
    if not shell:
        print("No suitable shell found (fish or zsh).", file=sys.stderr)
        return 1
    # Prepare environment with secrets (if any)
    base_env = os.environ.copy()
    updates, errors = _load_secrets_from_root(base_env)
    if errors:
        # Print prominently before launching the subshell. Use red color if supported.
        try:
            red = "\033[38;5;196m"
            reset = "\033[0m"
        except Exception:
            red = reset = ""
        banner = (
            "\n‼️  " + red + "subshell: one or more secret files were not found" + reset + " ‼️\n"
            + "\n".join(f" - {e}" for e in errors) + "\n"
        )
        print(banner, file=sys.stderr)

    # Merge and launch
    base_env.update(updates)
    shell.run(env=base_env)
    return 0


### argument parsing

def commandline_parser():
    parser = argparse.ArgumentParser(prog='subshell', add_help=True)
    # Global options (apply to default launch path as well)
    subparsers = parser.add_subparsers(dest='command')

    # subshell activate [zsh|fish] [--prefix ...]
    p_act = subparsers.add_parser('activate', help='Print activation snippet for the given shell')
    p_act.add_argument('shell', nargs='?', choices=['zsh', 'fish'], help='Shell to activate for (default: detect from $SHELL)')
    return parser


### entry point

def main(argv=None):
    args = commandline_parser().parse_args(argv)

    if args.command == 'activate':
        return run_activate(args.shell)
    
    else:
        return run_launch()


if __name__ == "__main__":
    code = main()
    if code:
        sys.exit(code)
