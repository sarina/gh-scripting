#!/usr/bin/env python3
"""
Usage:
    python -m replace_string_run_edx_lint.py

Requires:
    GITHUB_AUTH token in local environment

Description:
    Assumes you've run `replace_string_with_another`, thus repos already have
    your working branch defined, and you don't want to open a new set of PRs.

    For each repo in your org, first looks to see if one of the edx_lint files
    is present; if so, rolls back your branch, runs edx_lint, then re-runs
    the core logic to swap strings defined in `replace_string_with_another`.

Note:
    swap_strings has hardcoded shell commands that are wonky due to OSX. If
    you're not on OSX you should examine and change them.
"""

## TODO
# 1. use a file handler, test failing
# 2. check out branch (gracefully fail if does not exist)
# 3. updated commands
# if pylintrc or .editorconfig or commitlint.config.js exist:
## git reset --hard HEAD~1
## for each filename:
### if filename exists:
#### edx_lint write <filename>
# git commit "chore: run `edx_lint` update with the current version of the repo."
# run rest of script

import datetime
import logging
import subprocess
import sys
import time

from ghelpers import *


# Switch to DEBUG for additional debugging info
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

def main(org, root_dir, old_string, new_string, exclude_private=False, interactive=False):
    """
    Goes through all repos in an org, clones them (or switches to the default
    branch and then pulls latest changes), searches for the specified string, if
    found makes a new branch, switches the string with the new string, creates a
    pull request.

    * org (str): GitHub organization
    * root_dir (str): path to directory to clone repos (on Mac, may look like
      `/Users/<uname>/path/to/dir`
    * old_string: what string we're looking to see if each repo has
    * new_string: if old_string is found, what we should replace it with
    * exclude_private (bool): if True, script skips private repos (default
      False)
    * interactive (bool): if True, pauses before committing files upstream and
      awaits user confirmation
    """
    gh_headers = get_github_headers()
    branch_name = "tcril/fix-gh-org-url"
    commit_msg = "fix: fix github url strings (org edx -> openedx)"

    edx_lint_files = [
        "pylintrc",
        ".editorconfig",
        "commitlint.config.js"
    ]
    count_commits = 0
    count_skipped = 0

    ts = str(datetime.datetime.now())[:19]
    filename = f"output/run_edxlint_{ts}.json"
    with open(filename, "w") as f:
        for repo_data in get_repos(gh_headers, org, exclude_private):
            (rname, ssh_url, dbranch, _, count) = repo_data
            LOG.info("\n\n******* CHECKING REPO: {} ({}) ************".format(rname, count))
            # used these as my two testing repos, they don't need to be reprocessed
            if rname in ['django-wiki', 'XBlock']:
                LOG.info(f"skipping {rname}")
                count_skipped += 1
                continue

            repo_path = get_repo_path(rname, root_dir)
            # clone repo; if exists, checkout the default branch & pull latest
            clone_repo(root_dir, repo_path, ssh_url, dbranch)

            # Search for the string; fail fast if none exist
            if not found(old_string, repo_path):
                LOG.info("Did not find string {}".format(old_string))
                count_skipped += 1
                f.write(f"NO STRING: {rname}\n")
                continue

            # Search for the files we need to re-do. Move on if
            # none of them exist.
            exists = False
            for fname in edx_lint_files:
                if find_file(fname, repo_path):
                    LOG.info(f"found {fname}")
                    exists = True
            if not exists:
                LOG.info("Did not find any of the edx_lint files")
                f.write(f"NO LINT FILES: {rname}\n")
                count_skipped += 1
                continue

            # Checkout the already-existing branch_name
            if not checkout_branch(repo_path, branch_name):
                # this branch was never created - sort it out later
                LOG.info(f"Skipping {rname}, branch does not exist")
                count_skipped += 1
                f.write(f"BRANCH !EXISTS: {rname}\n")
                continue

            # Reset the branch to remove last autogen commit
            git_reset(1, repo_path)

            # Go through each special file and run edx_lint on them
            for fname in edx_lint_files:
                if find_file(fname, repo_path):
                    run_edx_lint(fname, repo_path)

            if interactive:
                try:
                    interactive_commit(repo_path)
                except RepoError:
                    # move on to next repo
                    continue

            # Make a commit for the edx_lint update
            make_commit(repo_path, "chore: run `edx_lint` update with the current version of the repo.")

            # # Swap old string for new string
            swap_strings(old_string, new_string, repo_path)
            make_commit(repo_path, commit_msg)
            force_push(repo_path)

            f.write(f"SUCCESS: {rname}\n")
            count_commits += 1
            # PR IS ALREADY MADE SO DO NOT NEED TO UPDATE PR

            # Without PR create calls, this should be able to be lower
            # than 15, but using 15 to be safe
            time.sleep(15)

    LOG.info(
        f"Processed {count} repos; {count_commits} branches successfully updated"
    )
    LOG.info(f"Skipped {count_skipped} repos as branch was non-existant or string didn't exist")


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


def swap_strings(old_string, new_string, repo_path):
    """
    Replaces all occurances of `old_string` in the repo with `new_string`
    recursively starting in the root directory given by `repo_path`

    Does not inspect the `.git/` directory.
    """
    # Command one: Look for files with the old_string
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

def find_file(fname, repo_path):
    """
    Returns True if fname exists in repo path

    fname (str) is the exact filename of a file you seek
    """
    proc = subprocess.Popen(
        f"ls {fname}",
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    # Results will be either ("filename", '') or ('', does not exist error msg)
    out, _ = proc.communicate()

    return len(out) > 0


def run_edx_lint(fname, repo_path):
    """
    Runs `edx_lint write <fname>`
    """
    proc = subprocess.Popen(
        f"edx_lint write {fname}",
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    _ = proc.communicate()

if __name__ == "__main__":
    root_dir = "/Users/sarinacanelake/openedx/"
    old_string = "github.com/edx"
    new_string = "github.com/openedx"
    main("openedx", root_dir, old_string, new_string, exclude_private=False, interactive=False)
