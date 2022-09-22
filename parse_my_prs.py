"""
Takes a json output of open prs and writes a file
that contains [repo_name, pr_branch_name]

This is in order to return to open PRs and update them.

Find the json file at a url like this:
https://api.github.com/search/issues?q=is:pr+org:openedx+author:sarina+is:open
(only gives 1 page of results, further research to use the search API)
"""
import datetime
import json
import requests
from ghelpers import get_github_headers

def parse_prs(filename):
    f = open(filename)
    data = json.load(f)
    gh_headers = get_github_headers()

    ts = str(datetime.datetime.now())[:19]
    f2 = f"output/pr_parse_{ts}"
    count = 0
    # get repos/{owner}/{repo}/pulls/{pull_number}
    get_pr_url = "https://api.github.com/repos/openedx/{0}/pulls/{1}"
    with open(f2, "w") as f:
        for pr_blob in data["items"]:
            # in form: "https://api.github.com/repos/openedx/blockstore/issues/203"
            pr_url = pr_blob["url"]
            # Only if you need clickable URLs
            pr_url = pr_url.replace("api.git", "git")
            pr_number = pr_url.split("/")[-1]
            repo_name = pr_blob["repository_url"].split("/")[-1]

            response = requests.get(
                get_pr_url.format(repo_name, pr_number),
                headers=gh_headers
            )
            branch_name = response.json()["head"]["ref"]

            # In order to update existing PR, need to be able to checkout the branch
            f.write(f"[{pr_url}, {repo_name}, {branch_name}]\n")
            count += 1

    print(f"Output of {count} PRs written to {f2}")
    

if __name__ == "__main__":
    # https://api.github.com/search/issues?q=is:pr+org:openedx+author:sarina+is:open
    parse_prs("inputs/my_prs_0922.txt")

