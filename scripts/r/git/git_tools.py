import os
import subprocess
import sys
from urllib.request import urlretrieve

from _shutil import (
    call2,
    call_echo,
    cd,
    confirm,
    fnull,
    get_output,
    get_time_str,
    print2,
)
from utils.menu.actionmenu import ActionMenu
from utils.script.path import get_my_script_root
from utils.shutil import shell_open


def add_gitignore_node():
    urlretrieve(
        "https://raw.githubusercontent.com/github/gitignore/master/Node.gitignore",
        ".gitignore",
    )


def is_working_tree_clean():
    return (
        subprocess.check_output(
            ["git", "status", "--short"], universal_newlines=True
        ).strip()
        == ""
    )


class GitMenu(ActionMenu):
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

        self.repo_name = os.path.basename(repo_path)
        if self.repo_name is None:
            raise Exception("Invalid repo name")

        self.bundle_file = None
        if backup_dir:
            self.bundle_file = os.path.join(backup_dir, self.repo_name + ".bundle")

        cd(repo_path)

        super().__init__(prompt=self.repo_path, close_on_selection=False)

    @ActionMenu.action()
    def commit(self, dry_run=False, amend=False) -> bool:
        if is_working_tree_clean():
            print2("Working directory clean, changed files in HEAD:", color="gray")
            for line in get_output(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
                shell=False,
            ).splitlines():
                print2("  " + line, color="gray")
            return False

        call_echo("git status --short")
        if not dry_run and confirm("Commit all changes?"):
            call_echo("git add -A")

            if amend:
                call_echo("git commit --amend --no-edit --quiet")
            else:
                message = input("commit message: ")
                if not message:
                    message = "Temporary commit @ %s" % get_time_str()

                call_echo(["git", "commit", "-m", message])
            return True
        else:
            return False

    def add_gitignore(self):
        if os.path.exists(".gitignore"):
            return

        if os.path.exists("package.json"):
            add_gitignore_node()

        else:  # unknown project
            with open(".gitignore", "w") as f:
                f.writelines(["/build"])

    @ActionMenu.action()
    def amend_history_commit(self):
        commit_id = input("History commit ID: ")

        call_echo(["git", "tag", "history-rewrite", commit_id])
        call2(["git", "config", "--global", "advice.detachedHead", "false"])
        call_echo(["git", "checkout", commit_id])

        input("Press enter to rebase children comments...")
        call_echo(
            [
                "git",
                "rebase",
                "--onto",
                "HEAD",
                # from commit id <==> master
                "tags/history-rewrite",
                "master",
            ]
        )
        call_echo(["git", "tag", "-d", "history-rewrite"])

    @ActionMenu.action(hotkey="alt+d")
    def diff(self):
        if not is_working_tree_clean():
            call_echo(["git", "diff"])
        else:
            call_echo(["git", "diff", "HEAD^", "HEAD"])

    @ActionMenu.action()
    def diff_previous_commit(self):
        call_echo("git diff HEAD^ HEAD")

    @ActionMenu.action()
    def diff_with_main_branch(self):
        call_echo("git diff origin/main...HEAD")

    @ActionMenu.action()
    def diff_commit(self):
        commit = input("commit hash: ")
        call_echo("git show %s" % commit)

    @ActionMenu.action(hotkey="`")
    def command(self):
        cmd = input("cmd> ")
        subprocess.call(cmd, shell=True)

    @ActionMenu.action()
    def open_folder(self):
        shell_open(os.getcwd())

    @ActionMenu.action()
    def fixup_commit(self):
        commit_id = input("Fixup commit (hash): ")
        call_echo(["git", "commit", "--fixup", commit_id])
        call_echo(["git", "rebase", commit_id + "^", "-i", "--autosquash"])

    @ActionMenu.action()
    def sync_github(self):
        FNULL = fnull()
        ret = subprocess.call(
            "gh repo view rossning92/%s" % self.repo_name, shell=True, stdout=FNULL
        )
        if ret == 1:
            os.chdir(os.path.dirname(self.repo_path))
            if not confirm('Create "%s" on GitHub?' % self.repo_name):
                sys.exit(1)
            call_echo("gh repo create --private -y %s" % self.repo_name)
        else:
            print('GitHub repo already exists: "%s"' % self.repo_name)
        os.chdir(self.repo_path)

        subprocess.check_call(
            [
                "git",
                "remote",
                "add",
                "origin",
                f"https://github.com/rossning92/{self.repo_name}.git",
            ]
        )

    @ActionMenu.action()
    def switch_branch(self):
        call_echo(["git", "branch"])
        name = input("Switch to branch [master]: ")
        if not name:
            name = "master"
        call_echo(["git", "checkout", name])

    def checkout_branch(self, branch):
        if (
            subprocess.check_output(
                ["git", "branch", "--list", branch], universal_newlines=True
            ).strip()
            == ""
        ):
            if confirm("Create branch %s?" % branch):
                call_echo(["git", "checkout", "-b", branch])
            else:
                raise Exception('branch does not exist: "%s"' % branch)

        call_echo(["git", "checkout", branch])


if __name__ == "__main__":
    backup_dir = os.environ.get("GIT_REPO_BACKUP_DIR")
    repo_path = os.environ.get("GIT_REPO", "")
    if not repo_path:
        repo_path = get_my_script_root()

    GitMenu(repo_path=repo_path).exec()
