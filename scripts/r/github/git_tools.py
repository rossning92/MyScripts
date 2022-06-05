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
    menu_item,
    menu_loop,
    print2,
    shell_open,
)

backup_dir = r"{{GIT_REPO_BACKUP_DIR}}"
repo_dir = r"{{GIT_REPO}}"


bundle_file = None
if backup_dir:
    bundle_file = os.path.join(backup_dir, os.path.basename(repo_dir) + ".bundle")


@menu_item(key="c")
def commit(dry_run=False, amend=False):
    if is_working_tree_clean():
        print2("(Working directory clean) Changed files in HEAD:", color="blue")
        for line in get_output(
            ["git", "--no-pager", "diff", "--name-only", "HEAD", "HEAD~1"], shell=False
        ).splitlines():
            print2("  " + line, color="blue")
        return

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


@menu_item(key="C")
def commit_and_push():
    commit()
    git_push()


@menu_item(key="R")
def revert_all():
    call_echo("git status --short")
    if not confirm("Revert all files?"):
        return
    call_echo("git reset HEAD --hard")


@menu_item(key="P")
def git_push(force=False):
    args = "git push"
    if force:
        args += " --force"
    call_echo(args)


@menu_item(key="l")
def show_git_log(show_all=True):
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


@menu_item(key="s")
def print_status():
    print2(
        "\nrepo_dir: %s" % os.getcwd(),
        color="magenta",
    )

    commit(dry_run=True)
    show_git_log(show_all=False)


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


@menu_item(key="b")
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


@menu_item(key="H")
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


@menu_item(key="a")
def amend():
    commit(amend=True)


@menu_item(key="A")
def amend_and_push():
    commit(amend=True)
    git_push(force=True)


@menu_item(key="p")
def pull():
    call_echo(["git", "pull"])


@menu_item(key="r")
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


@menu_item(key="d")
def diff():
    if not is_working_tree_clean():
        call_echo("git diff")
    else:
        call_echo("git diff HEAD^ HEAD")


@menu_item(key="D")
def diff_previous_commit():
    call_echo("git diff HEAD^ HEAD")


@menu_item(key="`")
def command():
    cmd = input("cmd> ")
    subprocess.call(cmd, shell=True)


@menu_item(key="B")
def unbundle():
    print2("Restoring from: %s" % bundle_file)
    call_echo(["git", "pull", bundle_file, "master:master"])


@menu_item(key="Z")
def undo():
    call_echo("git reset HEAD@{1}")


@menu_item(key="O")
def open_folder():
    shell_open(os.getcwd())


@menu_item(key="f")
def fixup_commit():
    commit_id = input("Fixup commit (hash): ")
    call_echo(["git", "commit", "--fixup", commit_id])
    call_echo(["git", "rebase", commit_id + "^", "-i", "--autosquash"])


@menu_item(key="G")
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


@menu_item(key="S")
def setup_project():
    # Init repo
    cd(repo_dir)
    if not os.path.exists(".git"):
        call_echo("git init")
        call_echo(
            "git remote add origin https://github.com/rossning92/%s.git" % repo_name
        )

    # Add .gitignore
    add_gitignore()

    # .gitattribute
    if not os.path.exists(".gitattributes"):
        with open(".gitattributes", "w") as f:
            f.writelines(["* text=auto eol=lf"])


@menu_item(key="X")
def clean_untracked_ignored():
    for dry_run in [True, False]:
        if not dry_run:
            if not confirm("Clean untracked files?"):
                return

        call_echo(
            [
                "git",
                "clean",
                "-n" if dry_run else "-f",
                "-X",  # remove ignored files
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


@menu_item(key="E")
def amend_commit_message(message=None):
    args = ["git", "commit", "--amend"]
    if message:
        args += ["-m", message]
    call_echo(args)


if __name__ == "__main__":
    repo_dir = r"{{GIT_REPO}}"
    repo_name = os.path.basename(repo_dir)

    setup_project()

    while True:
        try:
            menu_loop()
        except KeyboardInterrupt:
            print2("Command cancelled.", color="red")
        except Exception as e:
            print2("ERROR: %s" % e, color="red")
