test-fish:
    env SHELL=$(which fish) src/subshell.py

test-zsh:
    env SHELL=$(which zsh) src/subshell.py

test: test-fish test-zsh

bundle:
    python bundle.py

package version:
    cd dist && tar -czf "subshell-v{{version}}.tar.gz" bin/

release version:
    gh release create "v{{version}}" "dist/subshell-v{{version}}.tar.gz"
