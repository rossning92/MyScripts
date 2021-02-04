import os
import subprocess
import sys

from _shutil import call2, call_echo, cd, fnull, getch, print2, yes

backup_dir = r"{{GIT_REPO_BACKUP_DIR}}"
repo_dir = r"{{GIT_REPO}}"

bundle_file = None
if backup_dir is not None:
    bundle_file = os.path.join(backup_dir, os.path.basename(repo_dir) + ".bundle")
    print("Bundle file path: %s" % bundle_file)


def print_help():
    print2(
        r"""
  _   _ _____ _     ____  
 | | | | ____| |   |  _ \ 
 | |_| |  _| | |   | |_) |
 |  _  | |___| |___|  __/ 
 |_| |_|_____|_____|_|    
""",
        color="magenta",
    )

    print2(
        "[h] help          [1] run command\n"
        "[c] commit        [C] commit & push\n"
        "[a] amend         [A] amend & push\n"
        "[p] pull          [P] push\n"
        "[s] status & log  [d] git diff\n"
        "[r] revert file   [R] revert all changes\n"
        "[Z] undo"
    )


def commit(dry_run=False, amend=False):
    if dry_run:
        call_echo("git status --short")

    else:
        call_echo("git add -A")

        if amend:
            call_echo("git commit --amend --no-edit --quiet")
        else:
            message = input("commit message: ")
            if not message:
                raise Exception("Commit message is required.")

            call_echo(["git", "commit", "-m", message])


def revert():
    call_echo("git status --short")
    if not yes("Revert all files?"):
        return
    call_echo("git reset HEAD --hard")


def git_push():
    call_echo("git push -u origin master")


def show_git_log():
    call_echo(
        [
            "git",
            "log",
            "--date=relative",
            "--pretty=format:%C(yellow)%h %Cblue%ad %Cgreen%aN%Cred%d %Creset%s",
            "--graph",
            "-10",
        ]
    )


def print_status():

    print2(
        r"""
   ____ ___ _____   _____ ___   ___  _     ____  
  / ___|_ _|_   _| |_   _/ _ \ / _ \| |   / ___| 
 | |  _ | |  | |     | || | | | | | | |   \___ \ 
 | |_| || |  | |     | || |_| | |_| | |___ ___) |
  \____|___| |_|     |_| \___/ \___/|_____|____/ 
""",
        color="magenta",
    )

    commit(dry_run=True)
    show_git_log()


def create_bundle():
    if bundle_file is not None:
        print2("Create bundle: %s" % bundle_file)
        call_echo(["git", "bundle", "create", bundle_file, "master"])


if __name__ == "__main__":
    repo_dir = r"{{GIT_REPO}}"
    repo_name = os.path.basename(repo_dir)

    FNULL = fnull()
    ret = subprocess.call(
        "gh repo view rossning92/%s" % repo_name, shell=True, stdout=FNULL
    )
    if ret == 1:
        cd(os.path.dirname(repo_dir))
        if not yes('Create "%s" on GitHub?' % repo_name):
            sys.exit(1)
        call_echo("gh repo create %s" % repo_name)

    # Init repo
    cd(repo_dir)
    if not os.path.exists(".git"):
        call_echo("git init")
        call_echo(
            "git remote add origin https://github.com/rossning92/%s.git" % repo_name
        )

    # Add .gitignore
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w") as f:
            f.writelines(["/build"])

    print_status()

    while True:
        ch = getch()
        if ch == "h":
            print_help()
            continue
        elif ch == "c":
            commit()
        elif ch == "C":
            commit()
            git_push()
        elif ch == "a":
            commit(amend=True)
            create_bundle()
        elif ch == "A":
            commit(amend=True)
            call_echo("git push -u origin master --force")
        elif ch == "P":
            git_push()
        elif ch == "p":
            call_echo("git pull")
        elif ch == "R":
            revert()
        elif ch == "r":
            f = input("Input file to revert: ")
            if f:
                call_echo("git checkout %s" % f)
        elif ch == "d":
            call_echo("git diff")
        elif ch == "1":
            cmd = input("cmd> ")
            call2(cmd)
        elif ch == "b":
            create_bundle()
            continue
        elif ch == "B":
            print2("Restoring from: %s" % bundle_file)
            call_echo(["git", "pull", bundle_file, "master:master"])
        elif ch == "Z":
            call_echo("git reset HEAD@{1}")

        print_status()
