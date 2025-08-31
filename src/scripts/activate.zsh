# cleanup for reloads
autoload -Uz add-zsh-hook

add-zsh-hook -D chpwd subshell_chpwd 2>/dev/null
add-zsh-hook -D precmd subshell_precmd 2>/dev/null
unset SUBSHELL_PREV_PREFIX SUBSHELL_OUTSIDE

# Set the default to "subshell" if SUBSHELL_PROMPT is not set
: ${SUBSHELL_PROMPT:=subshell}

# Normalize the SUBSHELL_ROOT, if it's set
[[ -n ${SUBSHELL_ROOT:-} ]] && SUBSHELL_ROOT="${SUBSHELL_ROOT:A}"

# --- logic: compute inside/outside
subshell_update_state() {
  if [[ -z $SUBSHELL_ROOT ]]; then
    SUBSHELL_OUTSIDE=0
    return
  fi
  local here="${PWD:A}" root="${SUBSHELL_ROOT%/}"
  # Literal prefix check: inside if here == root or here starts with "root/"
  if [[ "$here" == "$root" ]]; then
    SUBSHELL_OUTSIDE=0
  elif [[ "${here[1,${#root}+1]}" == "$root/" ]]; then
    SUBSHELL_OUTSIDE=0
  else
    SUBSHELL_OUTSIDE=1
  fi
}

# --- prompt rendering
subshell_render_pre_prompt() {
  if (( SUBSHELL_OUTSIDE )); then
    print -r -- "‼️  %F{196}${SUBSHELL_PROMPT} is outside project root (${SUBSHELL_ROOT})%f ‼️"
  else
    print -r -- "📂 %F{33}${SUBSHELL_PROMPT}%f"
  fi
}

# --- hook: inject exactly one line above base prompt
subshell_chpwd() { subshell_update_state }
subshell_precmd() {
  [[ -n ${SUBSHELL_OUTSIDE-} ]] || subshell_update_state

  local base=$PROMPT
  if [[ -n $SUBSHELL_PREV_PREFIX && $base == $SUBSHELL_PREV_PREFIX$'
'* ]]; then
    base=${base#"$SUBSHELL_PREV_PREFIX"$'
'}
  fi

  local prefix
  prefix=$(subshell_render_pre_prompt)

  PROMPT="$prefix"$'
'"$base"
  SUBSHELL_PREV_PREFIX=$prefix
}


add-zsh-hook chpwd subshell_chpwd
add-zsh-hook precmd subshell_precmd
