######################################################################
# subshell prompt activation (fish shell)
# Keep this file simple: clear sections, minimal globals, idempotent load.
######################################################################

# Re-entry guard (idempotent sourcing)
if set -q __SUBSHELL_LOADED
    return 0
end
set -g __SUBSHELL_LOADED 1

# Suppress default fish greeting (avoids interfering with prompt capture / screenshots)
set -g fish_greeting ''

### cleanup for reload-style sourcing (remove old hooks and our functions if any)
# Only remove functions that are ours, preserve any existing fish_prompt that isn't ours
if functions -q fish_prompt
    set -l prompt_body (functions fish_prompt | string collect)
    if string match -q "*subshell*" "$prompt_body"
        # This is our wrapped prompt, remove it
        functions -e fish_prompt 2>/dev/null
    end
    # Otherwise preserve the existing fish_prompt (could be starship or user's prompt)
end
functions -e __subshell_chpwd 2>/dev/null
# Note: preserve __subshell_original_fish_prompt to avoid losing the user's original prompt

### defaults
# Set the default to "subshell" only if SUBSHELL_PROMPT is unset (allow empty string)
if not set -q SUBSHELL_PROMPT
    set -gx SUBSHELL_PROMPT subshell
else
    # ensure exported for starship / custom commands  
    set -gx SUBSHELL_PROMPT $SUBSHELL_PROMPT
end

# Normalize SUBSHELL_ROOT to absolute, if set
if set -q SUBSHELL_ROOT
    set -g SUBSHELL_ROOT (path resolve -- "$SUBSHELL_ROOT")
end

################################################################################
# SECTION 1: BUSINESS LOGIC
# Core state management and rendering - shell-agnostic functionality
################################################################################

function subshell_update_state --description 'Core business logic: determine inside/outside status'
    # Algorithm: PWD is "inside" if it equals SUBSHELL_ROOT or is a subdirectory
    # Returns: sets SUBSHELL_OUTSIDE to 0 (inside) or 1 (outside)
    
    if not set -q SUBSHELL_ROOT; or test -z "$SUBSHELL_ROOT"
        set -gx SUBSHELL_OUTSIDE 0  # No root defined = always inside
        return
    end
    
    # Normalize paths - get absolute paths and strip trailing slashes  
    set -l current_path (path resolve -- "$PWD")
    set -l root_path (string replace -r '/$' '' -- "$SUBSHELL_ROOT")
    
    # Check if current path is inside root path
    if test "$current_path" = "$root_path"
        set -gx SUBSHELL_OUTSIDE 0  # Exact match = inside
    else if string match -q "$root_path/*" "$current_path"
        set -gx SUBSHELL_OUTSIDE 0  # Subdirectory = inside
    else
        set -gx SUBSHELL_OUTSIDE 1  # Outside root = outside
    end
end

function subshell_render_pre_prompt --description 'Render the prefix line above the base prompt'
    if set -q SUBSHELL_OUTSIDE; and test $SUBSHELL_OUTSIDE -eq 1
        set -l color (set_color brred)
        set -l normal (set_color normal)
        printf "‼️  %s%s is outside project root (%s)%s ‼️" "$color" "$SUBSHELL_PROMPT" "$SUBSHELL_ROOT" "$normal"
    else
        set -l color (set_color yellow)
        set -l normal (set_color normal)
        printf "📂 %s%s%s" "$color" "$SUBSHELL_PROMPT" "$normal"
    end
end

################################################################################
# SECTION 2: PROMPT LIBRARY DETECTION
# Pure detection logic - returns boolean, minimal side effects  
################################################################################

function subshell_detect_starship --description 'Detect starship presence'
    # Primary signal: well-known env var exported by starship init script
    if set -q STARSHIP_SESSION_KEY; and test -n "$STARSHIP_SESSION_KEY"
        return 0
    end
    
    return 1
end

################################################################################
# SECTION 3: PROMPT INJECTION IMPLEMENTATION
# Library-specific integration and rendering
################################################################################

# --- Starship Implementation ---

function _subshell_get_bundled_starship_config --description 'Get the bundled starship config content'
    # Hardcoded starship config - single source of truth
    printf '[custom.subshell_inside]\n'
    printf 'when = '\''test "${SUBSHELL_OUTSIDE:-0}" -eq 0 && test -n "${SUBSHELL_PROMPT:-}"'\''\n'
    printf 'command = '\''printf %%s "${SUBSHELL_PROMPT:-subshell}"'\''\n'
    printf 'symbol = '\''📂'\''\n'
    printf 'style = '\''blue'\''\n'
    printf 'format = '\''[$symbol$output]($style)'\''\n'
    printf 'shell = '\''sh'\''\n'
    printf '\n[custom.subshell_outside]\n'
    printf 'when = '\''test "${SUBSHELL_OUTSIDE:-0}" -eq 1 && test -n "${SUBSHELL_PROMPT:-}"'\''\n'
    printf 'command = '\''printf "%%s (outside %%s)" "${SUBSHELL_PROMPT:-subshell}" "${SUBSHELL_ROOT}"'\''\n'
    printf 'symbol = '\''‼️ '\''\n'
    printf 'style = '\''red bold'\''\n'
    printf 'format = '\''[$symbol$output]($style)'\''\n'
    printf 'shell = '\''sh'\''\n'
end

function _subshell_create_starship_config --description 'Generate ephemeral starship config with subshell modules'
    # Skip if user already points STARSHIP_CONFIG to our generated file
    if set -q STARSHIP_CONFIG; and string match -q "*subshell-starship-*" "$STARSHIP_CONFIG"; and test -f "$STARSHIP_CONFIG"
        return 0
    end
    
    # Find user's existing config
    set -l orig_config ''
    if set -q STARSHIP_CONFIG; and test -r "$STARSHIP_CONFIG"
        set orig_config $STARSHIP_CONFIG
    else if set -q XDG_CONFIG_HOME; and test -r "$XDG_CONFIG_HOME/starship.toml"
        set orig_config "$XDG_CONFIG_HOME/starship.toml"
    else if test -r "$HOME/.config/starship.toml"
        set orig_config "$HOME/.config/starship.toml"
    end
    
    # Create temporary config by combining user config + bundled starship config
    set -l tmpdir (string trim -- (printf %s "$TMPDIR"))
    if test -z "$tmpdir"; or not test -d "$tmpdir"; set tmpdir /tmp; end
    set -l temp_config "$tmpdir/subshell-starship-"(id -u)"-$fish_pid.toml"
    
    # Start with user's existing config (if any)
    if test -n "$orig_config"
        cat "$orig_config" > $temp_config
    else
        printf '' > $temp_config
    end
    
    # Append our bundled starship modules
    printf '\n# --- subshell integration (auto-generated) ---\n' >> $temp_config
    _subshell_get_bundled_starship_config >> $temp_config
    
    set -gx STARSHIP_CONFIG $temp_config
    return 0
end

function subshell_init_starship --description 'Initialize starship integration'
    # Create ephemeral config
    _subshell_create_starship_config
end

# --- Generic Implementation ---

function subshell_init_generic --description 'Initialize generic prompt wrapping'
    # Save original prompt function
    if not functions -q __subshell_original_fish_prompt
        if functions -q fish_prompt
            functions -c fish_prompt __subshell_original_fish_prompt
        else
            function __subshell_original_fish_prompt --description 'Fallback base prompt'
                # Match fish's default prompt format: user@host path>
                printf '%s@%s %s> ' (whoami) (hostname -s) (prompt_pwd)
            end
        end
    end
    
    # Create wrapped prompt function  
    function fish_prompt --description 'Wrapped prompt that injects subshell prefix'
        # Update state if needed
        if not set -q SUBSHELL_OUTSIDE
            subshell_update_state
        end
        
        # Skip prefix if no SUBSHELL_PROMPT set
        if test -z "$SUBSHELL_PROMPT"
            __subshell_original_fish_prompt
            return
        end

        # Render prefix above original prompt
        set -l base (begin; __subshell_original_fish_prompt; end | string collect)
        
        # Check if the captured prompt starts with a newline and handle accordingly
        if string match -q -r '^\n' "$base"
            # Preserve the leading blank line: print it first, then subshell prompt, then cleaned base
            set -l clean_base (string replace -r '^[\n]' '' -- "$base")
            printf '\n'
            subshell_render_pre_prompt
            printf '\n%s' "$clean_base"
        else
            # Regular case: concatenate with newline after prefix
            subshell_render_pre_prompt
            printf '\n%s' "$base"
        end
    end
end

################################################################################
# INITIALIZATION AND HOOKS
################################################################################

# Hook to update state on directory changes
function __subshell_chpwd --on-variable PWD --description 'Update state on directory change'
    subshell_update_state
end

# Run detections and initialize appropriate implementation
if subshell_detect_starship
    subshell_init_starship
    # For starship: do NOT install prompt wrapper - let starship handle everything via custom modules
else
    subshell_init_generic
end