"""
what limit do i have left
"""
import json
import requests

from ghelpers import get_github_headers

gh_headers = get_github_headers()
response = requests.get('https://api.github.com/rate_limit', headers=gh_headers)

print(json.dumps(response.json(), indent=3, sort_keys=True))
