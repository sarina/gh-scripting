## Finding the node ID of the decoupling project (login-org, number=project number)

gh api graphql -f query='
  query{
    organization(login: "openedx"){
      projectNext(number: 8) {
	   id
      }
    }
  }'
