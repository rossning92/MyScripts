set -e

temp_file=$(mktemp)
input=$(<"$1")
cat >"$temp_file" <<EOF
Rephase the following, use proper english, don't use fancy word, simple and concise but still keep all meaning, don't replace the important keyword that may change the meaning. If i'm using markdown, keep the format don't change:

---

$input
EOF

run_script r/ML/chatgpt.py "$temp_file"
read -p '(press enter to exit...)'
