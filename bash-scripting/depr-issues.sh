# get repo info (api)

# if not cloned:
# clone repo

# else
git checkout master
git pull

# for both
git checkout -b add-depr-issue; git push -u origin add-depr-issue

mkdir .github
mkdir .github/workflows
cp ../.github/workflow-templates/add-depr-ticket-to-depr-board.yml .github/workflows

# only if repo doesn't have issues enabled:
mkdir .github/ISSUE_TEMPLATE
cp ../.github/.github/ISSUE_TEMPLATE/depr-ticket.yml .github/ISSUE_TEMPLATE
cp ../override_config.yml .github/ISSUE_TEMPLATE

# if verbose
git status
git diff
read -p "Press any key to continue... " -n1 -s

# add and commit
git add .
git commit -a -m "build: add depr automation & default issue overrides"

# can be done w api call:
git push
gh pr create --fill
