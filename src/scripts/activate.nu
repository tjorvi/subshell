# Subshell Prompt Prefix for Nushell
# - Core behavior per SPEC.md
# - Wraps user's existing prompt via PROMPT_COMMAND
# - Idempotent (does not double-wrap on reload)

# --- defaults ---------------------------------------------------------------
if ($env.SUBSHELL_ROOT? | is-empty) {
  $env.SUBSHELL_PROMPT = "subshell"
}

# Normalize SUBSHELL_ROOT to absolute, if set
if not ($env.SUBSHELL_ROOT? | default "" | is-empty) {
  let raw = $env.SUBSHELL_ROOT
  let homed = (if ($raw | str starts-with "~") { $raw | str replace -r '^~' ($env.HOME | default "") } else { $raw })
  let abs = if ($homed | str starts-with "/") { $homed } else { $env.PWD | path join $homed }
  $env.SUBSHELL_ROOT = $abs
}

# --- helpers ----------------------------------------------------------------
################################################################################
### BUSINESS LOGIC: Core state management
################################################################################

# Compute SUBSHELL_OUTSIDE=0/1 based on $env.PWD and $env.SUBSHELL_ROOT
def subshell_update_state [] {
  if ($env.SUBSHELL_ROOT? | default "" | is-empty) {
    $env.SUBSHELL_OUTSIDE = 0
    return
  }
  let here = ($env.PWD | into string)
  # Normalize root on-the-fly to be robust if user sets/changes it later
  let root_raw = ($env.SUBSHELL_ROOT | into string)
  let root_home = (if ($root_raw | str starts-with "~") { $root_raw | str replace -r '^~' ($env.HOME | default "") } else { $root_raw })
  let root_abs = if ($root_home | str starts-with "/") { $root_home } else { $env.PWD | path join $root_home }
  let root_clean = ($root_abs | str replace -r '/$' '')

  if $here == $root_clean {
    $env.SUBSHELL_OUTSIDE = 0
    return
  }
  let boundary = (if $root_clean == "" { "/" } else { $root_clean + "/" })
  # Special-case root '/': boundary should be '/'
  let boundary = (if $root_clean == "/" { "/" } else { $boundary })

  if ($here | str starts-with $boundary) {
    $env.SUBSHELL_OUTSIDE = 0
    return
  }
  $env.SUBSHELL_OUTSIDE = 1
}

################################################################################
### RENDERING: Visual formatting for different states
################################################################################

# Render the prefix line above the base prompt
def subshell_render_pre_prompt [] {
  if (($env.SUBSHELL_OUTSIDE? | default 0) == 1) {
    let red = (ansi --escape '38;5;196m')
    let reset = (ansi reset)
    $"‼️  ($red)($env.SUBSHELL_PROMPT)($reset) is outside project root (($env.SUBSHELL_ROOT)) ‼️"
  } else {
    let yellow = (ansi --escape '38;5;33m')
    let reset = (ansi reset)
    $"📂 ($yellow)($env.SUBSHELL_PROMPT)($reset)"
  }
}

################################################################################
### PROMPT WRAPPING: Default/fallback prompt integration
################################################################################

# --- prompt wrapping: preserve user's base prompt ---------------------------
# Save the original PROMPT_COMMAND once, so re-sourcing stays idempotent.
if not ((($env | columns) | any { |it| $it == "__SUBSHELL_ORIGINAL_PROMPT_COMMAND" })) {
  let base = if ($env.PROMPT_COMMAND? | is-empty) {
    {|| $"($env.PWD) > " }
  } else {
    $env.PROMPT_COMMAND
  }
  $env.__SUBSHELL_ORIGINAL_PROMPT_COMMAND = $base
}

# Install wrapped PROMPT_COMMAND that injects the prefix on its own line.
$env.PROMPT_COMMAND = {||
  # Recompute on each render (covers dir changes without explicit hooks)
  subshell_update_state
  let prefix = (subshell_render_pre_prompt)
  let base_out = (do $env.__SUBSHELL_ORIGINAL_PROMPT_COMMAND)
  $"($prefix)\n($base_out)"
}