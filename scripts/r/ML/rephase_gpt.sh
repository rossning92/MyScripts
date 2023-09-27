set -e

tmpfile=$(mktemp)
input=$(<"$1")
cat >"$tmpfile" <<EOF
Rephase the following, use proper english, don't use fancy word, simple and concise but still keep all meaning, don't replace the important keyword that may change the meaning. If i'm using markdown, keep the format don't change:

---

$input
EOF

[[ "$(uname -o)" == "Msys" ]] && tmpfile="$(cygpath -w "${tmpfile}")"
run_script r/ML/chatgpt.py --copy-to-clipboard "$tmpfile"
