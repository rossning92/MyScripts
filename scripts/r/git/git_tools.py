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

menu = ActionMenu(close_on_selection=False)


@menu.func()
def commit(dry_run=False, amend=False) -> bool:
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


@menu.func()
def commit_and_push():
    if commit():
        git_push()


@menu.func()
def revert_all():
    call_echo("git status --short")
    if not confirm("Revert all files?"):
        return
    call_echo("git reset HEAD --hard")


@menu.func()
def git_push(force=False):
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


@menu.func()
def git_push_force():
    git_push(force=True)


def git_log(show_all=True):
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


@menu.func(hotkey="alt+s")
def git_status():
    print2(
        "\nrepo_dir: %s" % os.getcwd(),
        color="magenta",
    )

    commit(dry_run=True)
    git_log(show_all=False)
    input()


def create_bundle():
    if bundle_file is not None:
        print2("Create bundle: %s" % bundle_file)
        call_echo(["git", "bundle", "create", bundle_file, "master"])


def add_gitignore_node():
    urlretrieve(
        "https://raw.githubusercontent.com/github/gitignore/master/Node.gitignore",
        ".gitignore",
    )


def add_gitignore():
    if os.path.exists(".gitignore"):
        return

    if os.path.exists("package.json"):
        add_gitignore_node()

    else:  # unknown project
        with open(".gitignore", "w") as f:
            f.writelines(["/build"])


@menu.func()
def switch_branch():
    call_echo(["git", "branch"])
    name = input("Switch to branch [master]: ")
    if not name:
        name = "master"
    call_echo(["git", "checkout", name])


def get_current_branch():
    return subprocess.check_output(
        ["git", "branch", "--show-current"], universal_newlines=True
    ).strip()


@menu.func()
def amend_history_commit():
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


@menu.func()
def amend():
    commit(amend=True)


@menu.func(hotkey="alt+a")
def amend_and_push():
    if commit(amend=True):
        git_push(force=True)


@menu.func()
def pull():
    call_echo(["git", "pull"])


@menu.func()
def revert_file():
    file = input("Input file to revert: ")
    if file:
        call_echo("git checkout %s" % file)


def is_working_tree_clean():
    return (
        subprocess.check_output(
            ["git", "status", "--short"], universal_newlines=True
        ).strip()
        == ""
    )


@menu.func(hotkey="alt+d")
def diff():
    if not is_working_tree_clean():
        call_echo(["git", "diff"])
    else:
        call_echo(["git", "diff", "HEAD^", "HEAD"])


@menu.func()
def diff_previous_commit():
    call_echo("git diff HEAD^ HEAD")


@menu.func()
def diff_with_main_branch():
    call_echo("git diff origin/main...HEAD")


@menu.func()
def diff_commit():
    commit = input("commit hash: ")
    call_echo("git show %s" % commit)


@menu.func(hotkey="`")
def command():
    cmd = input("cmd> ")
    subprocess.call(cmd, shell=True)


@menu.func()
def unbundle():
    print2("Restoring from: %s" % bundle_file)
    call_echo(["git", "pull", bundle_file, "master:master"])


@menu.func()
def undo():
    call_echo("git reset HEAD@{1}")


@menu.func()
def open_folder():
    shell_open(os.getcwd())


@menu.func()
def fixup_commit():
    commit_id = input("Fixup commit (hash): ")
    call_echo(["git", "commit", "--fixup", commit_id])
    call_echo(["git", "rebase", commit_id + "^", "-i", "--autosquash"])


@menu.func()
def sync_github():
    FNULL = fnull()
    ret = subprocess.call(
        "gh repo view rossning92/%s" % repo_name, shell=True, stdout=FNULL
    )
    if ret == 1:
        cd(os.path.dirname(repo_dir))
        if not confirm('Create "%s" on GitHub?' % repo_name):
            sys.exit(1)
        call_echo("gh repo create --private -y %s" % repo_name)
    else:
        print('GitHub repo already exists: "%s"' % repo_name)
    cd(repo_dir)

    subprocess.check_call(
        [
            "git",
            "remote",
            "add",
            "origin",
            f"https://github.com/rossning92/{repo_name}.git",
        ]
    )


@menu.func()
def git_init():
    run_script("r/git/git_init.sh")


@menu.func()
def clean_all():
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


def checkout_branch(branch):
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


@menu.func()
def amend_commit_message(message=None):
    args = ["git", "commit", "--amend"]
    if message:
        args += ["-m", message]
    call_echo(args)


@menu.func()
def create_patch():
    hash = input("Enter commit hash: ")
    if not hash:
        return
    call_echo(["git", "format-patch", "-1", hash])


@menu.func()
def garbage_collect():
    if confirm("Dangerous! this will expire all recent reflogs."):
        run_script("r/git/garbage_collect.sh")


@menu.func()
def checkout_remote_branch_partial():
    run_script(
        "r/git/git_checkout_remote_branch_partial.sh", variables={"GIT_REPO": repo_dir}
    )


@menu.func()
def checkout_remote_branch():
    run_script("r/git/git_checkout_remote_branch.sh", variables={"GIT_REPO": repo_dir})


@menu.func()
def apply_patch():
    file = input("Enter patch file path: ")
    if not file:
        return
    call_echo(["git", "apply", "--reject", "--whitespace=fix", file])


@menu.func()
def unstash():
    call_echo(["git", "stash", "apply"])


@menu.func()
def create_new_branch_and_checkout():
    branch = input("new branch name: ")
    if branch:
        call_echo(["git", "checkout", "-b", branch])


@menu.func()
def cherry_pick():
    commit = input("new commit hash: ")
    if commit:
        call_echo(["git", "cherry-pick", commit])


@menu.func()
def commit_gpt():
    run_script("r/ML/gpt/commitgpt.sh")


if __name__ == "__main__":
    backup_dir = os.environ.get("GIT_REPO_BACKUP_DIR")  # env: GIT_REPO_BACKUP_DIR
    repo_dir = os.environ.get("GIT_REPO")  # env: GIT_REPO
    if not repo_dir:
        repo_dir = get_my_script_root()

    repo_name = os.path.basename(repo_dir)
    if repo_name is None:
        raise Exception("Invalid repo name")

    bundle_file = None
    if backup_dir:
        bundle_file = os.path.join(backup_dir, repo_name + ".bundle")

    cd(repo_dir)

    menu.exec()
