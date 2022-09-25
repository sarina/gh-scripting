#!/usr/bin/env python3
"""
Usage:
    python -m apply_label.py

Requires:
    GITHUB_AUTH token in local environment

Description:
    Applies a specified label, with color and description, to every
    repo in a given github org

Future Work:
    Remove asserts and do inscript retry &/or dump the failed repos
"""

import logging
import os
import sys
import argparse
import requests

from github_helpers import (
    get_github_headers,
    get_repos_plus_keys
)

# Switch to DEBUG for additional debugging info
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

def main(org, name, color, description, exclude_private=False):
    """
    Script entrypoint
    """
    gh_headers = get_github_headers()

    count = 1
    for repo in get_repos_plus_keys(gh_headers, org, exclude_private):
        LOG.info("\n\n******* CHECKING REPO: {repo} ({count}) ************\n")
        create_or_update_label(gh_headers, org, repo, name, color, description)
        count = count + 1
    LOG.info("Successfully standardised label {name} across {count} repos")


def create_or_update_label(gh_headers, org, repo, name, color, description):
    """
    Looks for the label; if it's present, updates it with the specified color &
    description.
    If it's not present, creates it with specified color & description.
    """
    # URL for the Labels api (can read all labels and add a new one)
    labels_url = "https://api.github.com/repos/{0}/{1}/labels".format(org, repo)
    # URL for one specific label - can check if one is present, or update it
    single_label_url = "https://api.github.com/repos/{0}/{1}/labels/{2}".format(org, repo, name)

    action = None
    # If label is present, 200; if not, 404
    label_present_r = requests.get(single_label_url, headers=gh_headers)

    if label_present_r.status_code == 200:
        LOG.debug("Label {0} present on repo {1}, updating label".format(name, repo))
        r = requests.patch(
            single_label_url,
            headers=gh_headers,
            json={"color": color, "description": description}
        )
        assert r.status_code == 200, "Updating label failed with {}".format(r.status_code)
        validate(r.json(), color, description)
        action = "updated"

    else:
        # Add the label
        LOG.debug("Didn't find the label")
        r = requests.post(
            labels_url,
            headers=gh_headers,
            json={"name": name, "color": color, "description": description}
        )
        assert r.status_code == 201, "Adding label failed with {}".format(r.status_code)
        validate(r.json(), color, description, name)
        action = "added"

    LOG.info("Success: {} label".format(action))


def validate(rjson, color, description, name=None):
    fail = False
    if name is not None and rjson['name'] != name:
        fail = True
    if rjson['color'] != color:
        fail = True
    if rjson['description'] != description:
        fail = True

    assert not fail, "Creation or update failed, got: {}".format(rjson)


if __name__ == "__main__":
    try:
        os.environ["GITHUB_TOKEN"]
    except KeyError:
        sys.exit("*** ERROR ***\nGITHUB_TOKEN must be defined in this environment")

    parser = argparse.ArgumentParser(
        description="Applies a specified label, with short description and\
            color, to all repos in the specified organization - either adding\
            the label if it's not already there, or updating it to match the\
            specification if it is."
    )

    parser.add_argument(
        "org",
        help="Name of the organization"
    )

    parser.add_argument(
        "name",
        help="What's the case-sensitive name of the label to add/update?"
    )

    parser.add_argument(
        "color",
        help="What's 6-character hex code (no #) corresponding to label color?"
    )

    parser.add_argument(
        "description",
        help="Description of label (< 100 characters)"
    )

    parser.add_argument(
        "-P", "--exclude-private",
        help="Exclude private repos from this org",
        action="store_true"
    )

    args = parser.parse_args()

    main(args.org, args.name, args.color, args.description, args.exclude_private)
