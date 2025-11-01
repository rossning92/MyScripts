#!/usr/bin/env bash

__powerline() {
	BG_BLUE="\\[$(tput setab 4)\\]"
	BG_TEAL="\\[$(tput setab 6)\\]"
	FG_BLUE="\\[$(tput setaf 4)\\]"
	FG_DARK="\\[$(tput setaf 0)\\]"
	FG_TEAL="\\[$(tput setaf 6)\\]"
	FG_LIGHT="\\[$(tput setaf 15)\\]"
	RESET="\\[$(tput sgr0)\\]"

	ps1() {
		PS1="${FG_DARK}"
		PS1+="${BG_BLUE} \\u@\\h "
		PS1+="${FG_BLUE}${BG_TEAL}"
		PS1+="${BG_TEAL}${FG_DARK} \\w "
		PS1+="${RESET}${FG_TEAL}${RESET} "
	}

	PROMPT_COMMAND=ps1
}
# Skip if not interactive shell
[[ $- == *i* ]] || return
__powerline
unset __powerline
