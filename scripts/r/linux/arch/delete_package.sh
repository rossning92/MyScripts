pkg=$(pacman -Qe | fzf | cut -d ' ' -f1)
[[ -n "$pkg" ]] && sudo pacman -Rns --noconfirm "$pkg"
