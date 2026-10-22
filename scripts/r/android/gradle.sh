#!/usr/bin/env bash
set -euo pipefail

if [[ -x ./gradlew ]]; then
    GRADLE=./gradlew
else
    GRADLE=gradle
fi

# Keep Gradle's downloaded distribution and dependency cache with the project.
# An explicit GRADLE_USER_HOME still takes precedence.
export GRADLE_USER_HOME="${GRADLE_USER_HOME:-$PWD/.gradle}"

if [[ $# -eq 0 ]]; then
    set -- assembleDebug
fi

if [[ ${1:-} == --accept-licenses ]]; then
    android_home="${ANDROID_HOME:-$HOME/Android/Sdk}"
    sdkmanager="$android_home/cmdline-tools/latest/bin/sdkmanager"
    if [[ ! -x $sdkmanager ]]; then
        sdkmanager="$(command -v sdkmanager || true)"
    fi
    if [[ -z $sdkmanager ]]; then
        echo "sdkmanager not found." >&2
        exit 1
    fi
    printf '+ %q --sdk_root=%q --licenses\n' "$sdkmanager" "$android_home"
    yes | "$sdkmanager" --sdk_root="$android_home" --licenses
    exit
fi

printf '+ %q' "$GRADLE"
printf ' %q' "$@"
printf '\n'
"$GRADLE" "$@"
