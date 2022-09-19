#!/usr/bin/env python3
"""
Usage:
    python -m copy_file_to_repos.py

Requires:
    GITHUB_AUTH token in local environment

Description:
    Copies a given file to all repos in an `org`
"""

import datetime
import logging
import sys
import time

from ghelpers import *


# Switch to DEBUG for additional debugging info
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

def main(
        org, root_dir, branch_name, src_file_path,
        dest_file_path, commit_msg, pr_body,
        exclude_private=False, interactive=False,
        select_repos=None, commit_on_existing=False
    ):
    """
    Goes through all repos in an org, clones them, makes a new branch, copies
    specific files, commits them, creates a pull request, and merges the pull
    request.

    * org (str): GitHub organization
    * root_dir (str): path to directory to clone repos (on Mac, may look like
      `/Users/<uname>/path/to/dir`
    * branch_name (str): name of branch to be created
    * src_file_path (str): fully-qualified path of source file
    * dest_file_path (str): relative (to repo) path where it should go
    * commit_msg (str): what you want on the commit (will also be the
      title of the pull request)
    * pr_body (str): body message of the PR
    * exclude_private (bool): optional; if True, script skips private repos (default
      False)
    * interactive (bool): optional; if True, pauses before committing files upstream and
      awaits user confirmation
    * select_repos (list): optional; if set, only these repos will be processed
    * commit_on_existing (bool): if True, will commit on an already-created branch of
      name `branch_name`. Default behavior is to skip repos with `branch_name` defined. If True, a new PR will not be made.
    """
    gh_headers = get_github_headers()
    pr_details = {
        "title": commit_msg,
        "body": pr_body
    }

    count_commits = 0
    count_skipped = 0
    count_failed = 0

    ts = str(datetime.datetime.now())[:19]
    filename = f"output/copy_file_{ts}.json"
    with open(filename, "w") as f:
        for repo_data in get_repos(gh_headers, org, exclude_private):
            (rname, ssh_url, dbranch, _, count) = repo_data
            LOG.info("\n\n******* CHECKING REPO: {} ({}) ************".format(rname, count))
            if select_repos and rname not in select_repos:
                LOG.info(f"Skipping repo {rname}")
                count_skipped += 1
                f.write(f"NOT ON LIST: {rname}\n")
                continue

            repo_path = get_repo_path(rname, root_dir)
            # clone repo; if exists, checkout the default branch & pull latest
            clone_repo(root_dir, repo_path, ssh_url, dbranch)
 
            if not commit_on_existing and not new_branch(repo_path, branch_name):
                # this branch already exists
                LOG.info(f"Skipping {rname}, branch already exists")
                f.write(f"BRANCH EXISTS: {rname}")
                count_skipped += 1
                continue

            add_files(
                root_dir,
                repo_path,
                src_file_path,
                dest_file_path
            )
            if interactive:
                try:
                    interactive_commit(repo_path)
                except RepoError:
                    # move on to next repo
                    continue

            make_commit(repo_path, commit_msg)
            if commit_on_existing:
                # If we're committing on an existing branch, assume we are
                # updating the branches and don't need a new PR
                time.sleep(5)
                continue

            try:
                pr_url = make_pr(gh_headers, org, rname, branch_name, dbranch, pr_details)
                f.write(f"SUCCESS: {rname}\nPR: {pr_url}")
                LOG.info(f"Successfully made {pr_url}")
                count_commits += 1
            except PrCreationError as pr_err:
                LOG.info(pr_err.__str__())
                # info you need to retry
                LOG.info(f"Failed on {rname} with {pr_err}")
                f.write(f"FAILED: ({org}, {rname}, {branch_name}, {dbranch}, {pr_details})")
                count_failed += 1
            # Without, you hit secondary rate limits if you have more than ~30
            # repos. I tried 3, too short. 30, totally worked. there's a good number
            # in between that i'm sure
            time.sleep(5)

    LOG.info(
        f"Processed {count} repos; {count_commits} successes, {count_skipped} skipped, {count_failed} failures\n\nFull output logged in {filename}"
    )


def add_files(root_dir, repo_path, src_file_path, dest_file_path):
    """
    For the given repo (represented by the repo_path) which resides in the
    root_dir, copies a file represented by src_file_path (fully qualified)
    to the dest_file_path (relative to repo_path).

    If the repo does not have any directories in dest_file_path defined, they
    will be created.
    """
    # Make sure that all parts of the dest path exist - mkdir has no side
    # effects if the dirs already exist
    dirs = dest_file_path.split("/")
    for dir in dirs[:-1]:
        mkdir(repo_path, dir)

    if not root_dir.endswith('/'):
        root_dir = root_dir + '/'
    full_dest_path = repo_path + dest_file_path

    cp(repo_path, src_file_path, full_dest_path)


if __name__ == "__main__":

    org = "openedx"
    root_dir = "/Users/sarinacanelake/openedx/"
    branch_name = ''
    src_file_path = ''
    dest_file_path = ''
    commit_msg = ''
    pr_body = ''

    main(
        org,
        root_dir,
        branch_name,
        src_file_path,
        dest_file_path,
        commit_msg,
        pr_body,
        exclude_private=False,
        interactive=False,
        select_repos=None,
        commit_on_existing=False
    )
