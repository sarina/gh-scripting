#!/usr/bin/env python3
"""
Used to parse the successfully-made PR URLs out of the log output when you
overwrote the success output file and only had the logs to go off of.
"""

import json

def main():
    pr_urls = []
    with open('output/output-file.txt') as f:
        lines = f.readlines()
        for l in lines:
            if "https" in l:
                pr_urls.append(l[l.index('https'):-1])

    with open('output/prs-file.json', 'w') as f:
        f.write(json.dumps(pr_urls))

if __name__ == "__main__":
    main()