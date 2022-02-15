git checkout -b add-depr-issue; git push -u origin add-depr-issue

mkdir .github
mkdir .github/workflows
mkdir .github/ISSUE_TEMPLATE
cp ../.github/.github/ISSUE_TEMPLATE/depr-ticket.yml .github/ISSUE_TEMPLATE
cp ../override_config.yml .github/ISSUE_TEMPLATE
cp ../.github/workflow-templates/add-depr-ticket-to-depr-board.yml .github/workflows

git status
git diff

read -p "Press any key to continue... " -n1 -s

git add .
git commit -a -m "build: add depr automation & default issue overrides"
git push
gh pr create --fill
