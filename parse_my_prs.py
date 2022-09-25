"""
Takes a json output of a query over PRs and writes a file
that contains [repo_name, pr_branch_name]

This is in order to return to open PRs and update them.
"""
import datetime
import json
import requests
from ghelpers import (
    get_github_headers,
    gh_search_query
)

def parse_prs(search_query, branch_name=False):
    gh_headers = get_github_headers()
    data = gh_search_query(gh_headers, search_query)
    print(f"Processing {len(data)} PRs from search query")

    ts = str(datetime.datetime.now())[:19]
    f2 = f"output/pr_parse_{ts}"
    count = 1
    get_pr_url = "https://api.github.com/repos/openedx/{0}/pulls/{1}"

    overall_output = []

    for pr_blob in data:
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

    with open(f2, "w") as f:
        f.write(json.dumps(overall_output, indent=4))
    print(f"Output of {count-1} PRs written to {f2}")
    

if __name__ == "__main__":
    
    parse_prs("author:sarina is:pr is:open org:openedx")

