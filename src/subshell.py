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

##############
### Shells
###

class FishShell:
    def __str__(self):
        return "fish"

    def run(self):
        subprocess.run(["fish", "--init-command", f"{__file__} activate fish | source"])


class ZShell:
    """Launch zsh with custom PS1"""
    def run(self):
        with TemporaryDirectory() as tmpdirname:
            with open(os.path.join(tmpdirname, '.zshrc'), "w") as f:
                f.write(self._custom_zshrc())

            env = os.environ.copy()
            env['ZDOTDIR'] = tmpdirname
            shell_path = env.get('SHELL', '/bin/zsh')
            subprocess.run([shell_path], env=env)

    def __str__(self):
        return "zsh"

    def _custom_zshrc(self):
        current_zdotdir = os.environ.get('ZDOTDIR')
        current_rcpath = os.path.join(current_zdotdir if current_zdotdir else os.environ['HOME'], '.zshrc')

        return dedent(f"""
        source {current_rcpath}
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
    shell.run()
    return 0


### argument parsing

def commandline_parser():
    parser = argparse.ArgumentParser(prog='subshell', add_help=True)
    # Global options (apply to default launch path as well)
    parser.add_argument('-p', '--prefix', dest='prefix', default=None, help='Prefix to add to the prompt')
    subparsers = parser.add_subparsers(dest='command')

    # subshell activate [zsh|fish] [--prefix ...]
    p_act = subparsers.add_parser('activate', help='Print activation snippet for the given shell')
    p_act.add_argument('shell', nargs='?', choices=['zsh', 'fish'], help='Shell to activate for (default: detect from $SHELL)')
    p_act.add_argument('-p', '--prefix', default='[subshell] ', help='Prefix to add to the prompt')
    return parser


### entry point

def main(argv=None):
    args = commandline_parser().parse_args(argv)

    if args.command == 'activate':
        return run_activate(args.shell)
    
    else:
        # Default behavior: use provided -p/--prefix or fall back
        return run_launch()


if __name__ == "__main__":
    code = main()
    if code:
        sys.exit(code)
