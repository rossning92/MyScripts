import subprocess
import tempfile


def edit_text(text: str):
    with tempfile.NamedTemporaryFile(
        suffix=".tmp", mode="w+", delete=False, encoding="utf-8"
    ) as tmp_file:
        tmp_file.write(text)
        tmp_filename = tmp_file.name

    subprocess.call(["nvim", tmp_filename])

    with open(tmp_filename, "r", encoding="utf-8") as f:
        new_text = f.read()
    return new_text
