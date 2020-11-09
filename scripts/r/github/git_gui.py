from _shutil import *


def print_help():
    print2(
        "[h] help\n"
        "[c] commit [C] commit & push\n"
        "[a] amend  [A] amend & push\n"
        "[p] push\n"
        "[s] git status\n"
        "[l] git log\n"
        "[r] revert all changes\n"
    )


def commit(dry_run=False, amend=False):
    if dry_run:
        call_echo("git status --short")

    else:
        call_echo("git add -A")

        if amend:
            call_echo("git commit --amend --no-edit --quiet")
        else:
            call_echo('git commit -m "Initial commit"')


def revert():
    call_echo("git status --short")
    if not yes("Revert all files?"):
        return
    call_echo("git reset HEAD --hard")


def git_push():
    call_echo("git push -u origin master")


if __name__ == "__main__":
    repo_dir = r"{{GIT_REPO}}"
    repo_name = os.path.basename(repo_dir)

    cd(repo_dir)

    FNULL = fnull()
    ret = subprocess.call(
        "gh repo view rossning92/%s" % repo_name, shell=True, stdout=FNULL
    )
    if ret == 1:
        if not yes('Create "%s" on GitHub?' % repo_name):
            sys.exit(1)
        call_echo("gh repo create %s" % repo_name)

    # Init repo
    if not os.path.exists(".git"):
        call_echo("git init")
        call_echo(
            "git remote add origin https://github.com/rossning92/%s.git" % repo_name
        )

    # Add .gitignore
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w") as f:
            f.writelines(["/build"])

    commit(dry_run=True)

    print_help()

    while True:
        ch = getch()
        if ch == "h":
            print_help()
        elif ch == "c":
            call_echo("git status --short")
            if yes("Confirm commit?"):
                commit()
        elif ch == "C":
            call_echo("git status --short")
            if yes("Confirm commit?"):
                commit()
            git_push()
        elif ch == "a":
            call_echo("git status --short")
            if yes("Confirm amend?"):
                commit(amend=True)
        elif ch == "A":
            call_echo("git status --short")
            if yes("Confirm amend + push?"):
                commit(amend=True)
                call_echo("git push -u origin master --force")
        elif ch == "p":
            git_push()
        elif ch == "s":
            commit(dry_run=True)
        elif ch == "l":
            call_echo("git log --pretty=oneline --abbrev-commit")
        elif ch == "r":
            revert()
        elif ch == "1":
            call_echo("cmd")

