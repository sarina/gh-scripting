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
    repos = ["public_engineering"] #"paragon"
    for repo in repos:
        create_or_update_label(gh_headers, repo, name, color, description)

def create_or_update_label(gh_headers, repo, name, color, description):
    LOG.info("******* CHECKING REPO: {0} ************")
    labels_url = "https://api.github.com/repos/openedx/{0}/labels".format(repo)
    single_label_url = "https://api.github.com/repos/openedx/{0}/labels/{1}".format(repo, name)
    #labels = requests.get(labels_url, headers=gh_headers).json() # to get all labels on a repo

    # If the label is present, we just need to update the color & description
    if r == requests.get(single_label_url).status_code == 200:
        LOG.info("got 200 on the label check")
        r = requests.patch(
            single_label_url,
            headers=gh_headers,
            json={"color": color, "description": description}
        )
        assert r.status_code == 200
        validate(r.json(), color, description)

    else:
        LOG.info("Didn't find the label")
        r = requests.post(
            labels_url,
            headers=gh_headers,
            json={"name": name, "color": color, "description": description}
        )
        assert r.status_code == 201
        validate(r.json(), color, description, name)

def validate(rjson, color, description, name=None):
    if name is not None and rjson['name'] != name:
        LOG.info("Name was not created properly")
    if rjson['color'] != color:
        LOG.info("Color did not update properly")
    if rjson['description'] != description:
        LOG.info("Description did not update properly")


def get_github_headers() -> dict:
    """
    Load GH personal access token from file.
    """
    gh_token = os.environ["GITHUB_TOKEN"]
    LOG.info(" Authenticating.")
    gh_client = gh_api.Github(gh_token)
    LOG.info(" Authenticated.")

    # set up HTTP headers because PyGithub isn't able to determine team permissions on a repo in bulk.
    gh_headers = {"AUTHORIZATION": f"token {gh_token}"}
    return gh_headers

if __name__ == "__main__":
    main()