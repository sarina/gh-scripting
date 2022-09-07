#!/usr/bin/env python3
"""
Usage:
    python -m replace_string_with_another.py

Requires:
    GITHUB_AUTH token in local environment

Description:
    For each repo in your org, looks for a given string. If the string exists,
    switches to a new branch, replaces the string with a new string, commits
    changes, and opens a PR. Everything currently hard-coded.

Note:
    swap_strings has hardcoded shell commands that are wonky due to OSX. If
    you're not on OSX you should examine and change them.
"""

import datetime
import json
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
    pr_details = {
        "title": "Fix github url strings (org edx -> openedx)",
        "body": "## This PR was autogenerated\n\nThis pr replaces the old GitHub organization, github.com/edx, with the new GitHub organization, github.com/openedx.\n\nTagging @openedx/tcril-engineering for review, but others are welcome to provide review.\n\nRef: https://github.com/openedx/tcril-engineering/issues/42"
    }

    prs = []
    pr_failed = []
    repos_skipped = []

    for repo_data in get_repos(gh_headers, org, exclude_private):
        (rname, ssh_url, dbranch, _, count) = repo_data
        LOG.info("\n\n******* CHECKING REPO: {} ({}) ************".format(rname, count))

        repo_path = get_repo_path(rname, root_dir)
        # clone repo; if exists, checkout the default branch & pull latest
        clone_repo(root_dir, repo_path, ssh_url, dbranch)

        # Search for the string; fail fast if none exist
        if not found(old_string, repo_path):
            LOG.info("Did not find string {}".format(old_string))
            continue

        if not new_branch(repo_path, branch_name):
            # this branch already exists
            LOG.info("Skipping {}, branch already exists".format(rname))
            repos_skipped.append([rname, "branch exists"])
            continue

        # Swap old string for new string
        swap_strings(old_string, new_string, repo_path)

        if interactive:
            try:
                interactive_commit(repo_path)
            except RepoError:
                # move on to next repo
                continue

        make_commit(repo_path, commit_msg)
        try:
            pr_url = make_pr(gh_headers, org, rname, branch_name, dbranch, pr_details)
            prs.append(pr_url)
        except PrCreationError as pr_err:
            LOG.info(pr_err.__str__())
            # info you need to retry
            pr_failed.append((org, rname, branch_name, dbranch, pr_details))
        # Without, you hit secondary rate limits if you have more than ~30
        # repos. I tried 3, too short. 5, got through 80. 30, totally worked. there's a good number
        # in between that i'm sure
        time.sleep(15)

    LOG.info(
        "Processed {} repos; see output/prs.json ({}) and output/failed.json ({})".format(
            count, len(prs), len(pr_failed)
        )
    )
    LOG.info("Skipped these repos as branch was already defined: {}".format(repos_skipped))

    ts = str(datetime.datetime.now())[:19]
    with open(f"output/prs_{ts}.json", "w") as f:
        f.write(json.dumps(prs))

    with open(f"output/failed_{ts}.json", "w") as f2:
        f2.write(json.dumps(pr_failed))

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
    c1 = f'/usr/bin/grep -rl "{old_string}"'
    # Command two: Exclude .git/ dir: grep -Evw ".git"
    c2 = f'/usr/bin/grep -Evw ".git"'
    # Command three: Swap!
    # delimiter for sed; rather than escape we'll use _ if we're replacing a URL
    d = "/"
    if "/" in old_string or "/" in new_string:
        d = "_"
    # NOTE!!! This is the OSX command, drop `LC_ALL=C` and `'' -e` if not OSX!
    c3 = f"LC_ALL=C /usr/bin/xargs /usr/bin/sed -i '' -e 's{d}{old_string}{d}{new_string}{d}g'"

    # Now chain those calls together in a subprocess wheee
    chained = c1 + " | " + c2 + " | " + c3
    proc = subprocess.Popen(
        chained,
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
