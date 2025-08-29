#! /usr/bin/env python3

import os
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

def detect_shell():
    shell_path = os.environ.get('SHELL', '/bin/bash')
    shell_name = Path(shell_path).name
    
    if shell_name == "fish":
        return FishShell()
    elif shell_name == 'zsh':
        return ZShell()
    

########################
### The Subshell app
###

def main():
    shell = detect_shell()

    if not shell:
        print("No suitable shell found (fish or zsh).", file=sys.stderr)
        sys.exit(1)

    # Parse prompt from all CLI args; default to "subshell" if none
    args = sys.argv[1:]
    prefix = " ".join(args).strip() if args else "[subshell] "

    # Build the appropriate prompt/init configuration
    current_prompt = shell.detect_prompt()
    new_prompt = shell.prefix_prompt(prefix, current_prompt)

    shell.run(prompt=new_prompt)

if __name__ == "__main__":
    main()
