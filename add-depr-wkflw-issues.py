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

def main(org, name, color, description, exclude_private=False):
    """
    Script entrypoint
    """
    gh_headers = get_github_headers()

    count = 1
    for repo in get_repos(gh_headers, org, exclude_private):
        LOG.info("\n\n******* CHECKING REPO: {repo} ({count}) ************\n")
        create_or_update_label(gh_headers, org, repo, name, color, description)
        count = count + 1
    LOG.info("Successfully standardised label {name} across {count} repos")

def get_repos(gh_headers, org, exclude_private):
    """
    Generator
    Yields each repo'- name in the org
    """
    org_url = "https://api.github.com/orgs/{0}/repos".format(org)
    params = {"page": 1}
    if exclude_private:
        params["type"] = "public"
    response = requests.get(org_url, headers=gh_headers, params=params).json()
    while len(response) > 0:
        for repo_data in response:
            assert not repo_data['private']
            yield repo_data['name']
        params["page"] = params["page"] + 1
        response = requests.get(org_url, headers=gh_headers, params=params).json()


if __name__ == "__main__":
    main()