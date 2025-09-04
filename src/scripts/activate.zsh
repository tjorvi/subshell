######################################################################
# subshell prompt activation (single-file, lightly modular)
# Keep this file simple: clear sections, minimal globals, idempotent load.
######################################################################

# Re-entry guard (idempotent sourcing)
if [[ -n ${SUBSHELL__LOADED+x} ]]; then
  return
fi
typeset -g SUBSHELL__LOADED=1
[[ -n ${SUBSHELL_DEBUG:-} ]] && print -u2 -- "[subshell][debug] activate.zsh sourced (pid=$$)"

### cleanup for reload-style sourcing (remove old hooks if any)
autoload -Uz add-zsh-hook
add-zsh-hook -D chpwd subshell_chpwd 2>/dev/null
add-zsh-hook -D precmd subshell_precmd 2>/dev/null
unset SUBSHELL_PREV_PREFIX SUBSHELL_OUTSIDE

### defaults
# Set the default to "subshell" only if SUBSHELL_PROMPT is unset (allow empty string)
if (( ${+SUBSHELL_PROMPT} == 0 )); then SUBSHELL_PROMPT=subshell; fi
# Export key vars so starship custom modules (run in separate processes) can read them.
typeset -gx SUBSHELL_PROMPT

# Normalize the SUBSHELL_ROOT, if it's set
[[ -n ${SUBSHELL_ROOT:-} ]] && SUBSHELL_ROOT="${SUBSHELL_ROOT:A}"

################################################################################
# SECTION 1: BUSINESS LOGIC
# Core state management and rendering - shell-agnostic functionality
################################################################################

subshell_update_state() {
  # Algorithm: PWD is "inside" if it equals SUBSHELL_ROOT or is a subdirectory
  # Returns: sets SUBSHELL_OUTSIDE to 0 (inside) or 1 (outside)
  
  if [[ -z ${SUBSHELL_ROOT:-} ]]; then
    SUBSHELL_OUTSIDE=0  # No root defined = always inside
    typeset -gx SUBSHELL_OUTSIDE
    return
  fi
  
  # Normalize paths to absolute, no trailing slash
  local current_path="${PWD:A}"
  local root_path="${SUBSHELL_ROOT:A}"
  root_path="${root_path%/}"  # Remove trailing slash
  
  # Check if current path is inside root path
  if [[ $current_path == $root_path || $current_path == $root_path/* ]]; then
    SUBSHELL_OUTSIDE=0  # Inside root
  else
    SUBSHELL_OUTSIDE=1  # Outside root
  fi
  typeset -gx SUBSHELL_OUTSIDE
}

subshell_render_pre_prompt() {
  if (( SUBSHELL_OUTSIDE )); then
    print -r -- "‼️  %F{196}${SUBSHELL_PROMPT} is outside project root (${SUBSHELL_ROOT})%f ‼️"
  else
    print -r -- "📂 %F{33}${SUBSHELL_PROMPT}%f"
  fi
}

################################################################################
# SECTION 2: PROMPT LIBRARY DETECTION  
# Pure detection logic - returns boolean, minimal side effects
################################################################################

subshell_detect_p10k() {
  typeset -f p10k_segment >/dev/null || [[ -n ${POWERLEVEL9K_LEFT_PROMPT_ELEMENTS+x} ]]
}

subshell_detect_starship() {
  # Force flag for manual testing
  if [[ -n ${SUBSHELL_FORCE_STARSHIP:-} ]]; then
    [[ -n ${SUBSHELL_DEBUG:-} ]] && print -u2 -- "[subshell][debug] starship forced via SUBSHELL_FORCE_STARSHIP"
    return 0
  fi

  # Primary detection: function present OR well-known env var exported by init script
  typeset -f starship_precmd >/dev/null || [[ -n ${STARSHIP_SESSION_KEY:-} ]]
}

################################################################################
# SECTION 3: PROMPT INJECTION IMPLEMENTATION
# Library-specific integration and rendering
################################################################################

# --- PowerLevel10k Implementation ---

subshell_init_p10k() {
  # Define custom segment only when p10k present (idempotent)
  if ! typeset -f prompt_subshell >/dev/null; then
    prompt_subshell() {
      [[ -n ${SUBSHELL_OUTSIDE-} ]] || subshell_update_state
      [[ -n ${SUBSHELL_PROMPT} ]] || return
      if (( SUBSHELL_OUTSIDE )); then
        p10k segment -f 196 -i "‼️" -t "${SUBSHELL_PROMPT} outside ${SUBSHELL_ROOT}" 2>/dev/null || \
          print -r -- "‼️ ${SUBSHELL_PROMPT} outside ${SUBSHELL_ROOT}"
      else
        p10k segment -f 33 -i "📂" -t "${SUBSHELL_PROMPT}" 2>/dev/null || \
          print -r -- "📂 ${SUBSHELL_PROMPT}"
      fi
    }
  fi

  # Auto-inject segment into P10K prompt elements if not already present
  if [[ ${+POWERLEVEL9K_LEFT_PROMPT_ELEMENTS} -eq 1 ]]; then
    if (( ${(M)#POWERLEVEL9K_LEFT_PROMPT_ELEMENTS:#subshell} == 0 )); then
      # Find first newline element to inject before it, otherwise append
      local -a _elements=("${POWERLEVEL9K_LEFT_PROMPT_ELEMENTS[@]}")
      local newline_pos=-1 i
      for (( i=1; i<=${#_elements}; i++ )); do
        if [[ ${_elements[i]} == "newline" ]]; then
          newline_pos=$i
          break
        fi
      done
      
      if (( newline_pos > 0 )); then
        # Insert before first newline
        _elements=( "${_elements[@]:0:$((newline_pos-1))}" "subshell" "${_elements[@]:$((newline_pos-1))}" )
      else
        # No newline found, append to end
        _elements+=("subshell")
      fi
      
      POWERLEVEL9K_LEFT_PROMPT_ELEMENTS=("${_elements[@]}")
    fi
  fi
}

# --- Starship Implementation ---

# Get the bundled starship config content - hardcoded single source of truth
_subshell_get_bundled_starship_config() {
  cat <<'EOF'
[custom.subshell_inside]
when = 'test "${SUBSHELL_OUTSIDE:-0}" -eq 0 && test -n "${SUBSHELL_PROMPT:-}"'
command = 'printf %s "${SUBSHELL_PROMPT:-subshell}"'
symbol = '📂'
style = 'blue'
format = '[$symbol$output]($style)'
shell = 'sh'

[custom.subshell_outside]
when = 'test "${SUBSHELL_OUTSIDE:-0}" -eq 1 && test -n "${SUBSHELL_PROMPT:-}"'
command = 'printf "%s (outside %s)" "${SUBSHELL_PROMPT:-subshell}" "${SUBSHELL_ROOT}"'
symbol = '‼️ '
style = 'red bold'
format = '[$symbol$output]($style)'
shell = 'sh'
EOF
}

# Ephemeral starship config injector: creates a temp config that adds subshell modules
_subshell_starship_ephemeral_config() {
  # If user already points STARSHIP_CONFIG to our generated file, skip.
  if [[ ${STARSHIP_CONFIG:-} == *subshell-starship-* && -f ${STARSHIP_CONFIG} ]]; then
    return 0
  fi
  
  local tmpdir=${TMPDIR:-/tmp}
  local orig=""
  
  # Locate original config if any
  if [[ -n ${STARSHIP_CONFIG:-} && -r $STARSHIP_CONFIG ]]; then
    orig=$STARSHIP_CONFIG
  else
    local defcfg=${XDG_CONFIG_HOME:-$HOME/.config}/starship.toml
    [[ -r $defcfg ]] && orig=$defcfg
  fi
  
  local dest="$tmpdir/subshell-starship-${UID:-$EUID}-${PPID:-$$}.toml"
  
  # Build new config by combining user config + bundled starship modules
  {
    [[ -n $orig ]] && cat "$orig"
    echo "# --- added by subshell (ephemeral) ---"
    _subshell_get_bundled_starship_config
  } >| "$dest"

  # Root-level format handling: if no top-level format line references our modules, inject them.
  if ! grep -Eq '^[[:space:]]*format[[:space:]]*=' "$dest"; then
    printf '\nformat = "$custom.subshell_outside$custom.subshell_inside $all"\n' >> "$dest"
  else
    if ! grep -Eq '\$custom\.subshell_(inside|outside)' "$dest"; then
      # Prepend our modules before first existing format definition's $all or at start.
      awk 'BEGIN{done=0}
        /^format *=/ && done==0 {
          if ($0 ~ /\$all/) {
            sub(/\$all/,"$custom.subshell_outside$custom.subshell_inside $all")
          } else {
            sub(/"/,"$custom.subshell_outside$custom.subshell_inside ")
          }
          done=1
        }
        {print}' "$dest" >| "$dest.tmp" && mv "$dest.tmp" "$dest"
    fi
  fi

  export STARSHIP_CONFIG=$dest
  [[ -n ${SUBSHELL_DEBUG:-} ]] && print -u2 -- "[subshell][debug] starship ephemeral config generated: $STARSHIP_CONFIG"
}

subshell_init_starship() {
  # Ensure ephemeral config (zero-config starship integration) unless disabled.
  if [[ -z ${SUBSHELL_NO_EPHEMERAL_STARSHIP:-} ]]; then
    _subshell_starship_ephemeral_config || true
  fi

  [[ -n ${SUBSHELL_DEBUG:-} ]] && print -u2 -- "[subshell][debug] starship detected (function=$(( ${+functions[starship_precmd]} )) env=$(( ${+STARSHIP_SESSION_KEY} )))"

  # Wrap starship_precmd exactly once so we can post-process $PROMPT.
  if typeset -f starship_precmd >/dev/null && ! typeset -f __subshell_starship_precmd_orig >/dev/null; then
    # Create backup of original function
    local __orig; __orig=$(typeset -f starship_precmd)
    if [[ -n $__orig ]]; then
      # Remove original and create backup
      unfunction starship_precmd 2>/dev/null || true
      eval "${__orig/starship_precmd/__subshell_starship_precmd_orig}"
      # Redefine with our wrapper
      starship_precmd() {
        __subshell_starship_precmd_orig "$@" 2>/dev/null || true
        subshell_starship_post
      }
      [[ -n ${SUBSHELL_DEBUG:-} ]] && print -u2 -- "[subshell][debug] starship precmd wrapped"
    fi
  fi
}

subshell_starship_post() {
  # Placeholder for future starship integration extensions
  :
}

# --- Generic Implementation ---

subshell_init_generic() {
  # Generic prompt modification - inject prefix above PROMPT in subshell_precmd
  [[ -n ${SUBSHELL_DEBUG:-} ]] && print -u2 -- "[subshell][debug] using generic prompt injection"
}

################################################################################
# INITIALIZATION AND HOOKS
################################################################################

# Run detections and initialize appropriate implementation
if subshell_detect_p10k; then
  subshell_init_p10k
elif subshell_detect_starship; then
  subshell_init_starship  
else
  subshell_init_generic
fi

### hooks --------------------------------------------------------------
subshell_chpwd() { subshell_update_state }
subshell_precmd() {
  [[ -n ${SUBSHELL_OUTSIDE-} ]] || subshell_update_state
  # Late starship detection: pick up starship if it initializes after we load
  if ! typeset -f __subshell_starship_precmd_orig >/dev/null; then
    [[ -n ${SUBSHELL_DEBUG:-} ]] && print -u2 -- "[subshell][debug] precmd attempting late starship detect"
    if subshell_detect_starship; then
      subshell_init_starship
    fi
  fi
  # Starship: rely entirely on starship module for indicator
  if subshell_detect_starship; then
    [[ -n ${SUBSHELL_DEBUG:-} ]] && print -u2 -- "[subshell][debug] skipping prefix injection (starship active)"
    return
  fi
  # P10K: segment handles rendering
  if subshell_detect_p10k; then return; fi

  # Generic: inject prefix above PROMPT
  local base=$PROMPT
  if [[ -n $SUBSHELL_PREV_PREFIX ]]; then
    if [[ $base == "$SUBSHELL_PREV_PREFIX"$'\n'* ]]; then
      base=${base#"$SUBSHELL_PREV_PREFIX"$'\n'}
    elif [[ $base == $'\n'"$SUBSHELL_PREV_PREFIX"$'\n'* ]]; then
      base=$'\n'${base#$'\n'"$SUBSHELL_PREV_PREFIX"$'\n'}
    fi
  fi
  if [[ -z ${SUBSHELL_PROMPT} ]]; then
    PROMPT=$base
    SUBSHELL_PREV_PREFIX=
    return
  fi
  local prefix
  prefix=$(subshell_render_pre_prompt)
  if [[ $base == $'\n'* ]]; then
    PROMPT=$'\n'${prefix}$'\n'${base#$'\n'}
  else
    PROMPT=${prefix}$'\n'${base}
  fi
  SUBSHELL_PREV_PREFIX=$prefix
}

### register hooks -----------------------------------------------------
add-zsh-hook chpwd subshell_chpwd
add-zsh-hook precmd subshell_precmd