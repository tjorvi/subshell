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


##############
### Shells
###

class FishShell:
    def __str__(self):
        return "fish"

    def run(self, prompt):
        subprocess.run(["fish", "--init-command", prompt])

    def detect_prompt(self):
        return run_command('fish -c "functions fish_prompt"', capture=True)[1]
    
    def prefix_prompt(self, prefix, prompt):
        # Escape quotes to keep fish init command valid
        esc_prefix = prefix.replace('\\', r'\\').replace('"', r'\"')
        return dedent(f'''
            functions -c fish_prompt _fish_prompt

            function fish_prompt
                echo -n "{esc_prefix}"
                _fish_prompt
            end
            ''')

    def activation_script(self, prefix: str) -> str:
        """Return fish init snippet that prefixes the current prompt."""
        current_prompt = self.detect_prompt()
        return self.prefix_prompt(prefix, current_prompt)


class ZShell:
    """Launch zsh with custom PS1"""
    def run(self, prompt):

        with TemporaryDirectory() as tmpdirname:
            with open(os.path.join(tmpdirname, '.zshrc'), "w") as f:
                f.write(self._custom_zshrc(prompt))

            env = os.environ.copy()
            env['ZDOTDIR'] = tmpdirname
            shell_path = env.get('SHELL', '/bin/zsh')
            subprocess.run([shell_path], env=env)

    def __str__(self):
        return "zsh"

    def _custom_zshrc(self, prompt):
        current_zdotdir = os.environ.get('ZDOTDIR')
        current_rcpath = os.path.join(current_zdotdir if current_zdotdir else os.environ['HOME'], '.zshrc')

        # Escape for double-quoted PS1 assignment
        safe_prompt = prompt.replace('\\', r'\\').replace('"', r'\"')

        return dedent(f"""
        source {current_rcpath}
        PS1="{safe_prompt}"
        {'ZDOTDIR=' + current_zdotdir if current_zdotdir else 'unset ZDOTDIR'}
        """)
        
    def detect_prompt(self):
        argv = ["zsh", "-i", "-c", "print -r -- $PROMPT"]
        m, s = pty.openpty()
        p = subprocess.Popen(argv, stdin=s, stdout=s, stderr=s, close_fds=True)
        os.close(s)
        out = b""
        while True:
            try:
                b = os.read(m, 4096)
                if not b: break
                out += b
            except OSError:
                break
        p.wait()
        os.close(m)
        # last non-empty line is usually the print result
        return next((l for l in out.decode(errors="ignore").splitlines() if l.strip()), "")

    def prefix_prompt(self, prefix, prompt):
        return f'{prefix}{prompt}'

    def activation_script(self, prefix: str) -> str:
        """Return a zsh command that sets PS1 to a prefixed current prompt."""
        current_prompt = self.detect_prompt()
        new_prompt = self.prefix_prompt(prefix, current_prompt)
        # Escape for double-quoted PS1 assignment
        safe_prompt = new_prompt.replace('\\', r'\\').replace('"', r'\"')
        return f'PS1="{safe_prompt}"'

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

def run_activate(shell_name, prefix):
    shell = get_shell_by_name(shell_name) if shell_name else detect_shell()
    if not shell:
        print("No suitable shell found (fish or zsh).", file=sys.stderr)
        return 1
    script = shell.activation_script(prefix)
    # Print without adding an extra newline; fish snippet already ends with one
    print(script, end='' if script.endswith('\n') else '')
    return 0


def run_launch(prefix):
    shell = detect_shell()
    if not shell:
        print("No suitable shell found (fish or zsh).", file=sys.stderr)
        return 1
    current_prompt = shell.detect_prompt()
    new_prompt = shell.prefix_prompt(prefix or "[subshell] ", current_prompt)
    shell.run(prompt=new_prompt)
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
        return run_activate(args.shell, args.prefix)
    
    else:
        # Default behavior: use provided -p/--prefix or fall back
        prefix = args.prefix if args.prefix is not None else "[subshell] "
        return run_launch(prefix)


if __name__ == "__main__":
    code = main()
    if code:
        sys.exit(code)
