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
    array = ["/opt/homebrew/bin/git", command]
    array.extend(args)
    p1 = subprocess.Popen(
        array,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out = p1.communicate()
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

