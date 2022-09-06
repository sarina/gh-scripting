#!/usr/bin/env python3
"""
github helpers
"""

import logging
import os
import sys

import github as gh_api
import requests

# Switch to DEBUG for additional debugging info
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

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


def get_github_headers() -> dict:
    """
    Load GH personal access token from file.
    """
    gh_token = os.environ["GITHUB_TOKEN"]
    LOG.info(" Authenticating.")
    gh_client = gh_api.Github(gh_token)
    LOG.info(" Authenticated.")

    gh_headers = {"AUTHORIZATION": f"token {gh_token}"}
    return gh_headers


def get_repos(gh_headers, org, exclude_private):
    """
    Generator that iterates over all repos in `org`
    Yields a 4-tuple of repo data:
    - repo name (str)
    - ssh url (str)
    - default branch name (str)
    - has issues (boolean)

    * exclude_private (bool): if True, excludes private repos
    """
    org_url = "https://api.github.com/orgs/{0}/repos".format(org)
    params = {"page": 1}
    if exclude_private:
        params["type"] = "public"
    count = 0
    response = requests.get(org_url, headers=gh_headers, params=params).json()
    while len(response) > 0:
       for repo_data in response:
           count += 1
           yield (
               repo_data['name'],
               repo_data['ssh_url'],
               repo_data['default_branch'],
               repo_data['has_issues'],
               count
           )
       params["page"] = params["page"] + 1
       response = requests.get(org_url, headers=gh_headers, params=params).json()
