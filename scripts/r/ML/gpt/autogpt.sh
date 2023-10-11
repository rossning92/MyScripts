# https://github.com/Significant-Gravitas/Auto-GPT/blob/master/docs/installation.md

set -e
BRANCH=stable run_script r/git/git_clone.sh https://github.com/Significant-Gravitas/Auto-GPT
cd ~/Projects/Auto-GPT

cp .env.template .env
sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=\{{OPENAI_API_KEY}}/g" .env

if [[ ! -d 'env' ]]; then
    python -m venv env
    # pip install -r requirements.txt
fi

export OPENAI_API_KEY="{{OPENAI_API_KEY}}"
source env/Scripts/activate

./run.bat
