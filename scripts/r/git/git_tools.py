import os
import subprocess
import sys
from urllib.request import urlretrieve

from _script import get_my_script_root, run_script
from _shutil import (
    call2,
    call_echo,
    cd,
    confirm,
    fnull,
    get_output,
    get_time_str,
    print2,
    shell_open,
)
from utils.menu.actionmenu import ActionMenu


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


def git_log(show_all=False):
    args = [
        "git",
        "log",
        "--date=relative",
        "--pretty=format:%C(yellow)%h %Cblue%ad %Cgreen%aN%Cred%d %Creset%s",
        "--graph",
    ]
    if not show_all:
        args.append("-10")
    return subprocess.check_output(args, universal_newlines=True).strip()


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

        super().__init__(
            prompt=git_log() + "\n\n" + self.repo_path, close_on_selection=False
        )

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

    @ActionMenu.action()
    def commit_and_push(self):
        if self.commit():
            self.git_push()

    @ActionMenu.action()
    def revert_all(self):
        call_echo("git status --short")
        if not confirm("Revert all files?"):
            return
        call_echo("git reset HEAD --hard")

    @ActionMenu.action()
    def git_push(self, force=False):
        # Push and auto track remote branch
        subprocess.check_call(["git", "config", "--global", "push.default", "current"])
        args = [
            "git",
            "push",
            # will track remote branch of the same name:
            "-u",
        ]
        if force:
            args += ["--force"]
        call_echo(args)

    @ActionMenu.action()
    def git_push_force(self):
        self.git_push(force=True)

    def git_log(self, show_all=True):
        args = [
            "git",
            "log",
            "--date=relative",
            "--pretty=format:%C(yellow)%h %Cblue%ad %Cgreen%aN%Cred%d %Creset%s",
            "--graph",
        ]
        if not show_all:
            args.append("-10")
        call_echo(
            args,
            check=False,
            shell=False,
        )

    @ActionMenu.action(hotkey="alt+s")
    def git_status(self):
        print2(
            "\nrepo_dir: %s" % os.getcwd(),
            color="magenta",
        )

        self.commit(dry_run=True)
        self.git_log(show_all=False)
        input()

    def create_bundle(self):
        if self.bundle_file is not None:
            print2("Create bundle: %s" % self.bundle_file)
            call_echo(["git", "bundle", "create", self.bundle_file, "master"])

    def add_gitignore(self):
        if os.path.exists(".gitignore"):
            return

        if os.path.exists("package.json"):
            add_gitignore_node()

        else:  # unknown project
            with open(".gitignore", "w") as f:
                f.writelines(["/build"])

    @ActionMenu.action()
    def switch_branch(self):
        call_echo(["git", "branch"])
        name = input("Switch to branch [master]: ")
        if not name:
            name = "master"
        call_echo(["git", "checkout", name])

    def get_current_branch(self):
        return subprocess.check_output(
            ["git", "branch", "--show-current"], universal_newlines=True
        ).strip()

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

    @ActionMenu.action()
    def amend(self):
        self.commit(amend=True)

    @ActionMenu.action(hotkey="alt+a")
    def amend_and_push(self):
        if self.commit(amend=True):
            self.git_push(force=True)

    @ActionMenu.action()
    def pull(self):
        call_echo(["git", "pull"])

    @ActionMenu.action()
    def revert_file(self):
        file = input("Input file to revert: ")
        if file:
            call_echo("git checkout %s" % file)

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
    def unbundle(self):
        print2("Restoring from: %s" % self.bundle_file)
        call_echo(["git", "pull", self.bundle_file, "master:master"])

    @ActionMenu.action()
    def undo(self):
        call_echo("git reset HEAD@{1}")

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
    def git_init(self):
        run_script("r/git/git_init.sh")

    @ActionMenu.action()
    def clean_all(self):
        for dry_run in [True, False]:
            if not dry_run:
                if not confirm("Clean untracked files?"):
                    return

            call_echo(
                [
                    "git",
                    "clean",
                    "-n" if dry_run else "-f",
                    "-x",  # remove ignored files
                    "-d",  # remove directories
                ]
            )

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

    @ActionMenu.action()
    def amend_commit_message(self, message=None):
        args = ["git", "commit", "--amend"]
        if message:
            args += ["-m", message]
        call_echo(args)

    @ActionMenu.action()
    def create_patch(self):
        hash = input("Enter commit hash: ")
        if not hash:
            return
        call_echo(["git", "format-patch", "-1", hash])

    @ActionMenu.action()
    def garbage_collect(self):
        if confirm("Dangerous! this will expire all recent reflogs."):
            run_script("r/git/garbage_collect.sh")

    @ActionMenu.action()
    def checkout_remote_branch_partial(self):
        run_script(
            "r/git/git_checkout_remote_branch_partial.sh",
            variables={"GIT_REPO": repo_path},
        )

    @ActionMenu.action()
    def checkout_remote_branch(self):
        run_script(
            "r/git/git_checkout_remote_branch.sh", variables={"GIT_REPO": repo_path}
        )

    @ActionMenu.action()
    def apply_patch(self):
        file = input("Enter patch file path: ")
        if not file:
            return
        call_echo(["git", "apply", "--reject", "--whitespace=fix", file])

    @ActionMenu.action()
    def unstash(self):
        call_echo(["git", "stash", "apply"])

    @ActionMenu.action()
    def create_new_branch_and_checkout(self):
        branch = input("new branch name: ")
        if branch:
            call_echo(["git", "checkout", "-b", branch])

    @ActionMenu.action()
    def cherry_pick(self):
        commit = input("new commit hash: ")
        if commit:
            call_echo(["git", "cherry-pick", commit])

    @ActionMenu.action()
    def commit_gpt(self):
        run_script("r/ML/gpt/commitgpt.sh")


if __name__ == "__main__":
    backup_dir = os.environ.get("GIT_REPO_BACKUP_DIR")  # env: GIT_REPO_BACKUP_DIR
    repo_path = os.environ.get("GIT_REPO", "")  # env: GIT_REPO
    if not repo_path:
        repo_path = get_my_script_root()

    GitMenu(repo_path=repo_path).exec()
