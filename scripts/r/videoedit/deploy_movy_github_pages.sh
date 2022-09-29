set -e
cd "$(dirname "$0")/movy"

npm run build

git branch --delete --force gh-pages || true
git checkout --orphan gh-pages
git add -f dist
git commit -m "Rebuild GitHub pages"
# update dist/ folder as the project root
git filter-branch -f --prune-empty --subdirectory-filter dist
git push -f origin gh-pages
git checkout master
