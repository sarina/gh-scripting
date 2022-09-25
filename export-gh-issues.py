#!/usr/bin/env python3
"""
Usage:
    python -m export-gh-issues.py -h
"""

import argparse
from datetime import datetime
import json
import logging
from pandas import json_normalize

import requests
import sys

from ghelpers import get_github_headers

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
LOG = logging.getLogger(__name__)


def main(filetype, raw, repos, label):
    """
    Script entrypoint
    """
    gh_headers = get_github_headers()

    stamp = datetime.utcnow().isoformat()[0:19]
    repo_names = ','.join(repos)
    export_filename = f"output-export/{stamp}-{repo_names}.{filetype}"

    is_csv = filetype == 'csv'
    get_and_filter_issues(repos, gh_headers, export_filename, raw, label=label, csv=is_csv)


def get_and_filter_issues(all_repos, gh_headers, export_filename, raw, label=None, csv=False):
    """
    Get all issues that are not PRs from the specified repo.
    * export_filename: the name of the file you'd like your data exported to
    * raw: if True, returns all json fields. Otherwise returns a pre-determined filtered list.
    * label: only return issues with the given label.
    * csv: if True, returns a flattened CSV instead of a json; without filtering, this may not work.
    """
    all_issues = []
    for repo in all_repos:
        LOG.info("grabbing repo {0}".format(repo))
        url = "https://api.github.com/repos/openedx/{repo}/issues".format(repo=repo)
        all_issues = all_issues + requests.get(url, headers=gh_headers).json()

    saved_issues = []

    # Variables needed for doing hard-coded filtering of the issue to only the specified fields
    # Keys with single values: "key" : "value"
    keys_to_save = ["url", "number", "title", "body", "created_at", "updated_at"]
    # Keys that have keys nested in a dict: "key": { {nkey: value}, {nkey2: value} }
    nested_keyvalues = [{"user": "login"}]

    # Keys that follow with a list of dicts: "key": [{nkey: value}, {nkey2: value}]
    listed_keyvalues = [{"labels": "name"}, {"assignees": "login"}]

    for issue in all_issues:
        # all prs are issues, but not all issues are prs. grab just the issues        
        if 'pull_request' in issue:
            continue

        # replace api url with github url
        issue['url'] = issue['url'].replace('api.', '')
        issue['url'] = issue['url'].replace('repos/', '')

        # Filter out issues that don't have the given label, but return all issues in the Decoupling project
        if label and "decoupling" not in issue["url"]:
            # filter on those with only the label
            # issues have a key `label` with a list of multiple labels of the form:
            # "label": [ {"name": "label1name"}, {"name": "label2name"} ]
            # note the inner dicts have, in addition to name, keys: id, node_id, url, color, default, description
            match = [1 for item in issue["labels"] if item['name']==label] != []
            if not match:
                continue

        if not raw:
            # Extract the fields we need
            new_issue = {}
            for k in keys_to_save:
                v = issue[k]
                new_issue[k] = v

            for keypair in nested_keyvalues:
                k1 = [*keypair][0]
                k2 = keypair[k1]
                v = issue[k1][k2]
                # Flattening the tree for CSV conversion
                if csv:
                    new_issue["{k1}-{k2}".format(k1=k1, k2=k2)] = v
                else:
                    new_issue[k1] = {}
                    new_issue[k1][k2] = v

            for keypair in listed_keyvalues:
                k1 = [*keypair][0]
                k2 = keypair[k1]
                
                for k1dict in issue[k1]:
                    v = k1dict[k2]
                    if csv:
                        # flattening for csv conversion
                        dkey = "{k1}-{k2}".format(k1=k1, k2=k2)
                        if dkey not in new_issue:
                            new_issue[dkey] = []
                        new_issue[dkey].append(v)
                    else:
                        if k1 not in new_issue:
                            new_issue[k1] = []
                        new_issue[k1].append({k2: v})
                        
            # once new_issue is built out at end of "filtered" section, rename it for following line
            issue = new_issue
        # Append the edited issue to the list of issues we're saving
        saved_issues.append(issue)
    if csv:
        issue_dataframe = json_normalize(saved_issues)
        issue_dataframe.to_csv(export_filename, index=False)

    else:
        with open(export_filename, "a") as export_file:
            print(json.dumps(saved_issues, indent=4), file=export_file)

    LOG.info("Successfully wrote issues to: {0}".format(export_filename))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Use this script to collect issues (that aren't PRs) from one or more openedx GitHub repos.\
                     GitHub provides a large number of fields on an issue; by default, this script filters those to\
                     a small number of useful ones. Use the raw flag to see all available fields.\
                     Optionally, provide a label to get issues only with that label.")

    parser.add_argument('filetype',
                        help="can be one of `json` or `csv`",
                        default='export_filtered')

    parser.add_argument('-r', '--raw',
                        help="If flagged, issues will be exported with all fields present.",
                        action='store_true')

    parser.add_argument('repos',
                        help="One or more openedx repos to grab issues from",
                        nargs='+')

    parser.add_argument('-l', '--label',
                        help='Only return GitHub issues with this label.')


    args = parser.parse_args()

    # validation
    if args.filetype not in ['csv', 'json']:
        sys.exit("Filetype must be one of: `csv`, `json`")

    # raw output is untested with raw option... but allow people to try anyway
    if args.raw and args.filetype == 'csv':
        LOG.warning('filetype=csv and -r option unsupported')
        proceed = input("Raw output is untested with CSV option (json nesting level may be too deep). Proceed anyway? [y/n]: ")
        if proceed != 'y':
            LOG.info('Exiting program, not proceeding with raw output/csv')
            sys.exit()

    main(args.filetype, args.raw, args.repos, args.label)
