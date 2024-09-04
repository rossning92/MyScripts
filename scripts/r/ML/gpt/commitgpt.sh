set -e

temp_file=$(mktemp)
diff=$(git diff)
cat >"$temp_file" <<EOF
Suggest 10 commit message candidates based on the following diff:
${diff}

Commit messages should:
 - Follow conventional commits
 - Summerize key changes
 - Message format should be: <description>

Examples:
 - Add password regex pattern
 - Add new test cases
EOF

message=$(run_script r/ai/openai/complete_chat.py "$temp_file" | fzf | cut -d '.' -f 2- | xargs)

git add -A
git commit -m "$message"
