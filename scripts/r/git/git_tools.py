import os
import subprocess

from utils.menu.actionmenu import ActionMenu
from utils.menu.diffmenu import DiffMenu
from utils.script.path import get_my_script_root


def get_git_status_items():
    try:
        status = subprocess.check_output(
            ["git", "status", "--short"], universal_newlines=True
        )
        if status.strip():
            return status.splitlines(), False
        else:
            # Clean working tree, show changes in HEAD
            show_output = subprocess.check_output(
                ["git", "show", "--name-status", "--format=", "HEAD"],
                universal_newlines=True,
            )
            items = []
            for line in show_output.splitlines():
                if line.strip():
                    # git show --name-status gives "M\tfile"
                    # convert to "M  file" to match "git status -s" format (XY file)
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        items.append(f"{parts[0]:<2} {parts[1]}")
                    else:
                        items.append(line)
            return items, True
    except subprocess.CalledProcessError:
        return [], False


class GitMenu(ActionMenu):
    def __init__(self):
        super().__init__(close_on_selection=False)
        self._populate_items()

    def _populate_items(self):
        items, is_clean = get_git_status_items()
        for item in items:
            filename = item[3:]
            if " -> " in filename:
                filename = filename.split(" -> ")[-1].strip('"')

            if is_clean:
                git_args = ["HEAD~1", "HEAD", filename]
            elif item.startswith("??"):
                git_args = ["--no-index", os.devnull, filename]
            else:
                git_args = [filename]

            self.add_action(
                item,
                callback=lambda args=git_args: DiffMenu(git_args=args).exec(),
            )

    @ActionMenu.action("Refresh", k="ctrl+r")
    def _refresh(self):
        self.clear_items()
        self._populate_items()


if __name__ == "__main__":
    repo_path = os.environ.get("GIT_REPO", "")
    if not repo_path:
        repo_path = get_my_script_root()
    os.chdir(repo_path)

    GitMenu().exec()
