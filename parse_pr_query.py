"""
usage: parse-pr-query.py [-h] [-Q QUERY] [-B]

Takes a query over PRs and writes a json file that contains [pr_url, repo_name]
for each PR result in the query. Probably will do funky stuff if you don't
include 'is:pr' in your query.

optional arguments:
  -h, --help            show this help message and exit

  -q QUERY, --query QUERY
                        GitHub query, as you'd do over in the UI. Example:
                          'is:pr author:YourUsername'. Defaults to Sarina's open
                          PRs over the openedx github org.

  -B, --branch-name     Adds the name of the branch the PR is being made from
                          (head ref) to the output list for the PR
"""
import argparse
import datetime
import json
import os
import requests
import sys

from github_helpers import (
    get_github_headers,
    gh_search_query
)

def parse_prs(search_query=False, branch_name=False, foutput=False):
    """
    Returns a list of lists, each interior list as [pr_url, repo_name] for each
    pr given from the search_query, which must contain `is:pr` as part of the
    query. Default search query is 'author:sarina is:pr is:open org:openedx'

    If `branch_name` is set, the branch_name that the PR was made from is also
    added to the PR list.

    If `foutput` is set (implicitly set if called from the command line),
    insteads writes the output to a json file in the `output/` directory.
    """
    if not search_query:
        search_query = 'author:sarina is:pr is:open org:openedx'

    print(f"Sending search query: '{search_query}'")
    gh_headers = get_github_headers()
    data = gh_search_query(gh_headers, search_query)
    print(f"\nProcessing {len(data)} PRs from search query\n")

    count = 1
    get_pr_url = "https://api.github.com/repos/openedx/{0}/pulls/{1}"

    overall_output = []

    for pr_blob in data:
        if not count%10:
            print(f"processing pr #{count}")
        pr_url = pr_blob["url"]
        # Only if you need clickable URLs
        pr_url = pr_url.replace("api.git", "git")
        pr_number = pr_url.split("/")[-1]
        repo_name = pr_blob["repository_url"].split("/")[-1]

        result = [pr_url, repo_name]
        if branch_name:
            response = requests.get(
                get_pr_url.format(repo_name, pr_number),
                headers=gh_headers
            )
            branch_name = response.json()["head"]["ref"]
            result.append(branch_name)

        overall_output.append(result)
        count += 1

    if foutput:
        ts = str(datetime.datetime.now())[:19]
        f2 = f"output/pr_parse_{ts}"
        with open(f2, "w") as f:
            f.write(json.dumps(overall_output, indent=4))
        print(f"Output of {count-1} PRs written to {f2}")
        return

    return overall_output
    

if __name__ == "__main__":
    try:
        os.environ["GITHUB_TOKEN"]
    except KeyError:
        sys.exit("*** ERROR ***\nGITHUB_TOKEN must be defined in this environment")

    parser = argparse.ArgumentParser(
        description="Takes a query over PRs and writes a json file that contains [pr_url, repo_name] for each PR result in the query. Probably will do funky stuff if you don't include 'is:pr' in your query."
    )

    parser.add_argument(
        "-q", "--query",
        help="GitHub query, as you'd do over in the UI. Example: 'is:pr author:YourUsername'. Defaults to Sarina's open PRs over the openedx github org.",
        default="author:sarina is:pr is:open org:openedx"
    )

    parser.add_argument(
        "-B", "--branch-name",
        help="Adds the name of the branch the PR is being made from (head ref) to the output list for the PR",
        action="store_true"
    )

    args = parser.parse_args()
    parse_prs(args.query, args.branch_name, foutput=True)

