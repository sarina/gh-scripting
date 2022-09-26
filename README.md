# gh-scripting

just a dumb little collection of scripts i've found useful.

scripts require a GITHUB_AUTH token to be defined in the local environment

## helper functions

* `github_helpers.py`: Functions that help call the GitHub API or perform
  manipulation of local filesystem files using the `git` command

* `shell_helpers.py`: Functions that call local filesystem commands, such as
  `mv`, `cp`, and the base implementation of the `git` command

## general-use/could be kinda-useful for you?

* `licensing-check.py`: generates a json report of an org's repo's licenses

```
Usage: licensing-check.py [-h] [-P] org

  Creates a report of which repos have which licenses.

  positional arguments:
    org                   Name of the organization

  optional arguments:
    -h, --help            show this help message and exit
    -P, --exclude-private
                          Exclude private repos from this org
```

* `apply-labels.py`: for a given github organization, applies a label uniformly
  across all repos

```
❯ python -m  apply-labels.py -h
usage: apply-labels.py [-h] [-P] org name color description

Applies a specified label, with short description and color, to all repos in the specified organization - either adding the label if it's not already
there, or updating it to match the specification if it is.

positional arguments:
  org                   Name of the organization
  name                  What's the case-sensitive name of the label to add/update?
  color                 What's 6-character hex code (no #) corresponding to label color?
  description           Description of label (< 100 characters)

optional arguments:
  -h, --help            show this help message and exit
  -P, --exclude-private
                        Exclude private repos from this org
```


* `export-gh-issues.py`: Export GitHub issues from one or more repos to json or
  csv. Not working for repos with >30 issues.

```
> python -m export-gh-issues.py -h


usage: export-gh-issues.py [-h] [-r] [-l LABEL] filetype repos [repos ...]

Use this script to collect issues (that aren't PRs) from one or more openedx GitHub repos.
GitHub provides a large number of fields on an issue; by default, this script filters those
to a small number of useful ones. Use the raw flag to see all available fields. Optionally,
provide a label to get issues only with that label.

positional arguments:
  filetype              can be one of `json` or `csv`
  repos                 One or more openedx repos to grab issues from

optional arguments:
  -h, --help            show this help message and exit
  -r, --raw             If flagged, issues will be exported with all fields present.
  -l LABEL, --label LABEL
                        Only return GitHub issues with this label.
```

* `parse-pr-query.py`: returns a list of prs generated from a GH query over PRs

```
usage: parse-pr-query.py [-h] [-Q QUERY] [-B]

Takes a query over PRs and writes a json file that contains [repo_name,
pr_branch_name] for each PR result in the query. Probably will do funky
stuff if you don't include 'is:pr' in your query.

optional arguments:
  -h, --help            show this help message and exit

  -q QUERY, --query QUERY
                        GitHub query, as you'd do over in the UI. Example:
                          'is:pr author:YourUsername'. Defaults to Sarina's open
                          PRs over the openedx github org.

  -B, --branch-name     Adds the name of the branch the PR is being made from
                          (head ref) to the output list for the PR
```

* `bulk_merge_prs.py`: given a json list of PR urls, attempts to merge them. outputs
  a json list of failures.

* `checkout_all.py`: goes through a github org and checks out all its repos to a
  local directory. If the repo is already checked out, switches to the repo's
  default branch and pulls all upstream changes.

* `copy_file_to_repos.py`: Goes through all repos in an org, clones them, makes
    a new branch, copies specific files, commits them, creates a pull request,
    and merges the pull request. Requires viewing the file and changing a bunch
    of variables at the end of the file.

* `fetch_gh_request_limit.py`: shows how many requests you've got left.
  important: doesn't show secondary rate limit (which is not discoverable)

## more specific to problems i've been solving

You might be able to take inspiration from some of these scripts but you'll
definitely need to replace some hardcoded logic.

* `replace_string_with_another.py`: for each repo in your org, looks for a given
    string. If the string exists, switches to a new branch, replaces the string
    with a new string, commits changes, and opens a PR. Everything currently
    hard-coded, but would not be terribly difficult to make this one generic.

  * `replace_string_existing_branch.py`: Assumes you've run
    `replace_string_with_another`, thus repos already have your working branch
    defined, and you don't want to open a new set of PRs. Checks out existing
    branch (or re-creates if existing was already merged) and performs another
    string swap with the new strings, and makes a new commit.

    Many things hard-coded but as above, wouldn't be super hard to genericize.

  * `replace_string_run_edx_lint.py`: Basically, executes a command on every
    repo, on an existing branch. But this is a bit more specific - it first
    rolls back the previous commit, runs the command, then re-runs the original
    command. Description: For each repo in your org, first looks to see if one
    of the edx_lint files is present; if so, rolls back your branch, runs
    edx_lint, then re-runs the core logic to swap strings defined in
    `replace_string_with_another`.

    This could potentially be made more generic, but is so specific I can't
    imagine it's necessary.

* `add_depr_wkflw_issues.py`: non-generalized script to, for every repo in your org,
  copy a reference file onto a new branch and issue a pull request. Collects pull
  request URLs into an output json. Some associated files:

  * `parse_output.py`: parses log output from `add_depr_wkflw_issues` if needed.

  * `retry_failed_depr_wkflow_issues.py`: retries prs that failed to post correctly; takes
     in a set of info required to re-post them. Could probably be made more generic; this is
     good if you hit rate limits and have a list of ready-to-go branches that need PRs.

  * `revise_depr_wkflw_issues.py`: honestly not sure, this was made to correct
    some mistakes and is messy and undocumented. don't look at it.


