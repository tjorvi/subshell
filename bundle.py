from pathlib import Path

mainScript = (Path('.') / 'src' / 'subshell.py').read_text()

scripts = {
    path.name: path.read_text()
    for path in (Path('.') / 'src' / 'scripts').glob('*')
}

bundle = f'_bundled_scripts_ = {str(scripts)}'

Path('dist').mkdir(exist_ok=True)
output = (Path('dist') / 'subshell')


output .write_text('\n\n\n\n'.join(['#! /usr/bin/env python3', bundle, mainScript]))
output.chmod(0o755)
