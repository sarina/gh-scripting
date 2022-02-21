#!/usr/bin/env python3
"""
Usage:
    python -m add-depr-wkflw-issues.py

Requires:
    GITHUB_AUTH token in local environment

Description:
    Transfers reference workflow template to all repos in the org. Additionally,
    if the org doesn't have issues enabled, transfers a reference issue template
    and issue configuration (if issues are enabled, inheriting a more open
    reference issue template set will suffice).
"""

import logging
import os
import subprocess
import sys
import argparse
import requests

from ghelpers import get_github_headers


# Switch to DEBUG for additional debugging info
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

def main(org, root_dir, exclude_private=False, interactive=False):
    """
    Goes through all repos in an org, clones them, makes a new branch, copies
    specific files, commits them, creates a pull request, and merges the pull
    request.

    * org (str): GitHub organization
    * root_dir (str): path to directory to clone repos (on Mac, may look like 
      `/Users/<uname>/path/to/dir`
    * exclude_private (bool): if True, script skips private repos (default
      False)
    * interactive (bool): if True, pauses before committing files upstream and
      awaits user confirmation
    """
    gh_headers = get_github_headers()
    branch_name = "sarina/test"
    count = 1
    for rname, ssh_url, dbranch, has_issues in get_repos(gh_headers, org, exclude_private):
        LOG.info("\n\n******* CHECKING REPO: {rname} ({count}) ************\n")
        repo_path = get_repo_path(repo, root_dir)
        clone_repo(root_dir, repo_path, ssh_url, dbranch)
        new_branch(repo_path, branch_name)
        add_files(has_issues, interactive)
        commit_and_pr(gh_headers, org, rname)
        count = count + 1
    LOG.info("Successfully copied workflow to {count} repos")


def get_repos(gh_headers, org, exclude_private):
    """
    Generator
    Yields a 4-tuple of repo data:
    - repo name (str)
    - ssh url (str)
    - default branch name (str)
    - has issues (boolean)
    """
    org_url = "https://api.github.com/orgs/{0}/repos".format(org)
    params = {"page": 1}
    if exclude_private:
        params["type"] = "public"
    response = requests.get(org_url, headers=gh_headers, params=params).json()
    while len(response) > 0:
        for repo_data in response:
            yield (
                repo_data['name'],
                repo_data['ssh_url'],
                repo_data['default_branch'],
                repo_data['has_issues']
            )
        params["page"] = params["page"] + 1
        response = requests.get(org_url, headers=gh_headers, params=params).json()


def clone_repo(root_dir, repo_path, ssh_url, default_branch):
    """
    If not already cloned into root_dir, clones repo at that location. If
    cloned, switches to the repo's default_branch and pulls down the latest
    changes.
    """
    # Dev note: process.communicate returns a tuple of (output, error)
    path_exists = os.path.exists(repo_path)

    if not path_exists:
        process = subprocess.Popen(["/opt/homebrew/bin/git", "clone", ssh_url], cwd=root_dir)
        _ = process.communicate()

    else:
        p1 = subprocess.Popen(
            ["/opt/homebrew/bin/git", "checkout", default_branch],
            cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _ = p1.communicate()

        p2 = subprocess.Popen(
            ["/opt/homebrew/bin/git", "pull"],
            cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _ = p2.communicate()


def new_branch(repo_path, branch_name):
    """
    Creates and pushes to remote a new branch called branch_name
    """
    p1 = subprocess.Popen(
        ["/opt/homebrew/bin/git", "checkout", "-b", branch_name],
        cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _ = p1.communicate()

    p2 = subprocess.Popen(
        ["/opt/homebrew/bin/git", "push", "-u", "origin", branch_name],
        cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _ = p2.communicate()

def add_files(has_issues, interactive):
    pass


def commit_and_pr(gh_headers, org, rname):
    pass

def get_repo_path(repo, root_dir):
    if not root_dir.endswith('/'):
        root_dir = root_dir + '/'
    return root_dir + repo


if __name__ == "__main__":
    #clone_repo("frontend-enterprise", "/Users/sarinacanelake/openedx/",
    #"git@github.com:openedx/frontend-enterprise.git", "master")
    new_branch(get_repo_path("frontend-enterprise","/Users/sarinacanelake/openedx/"), "sarina/test")
#    main("openedx", "/Users/sarinacanelake/openedx", True, False)