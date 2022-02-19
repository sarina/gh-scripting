#!/usr/bin/env python3
"""
Usage:
    python -m 
"""

# pylint: disable=unspecified-encoding
import json
import logging
import os
import sys
import argparse
from datetime import datetime

import github as gh_api
import requests

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

def main():
    """
    Script entrypoint
    """
    # Configure information for the label you want to add/update
    name = "DEPR"
    color = "6140cf"
    description = "Mark for deprecation. See OEP-21"

    gh_headers = get_github_headers()

    for repo in get_repos(gh_headers):
        LOG.info("\n\n******* CHECKING REPO: {0} ************\n".format(repo))
        create_or_update_label(gh_headers, repo, name, color, description)

def get_repos(gh_headers):
    """ yields each repo name in the org """
    org_url = "https://api.github.com/orgs/openedx/repos"
    params = {"type": "public", "per_page": 100, "page": 1}
    response = requests.get(org_url, headers=gh_headers, params=params).json()
    while len(response) > 0:
        for repo_data in response:
            assert not repo_data['private']
            yield repo_data['name']
        params["page"] = params["page"] + 1
        response = requests.get(org_url, headers=gh_headers, params=params).json()


def create_or_update_label(gh_headers, repo, name, color, description):
    # URL for the Labels api (can read all labels and add a new one)
    labels_url = "https://api.github.com/repos/openedx/{0}/labels".format(repo)
    # URL for one specific label - can check if one is present, or update it
    single_label_url = "https://api.github.com/repos/openedx/{0}/labels/{1}".format(repo, name)
    #labels = requests.get(labels_url, headers=gh_headers).json() # to get all labels on a repo

    if requests.get(single_label_url).status_code == 200:
        LOG.info("Label {0} present on repo {1}, updating label".format(name, repo))
        r = requests.patch(
            single_label_url,
            headers=gh_headers,
            json={"color": color, "description": description}
        )
        assert r.status_code == 200, "Updating label failed"
        validate(r.json(), color, description)

    else:
        # Add the label
        LOG.info("Didn't find the label")
        r = requests.post(
            labels_url,
            headers=gh_headers,
            json={"name": name, "color": color, "description": description}
        )
        assert r.status_code == 201, "Failed to add the label"
        validate(r.json(), color, description, name)

    LOG.info("Success")


def validate(rjson, color, description, name=None):
    fail = False
    if name is not None and rjson['name'] != name:
        fail = True
    if rjson['color'] != color:
        fail = True
    if rjson['description'] != description:
        fail = True

    assert not fail, "Update failed, got: {}".format(rjson)


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


if __name__ == "__main__":
    main()