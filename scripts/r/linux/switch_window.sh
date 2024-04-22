#!/bin/bash

num=$(wmctrl -l | sed 's/  / /' | cut -d " " -f 4- | nl -w 3 -n rn | sed -r 's/^([ 0-9]+)[ \t]*(.*)$/\1 - \2/' | dmenu -b -i -p "Activate" -l 30 | cut -d '-' -f -1)
[[ -z "$num" ]] && exit
wmctrl -l | sed -n "$num p" | cut -c -10 | xargs wmctrl -i -a
