"""
Clones all public & private repos in your org.

If already cloned, switches to the default branch and pulls
  latest changes.
"""
import logging
import sys


from ghelpers import (
  clone_repo,
  get_github_headers,
  get_repos,
  get_repo_path
)

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

def clone_all(org, root_dir):
    gh_headers = get_github_headers()
    for repo_data in get_repos(gh_headers, org, False):
        (rname, ssh_url, dbranch, _, count) = repo_data
        LOG.info("\n\n******* CHECKING REPO: {} ({}) ************".format(rname, count))
        repo_path = get_repo_path(rname, root_dir)
        # clone repo; if exists, checkout the default branch & pull latest
        clone_repo(root_dir, repo_path, ssh_url, dbranch)

if __name__ == "__main__":
    root_dir = "/Users/sarinacanelake/openedx/"
    clone_all("openedx", root_dir)
