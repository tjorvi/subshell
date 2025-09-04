export ZSH="$HOME/.oh-my-zsh"
plugins=(git)
# dstufft has a blank line but also no clock nor timing info
# which would interfere with test stability
ZSH_THEME="dstufft"
source $ZSH/oh-my-zsh.sh
