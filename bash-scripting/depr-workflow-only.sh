git checkout -b add-depr-issue; git push -u origin add-depr-issue

mkdir .github
mkdir .github/workflows
cp ../.github/workflow-templates/add-depr-ticket-to-depr-board.yml .github/workflows

git status
git diff

read -p "Press any key to continue... " -n1 -s

git add .
git commit -a -m "build: add depr automation"
git push
gh pr create --fill
