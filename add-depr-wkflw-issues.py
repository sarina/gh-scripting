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
import sys
import argparse
import requests

from ghelpers import get_github_headers


# Switch to DEBUG for additional debugging info
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

def main(org, exclude_private=False, interactive=False):
    """
    Script entrypoint
    """
    gh_headers = get_github_headers()
    branch_name = "add-depr-issue"
    count = 1
    for rname, ssh_url, dbranch, has_issues in get_repos(gh_headers, org, exclude_private):
        LOG.info("\n\n******* CHECKING REPO: {rname} ({count}) ************\n")
        clone_repo(ssh_url, dbranch)
        new_branch(branch_name)
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

def clone_repo(ssh_url, dbranch):
    # if not cloned:
    # clone repo

    # else
    # git checkout master
    # git pull
    pass


def new_branch(branch_name):
    # git checkout -b add-depr-issue; git push -u origin add-depr-issue
    pass


def add_files(has_issues, interactive):
    pass


def commit_and_pr(gh_headers, org, rname):
    pass


if __name__ == "__main__":
    main("openedx", True, False)