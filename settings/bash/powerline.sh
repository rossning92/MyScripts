#!/usr/bin/env bash

__powerline() {
    BG_BLUE="\\[$(tput setab 31)\\]"
    BG_TEAL="\\[$(tput setab 35)\\]"
    FG_BLUE="\\[$(tput setaf 31)\\]"
    FG_DARK="\\[$(tput setaf 0)\\]"
    FG_TEAL="\\[$(tput setaf 35)\\]"
    FG_WHITE="\\[$(tput setaf 15)\\]"
    RESET="\\[$(tput sgr0)\\]"

    ps1() {
        PS1="${FG_WHITE}"
        PS1+="${BG_BLUE} \\u@\\h "
        PS1+="${FG_BLUE}${BG_TEAL}"
        PS1+="${BG_TEAL}${FG_WHITE} \\W "
        PS1+="${RESET}${FG_TEAL}${RESET} "
    }

    PROMPT_COMMAND=ps1
}
# Skip if not interactive shell
[[ $- == *i* ]] || return
__powerline
unset __powerline
