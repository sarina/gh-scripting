#!/usr/bin/env python3
"""
    Takes the failed PR posts from add_depr_wkflw_issues and retries them.
    Currently assumes that cloning, branching, file copy, commit, and push all
    succeeded, so this script simply retries making the PRs.
"""
import json
import logging
import sys
import time

from ghelpers import get_github_headers
from add_depr_wkflw_issues import (
    make_pr, git, get_repo_path, PrCreationError
)

# Switch to DEBUG for additional debugging info
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)


def main(path_to_failed_json, repo_root):
    """
    path_to_failed_json must be a fully qualified path to the file
      (ex: /Users/<uname>/gh-scripting/output/failed.json) that has data on prs
      that failed to be executed correctly, each entry being a 5-tuple of:
      (org, repo name, branch name, default branch name, dict that has one,
      both, or none of the keys "title" and "body" of the PR)
    repo_root must be a fully qualified path to the folder that holds the repo
    directories (ex: Users/<uname>/openedx)
    """
    gh_headers = get_github_headers()

    # Read in the output file
    f = open(path_to_failed_json)
    failed_repos = json.load(f)
    prs = []
    pr_failed = []
    count = 1
    for repo_data in failed_repos:
        (org, rname, branch_name, dbranch, pr_details) = repo_data
        LOG.info("\n\n******* CHECKING REPO: {} ({}) ************".format(rname, count))
        repo_path = get_repo_path(rname, repo_root)
        LOG.info("Got repo path {}".format(repo_path))
        # check out branch_name
        git("checkout", [branch_name], repo_path)
        try:
            pr_url = make_pr(gh_headers, org, rname, branch_name, dbranch, pr_details)
            prs.append(pr_url)
        except PrCreationError as pr_err:
            LOG.info(pr_err)
            # info you need to retry
            pr_failed.append([org, rname, branch_name, dbranch, pr_details]) 

        count += 1
        # sleep so we don't anger the secondary rate limit god
        time.sleep(5)

    with open("output/prs.json", "w") as f:
        f.write(json.dumps(prs))

    with open("output/failed.json", "w") as f2:
        f2.write(json.dumps(pr_failed))

if __name__ == "__main__":
    main(
        "/Users/sarinacanelake/openedx/gh-scripting/output/23Feb1700-failed.json",
        "/Users/sarinacanelake/openedx"
    )
