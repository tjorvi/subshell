# Subshell Prompt Prefix for fish
# - Core behavior per SPEC.md
# - Keeps user's existing prompt by wrapping it
# - Idempotent (does not double-wrap on reload)

# --- defaults
if not set -q SUBSHELL_PROMPT
    set -g SUBSHELL_PROMPT subshell
end

# --- helpers
function __subshell_abspath --description 'Resolve to absolute path (Fish 3.6+: path resolve)'
    if test -z "$argv[1]"
        return 1
    end
    path resolve -- $argv[1]
end

# Normalize SUBSHELL_ROOT to absolute, if set
if set -q SUBSHELL_ROOT
    set -g SUBSHELL_ROOT (__subshell_abspath "$SUBSHELL_ROOT")
end

function __subshell_update_state --description 'Compute SUBSHELL_OUTSIDE from $PWD and $SUBSHELL_ROOT'
    if not set -q SUBSHELL_ROOT; or test -z "$SUBSHELL_ROOT"
        set -g SUBSHELL_OUTSIDE 0
        return
    end
    set -l here $PWD
    set -l root (string replace -r '/$' '' -- "$SUBSHELL_ROOT")

    if test "$here" = "$root"
        set -g SUBSHELL_OUTSIDE 0
        return
    end

    set -l rlen (string length -- "$root")
    set -l prefix (string sub -s 1 -l $rlen -- "$here")
    if test "$prefix" = "$root"
        set -l next (string sub -s (math $rlen + 1) -l 1 -- "$here")
        if test -z "$next"; or test "$next" = '/'
            set -g SUBSHELL_OUTSIDE 0
            return
        end
    end
    set -g SUBSHELL_OUTSIDE 1
end

function __subshell_render_pre_prompt --description 'Render the prefix line above the base prompt'
    if set -q SUBSHELL_OUTSIDE; and test $SUBSHELL_OUTSIDE -eq 1
        set -l color (set_color brred)
        set -l normal (set_color normal)
        echo "‼️  "$color$SUBSHELL_PROMPT" is outside project root ("$SUBSHELL_ROOT")"$normal" ‼️"
    else
        set -l color (set_color yellow)
        set -l normal (set_color normal)
        echo "📂 "$color$SUBSHELL_PROMPT$normal
    end
end

# Recompute state on directory changes
function __subshell_chpwd --on-variable PWD --description 'Update state on directory change'
    __subshell_update_state
end

# --- prompt wrapping: preserve user's base prompt
if not functions -q __subshell_original_fish_prompt
    if functions -q fish_prompt
        functions -c fish_prompt __subshell_original_fish_prompt
    else
        function __subshell_original_fish_prompt --description 'Fallback base prompt'
            printf '%s > ' (prompt_pwd)
        end
    end
end

function fish_prompt --description 'Wrapped prompt that injects subshell prefix'
    if not set -q SUBSHELL_OUTSIDE
        __subshell_update_state
    end
    __subshell_render_pre_prompt
    __subshell_original_fish_prompt
end
