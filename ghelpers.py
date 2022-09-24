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
    Yields a 5-tuple of repo data:
    - repo name (str)
    - ssh url (str)
    - default branch name (str)
    - has issues (boolean)
    - count (running count of number of repos given)

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


def get_repos_plus_keys(gh_headers, org, exclude_private, keys=None):
    """
    Generator
    Yields each repo's name in the org, plus optional additional data

    keys: list. Will also yield the data for the key(s) provided, in an ordered
      list of [repo_name, key1_result, key2_result, ...].
      Keys are strings that represent a data element you can grab from a github
      `repo` data struct (see the data response samples at
      https://docs.github.com/en/rest/repos/repos)
    """
    org_url = "https://api.github.com/orgs/{0}/repos".format(org)
    params = {"page": 1}
    if exclude_private:
        params["type"] = "public"
    response = requests.get(org_url, headers=gh_headers, params=params).json()
    while len(response) > 0:
        for repo_data in response:
            result = [repo_data['name']]
            if keys:
                for key in keys:
                    result.append(repo_data[key])
            yield result
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

    Returns False if branch_name already exists
    """
    _, err = git("checkout", ["-b", branch_name], repo_path)
    err = err.decode('utf-8')
    branch_error = f"fatal: a branch named '{branch_name}' already exists"
    if branch_error in err:
        return False

    git("push", ["-u", "origin", branch_name], repo_path)
    return True

def checkout(repo_path, branch_name):
    git("checkout", [branch_name], repo_path)

def checkout_branch(repo_path, branch_name):
    """
    Tries to check out existing branch, branch_name

    Returns False if branch_name does not exist
    """
    _, err = git("checkout", [branch_name], repo_path)
    err = err.decode('utf-8')
    branch_error = f"error: pathspec '{branch_name}' did not match any file(s) known to git"
    if branch_error in err:
        return False
    return True


def make_commit(repo_path, commit_msg, force=False):
    """
    Commits every new file & change in the repo, with the given commit_msg,
    and pushes to origin

    if `force` is True, will execute a force-push of the commits.
    """
    git("add", ["."], repo_path)
    git(
        "commit",
        ["-a", "-m", commit_msg],
        repo_path
    )
    if force:
        git("push", ["-f"], repo_path)
    else:
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
    if not repo.endswith('/'):
        repo = repo + '/'
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


def git_reset(num_commits, repo_path):
    """
    Does "git reset --hard HEAD~{num_commits}
    """
    # For the life of me I cannot figure out why using git() wasn't working -
    # it was not passing through the "--" on the "--hard" arg. :shrug:
    proc = subprocess.Popen(
        f"git reset --hard HEAD~{num_commits}",
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    out = proc.communicate()
    return out
