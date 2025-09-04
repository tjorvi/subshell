Put activation scripts in separate files for easy syntax checking and coloring etc.

Use a single .py file for the entire logic for easy distribution. Activation scripts can 
be trivially bundled in a transparent way.

## Activation scripts
Full duplication is expected between different shell activation scripts.
Within each, there must be very clean separation.
  1. Business logic
  2. Prompt library detection (starship, oh-my-zsh, powerline10k), as supported per shell.
  3. Prompt injection implementation for each prompt library.

## Shell and prompt library support

### Starship (with fish or zsh)
### Detection
Check for existence of env $STARSHIP_SESSION_KEY
### Tactic
Copy the users starship config file to a temp dir, set the env var to use that instead, and append 2 static sections to it. One for inside and one for outside.

### Fish (without starship)
### Detection
If $SHELL ends with `fish` and there's no prompt library detected
### Tactic
Use --init-command to wrap the prompt function.
In the wrapper function call the original prompt and capture into a variable.
If the captured prompt starts with a new line then strip that off and print it out. Then print the subshell, then the remainder of the original prompt.

### Powerline10k
### Detection
TODO
### Tactic
Hook into the powerline composable prompt.

### Zsh
### Detection
If $SHELL ends with `zsh` and there's no prompt library detected
### Tactic
Copy the users zshrc to run init code.
Detect if the current prompt starts with an empty line.
Prefix the prompt but hook below the empty line.
