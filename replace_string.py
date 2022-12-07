#!/usr/bin/env python3
"""
Usage:
    python -m replace_string.py Arguments defined at end of file (for now)

Requires:
    GITHUB_AUTH token in local environment

Description:
    Fundamentally, replaces a string with another string. It can do this for all
    repos on a github org, or specified repos. It can create the swap on a new
    branch or on a repo's existing branch; it can generate a new PR or not. You
    can specify an arbitrary number of swap pairs.

    Outputs a json file of: successful PRs made, repos where PRs were failed to
    be made, and repos with existing branches that were updated.

Notes:
    There is a small amount of hardcoded functionality and variable definitions
    at the end of the file, in the `__main__` section. It may be difficult to
    make this script fully generic, but this is pretty close.

    `swap_strings` (in shell_helpers.py) has hardcoded shell commands that are
    wonky due to OSX. If you're not on OSX you should examine and change them.
"""

import datetime
import json
import logging
import sys
import time

from github_helpers import *
from parse_pr_query import parse_prs
from shell_helpers import *

### TODO ###
"""
1. Figure out what argument options are needed to:
  - specify all org vs read from repo list
  - allow arbitrary string pairs
  - new branch vs existing branch
  - make PRs or not
2. Fix up `__main__` to pull in parse-pr-query results
"""



# Switch to DEBUG for additional debugging info
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

def main(
        org_or_query,  # is either a string `org_name` or a PR query (see parse-pr-query.py)
        string_pairs,  # a list of pairs (old_string, new_string, commit_msg)
        branch_name,  # if opening a new branch, else None
        pr_details,  # when opening the pr. dict of {"title": "title text", "body": "body_text"} or None if not creating a PR
        root_dir,
        exclude_private=False,
        interactive=False
    ):
    """
    Goes through all repos in an org, clones them (or switches to the default
    branch and then pulls latest changes), searches for the specified string, if
    found makes a new branch, switches the string with the new string, creates a
    pull request.

    * org (str): GitHub organization
    * root_dir (str): path to directory to clone repos (on Mac, may look like
      `/Users/<uname>/path/to/dir`
    * old_string: what string we're looking to see if each repo has
    * new_string: if old_string is found, what we should replace it with
    * exclude_private (bool): if True, script skips private repos (default
      False)
    * interactive (bool): if True, pauses before committing files upstream and
      awaits user confirmation
    """
    gh_headers = get_github_headers()

    summary = {
        "commits": 0,    # number of commits made (intentionally not making a PR)
        "pr_success": 0, # number of PRs made
        "pr_failure": 0, # number of PRs that had a failure to create
        "skipped": 0     # number of repos we skipped
    }
    overall_output = {}

    if "is:pr" in org_or_query:
        LOG.info(f" Found pr query: {org_or_query}")
        # repo name, ssh_url, default branch, _, count
        loop_iterator = parse_prs(org_or_query) # TODO fix this return value
        
    else:
        LOG.info(f" Found org: {org_or_query}")
        loop_iterator = get_repos(gh_headers, org_or_query, exclude_private)

    try:
        for repo_data in loop_iterator:
            (rname, ssh_url, dbranch, _, count) = repo_data
            single_output = []
            LOG.info("\n\n******* CHECKING REPO: {} ({}) ************".format(rname, count))
            repo_path = get_repo_path(rname, root_dir)

            # clone repo; if exists, checkout the default branch & pull latest
            clone_repo(root_dir, repo_path, ssh_url, dbranch)

            # # TODO: Figure out how to handle new branches vs existing ones
            # # Checkout the already-existing branch_name -- maybe a new arg
            # branch_created = False
            # if not checkout_branch(repo_path, branch_name):
            #     # this branch was never created, or already merged, so
            #     # create it for the new commit
            #     new_branch(repo_path, branch_name)
            #     branch_created = True

            # Go thru and s/old string/new string/g in the repo, then make a commit.
            # If multiple swaps, does one commit for each swap.
            for (old_string, new_string, commit_msg) in string_pairs:
                # Search for the string; fail fast if none exist
                if not found(old_string, repo_path):
                    LOG.info(" Did not find string {}".format(old_string))
                    summary["skipped"] += 1
                    single_output.append(f"Did not find string {old_string}")
                    continue

                # Swap old string for new string
                swap_strings(old_string, new_string, repo_path)

                if interactive:
                    try:
                        interactive_commit(repo_path)
                    except RepoError:
                        # move on to next repo
                        continue

                make_commit(repo_path, commit_msg)
                single_output.append(f"CREATED: {commit_msg}\n")

            if pr_details:
                try:
                    LOG.info(f" Making a pull request")
                    pr_url = make_pr(gh_headers, org, rname, branch_name, dbranch, pr_details)
                    single_output.append(f"  PR: {pr_url}\n")
                    summary["pr_success"] += 1
                except PrCreationError as pr_err:
                    LOG.info(pr_err.__str__())
                    # info you need to retry
                    single_output.append(
                        f"FAIL REPO INFO: {org}, {rname}, {branch_name}, {dbranch}, {pr_details}\n"
                    )
                    summary["pr_failure"] += 1

                time.sleep(5)
            else:
                LOG.info(f"  committed to branch with no PR")
                summary["commits"] += 1

            overall_output["rname"] = single_output

    except KeyboardInterrupt:
        LOG.info(" Received interrupt, cancelling out")

    finally:
        ts = str(datetime.datetime.now())[:19]
        filename = f"output/replace_existing_branch_{ts}.json"
        with open(filename, "w") as f:
            f.write(json.dumps(overall_output, indent=4))
        print(f"Output of {count-1} repos written to {filename}")
        LOG.info(
            f" Processed {count} repos; PRs successfully made and {summary['pr_failure']} failures occurred when making PRs."
        )
        LOG.info(f"  {summary['commits']} commits created on existing branches.")
        LOG.info(f"  Skipped {summary['skipped']} repos")


if __name__ == "__main__":
    # is either a string `org_name` or a PR query (see parse-pr-query.py)
    org_or_query =  "author:sarina is:pr is:open org:openedx" #"openedx"

    # a list of pairs (old_string, new_string, commit_msg)
    string_pairs = [
        ("uses: edx/.github", "uses: openedx/.github", "fix: update path to .github workflows to read from openedx org")
    ]

    # if opening a new branch or recommitting on existing branch. Put "None" if providing pr_data lists
    branch_name = "tcril/fix-gh-org-url"

    # when opening the pr. dict of {"title": "title text", "body": "body_text"}
    #  or None if not creating a PR
    pr_details = {
        "title": "Fix github url strings in .github workflows",
        "body": "## This PR was autogenerated\n\nThis pr replaces the old GitHub organization, github.com/edx, with the new GitHub organization, github.com/openedx, in .github/workflow files.\n\nLooking for people to provide review.\n\nRef: https://github.com/openedx/tcril-engineering/issues/42"
    }

    # Where to clone new repos & where existing repos exist
    root_dir = "/Users/sarinacanelake/openedx/"


    main(
        org_or_query, string_pairs,
        branch_name, pr_details, root_dir,
        exclude_private=False, interactive=False
    )
