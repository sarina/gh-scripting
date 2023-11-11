#!/usr/bin/env python3
"""
Helpers for shell commands, such as `cp`, `mv`, or a call
for any command that starts with `git`.
"""
import subprocess

def mkdir(working_dir, dir_name):
    p1 = subprocess.Popen(
        ["/bin/mkdir", dir_name],
        cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _ = p1.communicate()


def cp(working_dir, filepath, dest_path):
    p1 = subprocess.Popen(
        ["cp", filepath, dest_path],
        cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _ = p1.communicate()


def git(command, args, cwd):
    """
    Executes a Git command.
    * command: string
    * args: list of command line arguments
    * cwd: string, which working dir to execute the command in
    """
    # TEMP TODO
    # this is hardcoded for the "gh repo clone" command in checkout_all
    array = ["/opt/homebrew/bin/gh", command, "clone"]
    array.extend(args)
    p1 = subprocess.Popen(
        array,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out = p1.communicate()
    print("{}".format(out))
    return out


class RepoError(Exception):
    pass


def interactive_commit(repo_path):
    """
    Runs `git diff` then waits for user input about whether or not to push changes
    """
    # don't call the `git` method because we always want this to go to stdout
    p1 = subprocess.Popen(
        ["/opt/homebrew/bin/git", "diff"],
        cwd=repo_path
    )
    _ = p1.communicate()

    cmd = input("Push changes? Y/N: ")
    while cmd.lower() not in ["y", "n"]:
        cmd = input("Push changes? Y/N: ")
    if cmd.lower() == 'n':
        cmd2 = input("Press Q to quit program, other inputs will continue to next repo: ")
        if cmd2.lower() == "q":
            raise KeyboardInterrupt
        raise RepoError


def swap_strings(old_string, new_string, repo_path):
    """
    Replaces all occurances of `old_string` in the repo with `new_string`
    recursively starting in the root directory given by `repo_path`

    Does not inspect the `.git/` directory.
    """
    # Command one: Look for files with the old_string, skipping the .git directorys
    c1 = f'/usr/bin/grep -rl --exclude-dir=.git "{old_string}"'

    # Command two: Swap!
    # delimiter for sed; rather than escape we'll use _ if we're replacing a URL
    d = "/"
    if "/" in old_string or "/" in new_string:
        d = "_"
    # NOTE!!! This is the OSX command, drop `LC_ALL=C` and `'' -e` if not OSX!
    c2 = f"LC_ALL=C /usr/bin/xargs /usr/bin/sed -i '' -e 's{d}{old_string}{d}{new_string}{d}g'"

    # Now chain those calls together in a subprocess wheee
    chained = c1 + " | " + c2
    proc = subprocess.Popen(
        chained,
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )

    _ = proc.communicate()


def found(old_string, repo_path):
    """
    Looks through the repo specified by `repo_path` to see if there are any
    occurances of `old_string`

    Returns bool: True if the string is found, else False
    """
    # grep -r old_string . returns an array of which files match the string.
    proc = subprocess.Popen(
        f"grep -r {old_string} .",
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    res, _ = proc.communicate()
    return len(res) > 0
