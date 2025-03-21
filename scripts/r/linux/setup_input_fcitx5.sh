# https://wiki.archlinux.org/title/Fcitx5

append_line_dedup() {
    touch "$1"
    # Remove the line if it exists and then append it
    if [[ -f "$1" ]] && grep -qF -- "$2" "$1"; then
        repl=$(printf '%s\n' "$2" | sed -e 's/[]\/$*.^[]/\\&/g')
        sed -i "\%^$repl$%d" "$1"
    fi
    echo "$2" >>"$1"
}

prepend_line_dedup() {
    # Remove the line if it exists and then prepend it
    if [[ -f "$1" ]] && grep -qF -- "$2" "$1"; then
        repl=$(printf '%s\n' "$2" | sed -e 's/[]\/$*.^[]/\\&/g')
        sed -i "\%^$repl$%d" "$1"
    fi
    printf '%s\n%s\n' "$2" "$(cat $1)" >"$1"
}

[ -e "$HOME/.config/fcitx5" ] || ln -s "{{MYSCRIPT_ROOT}}/settings/fcitx5" "$HOME/.config/fcitx5"

sudo pacman -S --noconfirm --needed fcitx5 fcitx5-qt fcitx5-gtk fcitx5-config-qt fcitx5-chinese-addons

prepend_line_dedup ~/.xinitrc "export XMODIFIERS=@im=fcitx"
prepend_line_dedup ~/.xinitrc "export QT_IM_MODULE=fcitx"
prepend_line_dedup ~/.xinitrc "export GTK_IM_MODULE=fcitx"

append_line_dedup ~/.xinitrc "fcitx5 -d"
