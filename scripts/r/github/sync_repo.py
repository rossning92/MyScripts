from _shutil import *

if __name__ == "__main__":
    repo_dir = r"{{GIT_REPO}}"
    repo_name = os.path.basename(repo_dir)

    cd(repo_dir)

    with open(os.devnull, "w") as FNULL:
        ret = subprocess.call("gh repo view rossning92/%s" % repo_name, shell=True)

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

    if get_output("git status --short").strip():
        call_echo("git add -A --dry-run")
        if not yes("Confirm?"):
            sys.exit(1)
        call_echo("git add -A")

        call_echo('git commit -m "Initial commit"')

    # Push
    call_echo("git push -u origin master")
