test-fish:
    env SHELL=$(which fish) src/subshell.py

test-zsh:
    env SHELL=$(which zsh) src/subshell.py

test: test-fish test-zsh

bundle:
    python bundle.py
