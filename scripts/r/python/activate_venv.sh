venv_path="$HOME/.venv/{{VENV_NAME}}"
if [ ! -d "$venv_path" ]; then
    {{PYTHON_EXEC if PYTHON_EXEC else 'python'}} -m "$venv_path"
fi
source "$HOME/.venv/{{VENV_NAME}}/bin/activate"
