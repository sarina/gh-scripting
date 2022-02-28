# gh-scripting

just a dumb little collection of scripts i've found useful.

* ghelpers.py: github helper functions

* apply-labels.py: for a given github organization, applies a label uniformly
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

* export-gh-issues.py: Export GitHub issues to json or csv. One day
  will script over beta projects (when the API is ready).

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

  * Useful GitHub fields

    * As mentioned above, by default the script filters the raw GitHub-returned json to a small number of what I deem are useful fields. These are: "url", "\
number", "title", "body", "created_at", "updated_at", "user" (github username).

    * Additionally, the following two fields are returned as nested json (if json output is chosen) or as a flattened list (if csv output is chosen): "label\
s" and "assignees"

    * See "sample-output/" folder for some sample outputs.

* add_depr_wkflw_issues.py: non-generalized script to, for every repo in your org,
  copy a reference file onto a new branch and issue a pull request. Collects pull
  request URLs into an output json.

* bulk_merge_prs.py: given a json list of PR urls, attempts to merge them. outputs
  a json list of failures.

* parse_output.py: parses log output from add_depr_wkflw_issues if needed.

* retry_failed_depr_wkflow_issues.py: self-explanatory