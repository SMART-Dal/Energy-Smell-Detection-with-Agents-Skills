The function under test calls `_check_comments` and `_check_reviews`, which both call network functions (`_get_repo_commenters` uses REST, `_check_reviews` uses GraphQL). These need network access. So the function cannot run here.

Actually wait — `_get_repo_commenters` makes a request. So yes, network access required. CANNOT RUN.