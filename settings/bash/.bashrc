# If not running interactively, don't do anything
[[ $- != *i* ]] && return

# PS1='[\u@\h \W]\$ '
# PS1="\[\e[1;34m\]╭─\[\e[1;32m\]\u@\h \[\e[0;36m\]\W\n\[\e[1;34m\]╰─❯ \[\e[0m\]"

PROMPT_COMMAND='if [ -n "$LAST_PROMPT" ]; then echo; fi; LAST_PROMPT=1' # prints a newline after each command
PS1='\[\e]0;\w\a\][\[\033[32m\]\u@\h \[\033[35m\]\W\[\033[0m\]]\n$ '

export PATH="$HOME/MyScripts/bin:$PATH"

alias c='xclip -selection clipboard'
alias grep='grep --color=auto'
alias i='sudo pacman -S --noconfirm'
alias ls='ls --color=auto'
alias v=nvim

if [[ -n "$TERMUX_VERSION" ]]; then
	[[ "$(tty)" == "/dev/pts/0" ]] && $HOME/MyScripts/myscripts --startup
fi
