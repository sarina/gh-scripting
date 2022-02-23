#!/usr/bin/env python3
"""
Usage:
    python -m add-depr-wkflw-issues.py

Requires:
    GITHUB_AUTH token in local environment

Description:
    Transfers reference workflow template to all repos in the org. Additionally,
    if the org doesn't have issues enabled, transfers a reference issue template
    and issue configuration (if issues are enabled, inheriting a more open
    reference issue template set will suffice).
"""

import json
import logging
import os
import requests
import subprocess
import sys
import time

from ghelpers import get_github_headers


# Switch to DEBUG for additional debugging info
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

def main(org, root_dir, exclude_private=False, interactive=False):
    """
    Goes through all repos in an org, clones them, makes a new branch, copies
    specific files, commits them, creates a pull request, and merges the pull
    request.

    * org (str): GitHub organization
    * root_dir (str): path to directory to clone repos (on Mac, may look like
      `/Users/<uname>/path/to/dir`
    * exclude_private (bool): if True, script skips private repos (default
      False)
    * interactive (bool): if True, pauses before committing files upstream and
      awaits user confirmation
    """
    gh_headers = get_github_headers()
    branch_name = "tcril/depr-automation-workflow"
    workflow_template_name = "add-depr-ticket-to-depr-board.yml"
    issue_template_name = "depr-ticket.yml"
    commit_msg_wkflow_only = "build: add DEPR workflow automation"
    pr_details_wkflow_only = {
        "title": "Add DEPR workflow automation",
        "body": "## This PR was autogenerated\n\n## This PR will be automerged\n\nThis pr introduces workflow automation which allows us to put DEPR tickets from this repo onto the global DEPR project board. It also notifies the `#depr-slash-n-burn` Slack room when new issues are created."
    }

    commit_msg_with_issue = commit_msg_wkflow_only + " & default issue overrides"
    pr_details_with_issue = {
        "title": pr_details_wkflow_only["title"] + " & default issue overrides",
        "body": pr_details_wkflow_only["body"] + "\n\nSince this repo currently does not have Issues enabled, a special override configuration has been added to turn off all issue types except DEPR tickets. This will allow us to turn on Issues in this repo without opening the gates for other types of reports."
    }

    prs = []
    pr_failed = []
    repos_skipped = []

    for repo_data in get_repos(gh_headers, org, exclude_private):
        (rname, ssh_url, dbranch, has_issues, count) = repo_data
        LOG.info("\n\n******* CHECKING REPO: {} ({}) ************".format(rname, count))

        repo_path = get_repo_path(rname, root_dir)
        # clone repo; if exists, checkout the default branch & pull latest
        clone_repo(root_dir, repo_path, ssh_url, dbranch)
        if issue_config_exists(repo_path):
            # Some repos may already configure issues, so don't overwrite
            LOG.info("Skipping {} (don't want to overwrite config.yml)".format(rname))
            repos_skipped.append([rname, "config exists"])
            continue
        if not new_branch(repo_path, branch_name):
            # this branch already exists
            LOG.info("Skipping {}, branch already exists".format(rname))
            repos_skipped.append([rname, "branch exists"])
            continue

        add_files(
            root_dir,
            repo_path,
            workflow_template_name,
            has_issues,
            issue_template_name
        )
        if interactive:
            try:
                interactive_commit(repo_path)
            except RepoError:
                # move on to next repo
                continue

        # If the repo has issues only committing the workflow, otherwise also
        # committing the issue template and configuration
        commit_msg = commit_msg_wkflow_only if has_issues else commit_msg_with_issue
        pr_details = pr_details_wkflow_only if has_issues else pr_details_with_issue

        make_commit(repo_path, commit_msg)
        try:
            pr_url = make_pr(gh_headers, org, rname, branch_name, dbranch, pr_details)
            prs.append(pr_url)
        except PrCreationError as pr_err:
            LOG.info(pr_err.__str__())
            # info you need to retry
            pr_failed.append((org, rname, branch_name, dbranch, pr_details))
        # Without, you hit secondary rate limits if you have more than ~30
        # repos. I tried 3, too short. 30, totally worked. there's a good number
        # in between that i'm sure
        time.sleep(5)

    LOG.info(
        "Processed {} repos; see output/prs.json ({}) and output/failed.json ({})".format(
            count, len(prs), len(pr_failed)
        )
    )
    LOG.info("Skipped these repos as branch was already defined: {}".format(repos_skipped))
    with open("output/prs.json", "w") as f:
        f.write(json.dumps(prs))

    with open("output/failed.json", "w") as f2:
        f2.write(json.dumps(pr_failed))


def get_repos(gh_headers, org, exclude_private):
    """
    Generator
    Yields a 4-tuple of repo data:
    - repo name (str)
    - ssh url (str)
    - default branch name (str)
    - has issues (boolean)
    """
    org_url = "https://api.github.com/orgs/{0}/repos".format(org)
    params = {"page": 1}
    if exclude_private:
        params["type"] = "public"
    count = 0
    response = requests.get(org_url, headers=gh_headers, params=params).json()
    while len(response) > 0:
       for repo_data in response:
           count += 1
           yield (
               repo_data['name'],
               repo_data['ssh_url'],
               repo_data['default_branch'],
               repo_data['has_issues'],
               count
           )
       params["page"] = params["page"] + 1
       response = requests.get(org_url, headers=gh_headers, params=params).json()


def clone_repo(root_dir, repo_path, ssh_url, default_branch):
    """
    If not already cloned into root_dir, clones repo at that location. If
    cloned, switches to the repo's default_branch and pulls down the latest
    changes.
    """
    path_exists = os.path.exists(repo_path)

    if not path_exists:
        git("clone", [ssh_url], root_dir)

    else:
        git("checkout", [default_branch], repo_path)
        git("pull", [], repo_path)


def issue_config_exists(repo_path):
    """
    returns True if the issue template config.yml file exists in the repo_path
    """
    path_to_config = repo_path + "/.github/ISSUE_TEMPLATE/config.yml"
    return os.path.exists(path_to_config)

def new_branch(repo_path, branch_name):
    """
    Creates and pushes to remote a new branch called branch_name
    """
    _, err = git("checkout", ["-b", branch_name], repo_path)
    branch_error = "fatal: A branch named '{}' already exists.".format(branch_name)
    if branch_error in str(err):
        return False

    git("push", ["-u", "origin", branch_name], repo_path)
    return True


def add_files(root_dir, repo_path, wtemplate_name, has_issues, itemplate_name):
    """
    For the given repo (represented by the repo_path) which resides in the
    root_dir, copies a workflow template from the root_dir/.github/workflow-templates
    directory into repo_path/.github/workflow-templates.

    If the repo does not have issues enabled, copies
    root_dir/override_config.yml and root_dir/.github/ISSUE_TEMPLATE/itemplate_name
    into repo_path/.github/ISSUE_TEMPLATE/config.yml and itemplate_name, respectively
    """
    mkdir(repo_path, ".github")
    mkdir(repo_path, ".github/workflows")

    dot_github_path = get_repo_path('.github', root_dir)
    workflow_template_path = dot_github_path + '/workflow-templates/' + wtemplate_name
    workflow_destination_path = repo_path + '/.github/workflows'
    cp(repo_path, workflow_template_path, workflow_destination_path)

    if not has_issues:
        # if issues aren't enabled on this repo yet, we copy over the DEPR
        # template as well as a config file to turn on the DEPR template
        mkdir(repo_path, ".github/ISSUE_TEMPLATE")
        issue_template_path = dot_github_path + "/.github/ISSUE_TEMPLATE/" + itemplate_name
        cp(repo_path, issue_template_path, ".github/ISSUE_TEMPLATE")
        cp(repo_path, "../override_config.yml", ".github/ISSUE_TEMPLATE/config.yml")

def make_commit(repo_path, commit_msg):
    """
    Commits every new file & change in the repo, with the given commit_msg
    """
    git("add", ["."], repo_path)
    git(
        "commit",
        ["-a", "-m", commit_msg],
        repo_path
    )
    git("push", [], repo_path)

def make_pr(gh_headers, org, rname, branch_name, dbranch, pr_details):
    """
    in the given org & repo, create a pr from specified branch into the default
    branch with the supplied title and/or body.

    pr_details (dict): specify the title and/or body of the pull request using
    the keys "title" and "body". Optional; can supply an empty dict.
    """
    post_url = "https://api.github.com/repos/{0}/{1}/pulls".format(org, rname)
    params = {
        "head": branch_name,
        "base": dbranch
    }
    params.update(pr_details)
    response = requests.post(post_url, headers=gh_headers, json=params)
    if response.status_code != 201:
        raise PrCreationError(response.status_code, response.json())

    pr_url = response.json()["html_url"]
    LOG.info("PR success: {}".format(pr_url))
    return pr_url

def mkdir(working_dir, dir_name):
    p1 = subprocess.Popen(
        ["/bin/mkdir", dir_name],
        cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _ = p1.communicate()

def cp(working_dir, filepath, dest_path):
    p1 = subprocess.Popen(
        ["cp", filepath, dest_path],
        cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _ = p1.communicate()


def git(command, args, cwd):
    array = ["/opt/homebrew/bin/git", command]
    array.extend(args)
    p1 = subprocess.Popen(
        array,
        cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out = p1.communicate()
    return out

def get_repo_path(repo, root_dir):
    if not root_dir.endswith('/'):
        root_dir = root_dir + '/'
    return root_dir + repo

class RepoError(Exception):
    pass


class PrCreationError(Exception):
    def __init__(self, status_code, rjson):
        self.status_code = status_code
        self.rjson = rjson

    def __str__(self):
        error_string = "Problem creating pull request."
        error_string += "\nGot status code: {}".format(self.status_code)
        error_string += "\nJSON: {}".format(self.rjson)
        return error_string

def interactive_commit(repo_path):
    # don't call the `git` method because we always want this to go to stdout
    p1 = subprocess.Popen(
        ["/opt/homebrew/bin/git", "status"],
        cwd=repo_path
    )
    _ = p1.communicate()

    cmd = input("Push changes? Y/N: ")
    while cmd.lower() not in ["y", "n"]:
        cmd = input("Push changes? Y/N: ")
    if cmd.lower() == 'n':
        cmd2 = input("Press Q to quit program, other inputs will continue to next repo: ")
        if cmd2.lower() == "q":
            raise KeyboardInterrupt
        raise RepoError


if __name__ == "__main__":
    root_dir = "/Users/sarinacanelake/openedx/"
    main("openedx", root_dir, True, False)