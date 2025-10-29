repo_name="$(basename "$(pwd)")"
read -r -p "Create repo '${repo_name}'? [y/N]: " confirm
if [[ ${confirm,,} == "y" || ${confirm,,} == "yes" ]]; then
	gh repo create "${repo_name}" --private --source=. --remote=origin --push
fi
