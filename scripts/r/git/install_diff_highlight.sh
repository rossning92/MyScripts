#!/usr/bin/env bash
set -euo pipefail

work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT
source_url=https://raw.githubusercontent.com/git/git/master/contrib/diff-highlight

curl -fsSL "$source_url/DiffHighlight.pm" -o "$work_dir/DiffHighlight.pm"
curl -fsSL "$source_url/diff-highlight.perl" -o "$work_dir/diff-highlight.perl"
{
  printf '#!/usr/bin/perl\n'
  cat "$work_dir/DiffHighlight.pm" "$work_dir/diff-highlight.perl"
} > "$work_dir/diff-highlight"

perl -c "$work_dir/diff-highlight"
sudo install -m 755 "$work_dir/diff-highlight" /usr/local/bin/diff-highlight
