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

developer_s_all_issues = """
{
  search(query: "author:%s", type: ISSUE, first: 100%s) {
    edges {
      node {
        ... on PullRequest {
          title
          createdAt
          number
          repository {
            nameWithOwner
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""