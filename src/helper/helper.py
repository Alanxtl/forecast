import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, f'../crawler'))

import graphql

def get_first_commit_date(owner_name, repo_name):
    """获取指定仓库的第一个提交日期."""
    # 初始查询模板
    query_template = """
    {
        repository(owner: "%s", name: "%s") {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 100%s) {
                            edges {
                                node {
                                    committedDate
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


    cursor = None
    first_commit_date = None

    while True:
        # 构建查询
        if ( cursor is None ):
            tem_cursor = ""
        else:
            tem_cursor = ", after: \"" + cursor + "\""

        query_string = query_template % (owner_name, repo_name, tem_cursor)

        # 执行查询
        response = graphql.query(query_string)

        # 解析响应
        edges = response["data"]["repository"]["defaultBranchRef"]["target"]["history"]["edges"]
        page_info = response["data"]["repository"]["defaultBranchRef"]["target"]["history"]["pageInfo"]

        if edges:
            # 获取当前提交的日期
            first_commit_date = edges[-1]["node"]["committedDate"]

        # 检查是否还有下一页
        if not page_info["hasNextPage"]:
            break

        # 更新游标进行下一次查询
        cursor = page_info["endCursor"]
        # print("cursor: ", first_commit_date)

    return first_commit_date[0: 10], first_commit_date[11: -1]


if __name__ == "__main__":
    print(get_first_commit_date("XS-MLVP", "env-xs-ov-00-bpu"))
