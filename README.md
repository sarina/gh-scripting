# gh-scripting

just a dumb little collection of scripts i've found useful.

* apply-labels.py: for a given github organization, applies a label uniformly
  across all repos

* bash-scripting: bash scripts to automate bulk github actions

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

