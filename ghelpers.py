#!/usr/bin/env python3
"""
github helpers
"""

import logging
import os
import subprocess
import sys

import github as gh_api
import requests

# Switch to DEBUG for additional debugging info
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)

def get_repo_names(gh_headers, org, exclude_private):
    """
    Generator
    Yields each repo'- name in the org
    """
    org_url = "https://api.github.com/orgs/{0}/repos".format(org)
    params = {"page": 1}
    if exclude_private:
        params["type"] = "public"
    response = requests.get(org_url, headers=gh_headers, params=params).json()
    while len(response) > 0:
        for repo_data in response:
            assert not repo_data['private']
            yield repo_data['name']
        params["page"] = params["page"] + 1
        response = requests.get(org_url, headers=gh_headers, params=params).json()


def get_github_headers() -> dict:
    """
    Load GH personal access token from file.
    """
    gh_token = os.environ["GITHUB_TOKEN"]
    LOG.info(" Authenticating.")
    gh_client = gh_api.Github(gh_token)
    LOG.info(" Authenticated.")

    gh_headers = {"AUTHORIZATION": f"token {gh_token}"}
    return gh_headers


def get_repos(gh_headers, org, exclude_private):
    """
    Generator that iterates over all repos in `org`
    Yields a 4-tuple of repo data:
    - repo name (str)
    - ssh url (str)
    - default branch name (str)
    - has issues (boolean)

    * exclude_private (bool): if True, excludes private repos
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


def git(command, args, cwd):
    """
    Executes a Git command.
    * command: string
    * args: list of command line arguments
    * cwd: string, which working dir to execute the command in
    """
    array = ["/opt/homebrew/bin/git", command]
    array.extend(args)
    p1 = subprocess.Popen(
        array,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out = p1.communicate()
    return out

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


def new_branch(repo_path, branch_name):
    """
    Creates and pushes to remote a new branch called branch_name
    """
    _, err = git("checkout", ["-b", branch_name], repo_path)
    err = err.decode('utf-8')
    branch_error = f"fatal: a branch named '{branch_name}' already exists"
    if branch_error in err:
        return False

    git("push", ["-u", "origin", branch_name], repo_path)
    return True


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
    """
    Runs `git diff` then waits for user input about whether or not to push changes
    """
    # don't call the `git` method because we always want this to go to stdout
    p1 = subprocess.Popen(
        ["/opt/homebrew/bin/git", "diff"],
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
