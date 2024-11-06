all_commits = """
{
    repository(owner: "%s", name: "%s") {
        defaultBranchRef {
            target {
                ... on Commit {
                    history(first: 100%s) {
                        edges {
                            node {
                                author {
                                    name
                                    email
                                }
                                additions
                                deletions
                                changedFilesIfAvailable
                                committedDate
                                message
                                oid
                            }
                        }
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                    }
                }
            }
        }
    }
}
"""

all_issues = """
{
  repository(owner: "%s", name: "%s") {
    issues(first: 100%s) {
      edges {
        node {
          title
          labels(first: 100) {
            edges {
              node {
                name
              }
            }
            totalCount
          }
          createdAt
          closedAt
          state
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""
