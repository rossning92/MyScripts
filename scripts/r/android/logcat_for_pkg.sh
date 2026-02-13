function logcat {
    pkg="$1"
    uid="$(adb shell pm list package -U $pkg | sed 's/.*uid://')"
    if [ -z "$uid" ]; then
        echo >&2 "pkg '$pkg' not found"
        return 1
    fi

    adb logcat --uid="$uid" "$@"
}

logcat {{PKG_NAME}} "$@"
