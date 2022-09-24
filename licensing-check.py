#!/usr/bin/env python3
"""
Usage: licensing-check.py [-h] [-P] org

  Creates a report of which repos have which licenses.

  positional arguments:
    org                   Name of the organization

  optional arguments:
    -h, --help            show this help message and exit
    -P, --exclude-private
                          Exclude private repos from this org

Requires:
    GITHUB_AUTH token in local environment    
"""

import argparse
import datetime
import json
import logging
import os
import sys

from ghelpers import *


LOG = logging.getLogger(__name__)

def main(org, exclude_private=False):
    """
    Script entrypoint
    """
    gh_headers = get_github_headers()
    count = 1
    ldata = {"no license": []}

    for rname, license_data in get_repos_plus_keys(gh_headers, org, exclude_private, ["license"]):
        if not count%5:
            LOG.info(f"******* CHECKING REPO: {rname} ({count}) ************")

        if license_data is None:
            ldata["no license"].append(rname)
            count += 1
            continue

        l_id = license_data["spdx_id"]
        if l_id  not in ldata:
            # Add the human-readable name as the first item
            lname = license_data["name"]
            ldata[l_id] = [lname]

        # Add the name of this repo to its appropriate ID list
        ldata[l_id].append(rname)
        count = count + 1

    ts = str(datetime.datetime.now())[:19]
    fname = f"output/license_check_{ts}.json"
    with open(fname, "w") as f:
        for license in ldata:
            num = len(ldata[license]) - 1
            f.write(f"Found {num} repos with license type {license}")
        f.write("\n\n\n")
        f.write(json.dumps(ldata, indent=4))

    LOG.info(f"Successfully checked licenses across {count} repos")
    LOG.info(f"Wrote output to {fname}")


if __name__ == "__main__":
    try:
        os.environ["GITHUB_TOKEN"]
    except KeyError:
        sys.exit("*** ERROR ***\nGITHUB_TOKEN must be defined in this environment")

    parser = argparse.ArgumentParser(
        description="Creates a report of which repos have which licenses."
    )

    parser.add_argument(
        "org",
        help="Name of the organization"
    )

    parser.add_argument(
        "-P", "--exclude-private",
        help="Exclude private repos from this org",
        action="store_true"
    )

    args = parser.parse_args()

    main(args.org, args.exclude_private)
