#!/usr/bin/env python3
"""
Used to close prs you've got in a list in a json file somewhere

Just literally, a list of prs in the form `http://github.com/<org>/<repo>/pull/<num>
"""

# Better may have been: just iterate thru all your repos, search for any open
# PRs with the branch name that you've given the bulk prs, and closing that PR. Oh
# well fix that if you do it again. This would look like:

# gurl = "https://api.github.com/repos/openedx/{}/pulls".format(pr_json[1])
# getparams = {"head": "openedx:tcril/depr-automation-workflow"} # name of branch
# r = requests.get(gurl, headers=gh_headers, params=getparams).json()
# pr = r[0]['url'].replace("api.", "")
# pr = pr.replace("pulls/", "pull/")
# pr = pr.replace("repos/", "")

import argparse
import datetime
import json
import logging
import requests
import sys
import time

from github_helpers import get_github_headers

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

def main(path_to_file):
    stamp = str(datetime.datetime.now())[:19]
    path_to_failures = "/Users/sarinacanelake/openedx/gh-scripting/output/closed_failures_" + stamp + ".json"
    gh_headers = get_github_headers()
    prs_to_close = []
    failures = []
    params = {
        "commit_title": "Merge DEPR automation workflow"
    }
    rebase_params = {**params, **{"merge_method": "rebase"}}
    with open(path_to_file) as f:
        prs_to_close = json.load(f)
        for pr in prs_to_close:

            LOG.info("********* Closing: {}".format(pr))
            org, repo, number = parse_fields(pr)
            merge_url = "https://api.github.com/repos/{0}/{1}/pulls/{2}/merge".format(org, repo, number)
            response = requests.put(merge_url, headers=gh_headers, json=params)

            sc = response.status_code
            if sc == 200:
                LOG.info(" Merged - Success!\n")
            else:
                rjson = response.json()
                # If it says this, about half of the time it means you have to
                # rebase before merging. Two repos require squashing, the rest
                # require approvals. To keep it simple, let's only re-try w/ rebase.
                if rjson["message"] == "Merge commits are not allowed on this repository.":
                    response = requests.put(merge_url, headers=gh_headers, json=rebase_params)
                    sc = response.status_code
                    if sc == 200:
                        LOG.info(" Merged - Success!\n")
                        continue
                    rjson = response.json()
                LOG.info(" Failure - {}\n".format(sc))
                failures.append((pr, sc, rjson))

            time.sleep(2)

    numFail = len(failures)
    LOG.info(f" Writing {numFail} failures to: {path_to_failures}")
    with open(path_to_failures, 'w') as f:
        f.write(json.dumps(failures))


def parse_fields(pr):
    """
    given: https://github.com/<org>/<repo>/pull/<num>
    """
    fields = pr.split("/")
    org = fields[3]
    repo = fields[4]
    num = fields[-1]
    return (org, repo, num)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="closes each pr in a json list of prs"
    )

    parser.add_argument(
        "file",
        help="file to read from"
    )

    args = parser.parse_args()
    main(
        args.file
    )
