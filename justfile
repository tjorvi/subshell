test-fish:
    env SHELL=$(which fish) src/subshell.py

test-zsh:
    env SHELL=$(which zsh) src/subshell.py

test: clean-prompts prompts-force prompts-txt prompts-decode prompts-svg
    python tools/verify-prompts.py && echo "✅ All tests passed!" || echo "❌ Tests failed!"

approve-prompts: prompts-txt prompts-decode prompts-svg
    rm verified-prompts/*.ansi || truec
    cp assets/*.ansi verified-prompts/
    cp assets/*.txt verified-prompts/
    cp assets/*.decoded verified-prompts/
    cp assets/*.svg verified-prompts/

# Generate (or update) screenshots via Python orchestrator (no Makefile required)
screenshots:
    python tools/screenshots.py run

# Force re-render all screenshots (ignore existing PNGs)
screenshots-force:
    python tools/screenshots.py run --force

# Capture ANSI prompt states (text-based replacement for PNG screenshots)
prompts:
    python tools/capture_prompts.py

clean-prompts:
    rm -f assets/*.ansi assets/*.txt

prompts-force:
    python tools/capture_prompts.py --force

# Convert .ansi files to .txt using ansi2txt.py
prompts-txt:
    #!/usr/bin/env sh
    for ansi_file in assets/*.ansi; do
        if [ -f "$ansi_file" ]; then
            txt_file="${ansi_file%.ansi}.txt"
            echo "Converting $(basename "$ansi_file") to $(basename "$txt_file")"
            cat "$ansi_file" | python tools/ansi2txt.py > "$txt_file"
        fi
    done

prompts-decode:
    #!/usr/bin/env sh
    for ansi_file in assets/*.ansi; do
        if [ -f "$ansi_file" ]; then
            decoded_file="${ansi_file%.ansi}.decoded"
            echo "Converting $(basename "$ansi_file") to $(basename "$decoded_file")"
            cat "$ansi_file" | python tools/ansi2txt.py --decode-only > "$decoded_file"
        fi
    done

prompts-svg:
    #!/usr/bin/env sh
    for ansi_file in assets/*.ansi; do
        if [ -f "$ansi_file" ]; then
            svg_file="${ansi_file%.ansi}.svg"
            echo "Converting $(basename "$ansi_file") to $(basename "$svg_file")"
            cat "$ansi_file" | python tools/ansi2txt.py --svg > "$svg_file"
        fi
    done

bundle:
    python tools/bundle.py

package version:
    cd dist && tar -czf "subshell-v{{version}}.tar.gz" bin/

release version:
    gh release create "v{{version}}" "dist/subshell-v{{version}}.tar.gz"
