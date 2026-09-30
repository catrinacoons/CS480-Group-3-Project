import zephyr_pydriller
import zephyr_github_api
import csv
import json

# this will use both pydriller and PyGithub files to create our results
# zephyr_pydriller: commits + stats -> commits.csv
# zephyr_github_api: issues/prs/comments -> threads.csv, comments.csv
# unique thread/comment authors -> rabbit_users.csv (RABBIT input)
# TODO: provenance.json to get settings and checkpoint counts
# TODO - run RABBIT and save rabbit.csv



def github_api():
# connect to GitHub and pull the repo needed
    initalize_repository = zephyr_github_api.authenticate_token()
# mine the commit data and save them to commits.csv
    rows = zephyr_github_api.commit_data(initalize_repository)
    zephyr_github_api.commits_csv(rows, "commits.csv")
# calculate the commit statistics and save them to results.json
    calculate = zephyr_github_api.calculate_results(rows)
    with open("results.json", "w", encoding="utf-8") as results:
        json.dump(calculate, results)
# build and save metadata to provenance.json
    build = zephyr_github_api.provenance_json()
    with open("provenance.json", "w", encoding="utf-8") as provenance:
        json.dump(build, provenance)
# print a statement letting you know it worked and finished
    print(f"Data mined has been found to be {calculate['num_commits']} commits.")
    return rows

# Reads commits.csv for rabbits_csv to prevent redundant remining
def rabbit_csv(rows, path="rabbit_users.csv"):
# "r" = read    "w" = write     "a" = append
# use "r" to read the commits file to prevent redundant information
# then write to its own csv file
# encoding="utf-8" makes sure that the author names with weird characters are correct
    with open(path, "r", newline="", encoding="utf-8") as csv_file:
# DictWriter changes each row to dictionary to ensure that it matches the columns required
# fieldname makes sure the columns are in the correct order
        return list(csv.DictReader(csv_file))


# TODO: define rabbit execution (or call it if defined in github_api)


def pydriller_step():
    commits = zephyr_pydriller.mine_commits()
    zephyr_github_api.commits_csv(commits, "commits.csv", zephyr_pydriller.PYDRILLER_COLUMNS)
    print(f"Commits found by PyDriller: {len(commits)}")
    return commits

def github_api_conversations():
    repo = zephyr_github_api.authenticate_token()
    threads = zephyr_github_api.thread_data(repo)
    comments = zephyr_github_api.comment_data(repo)
    zephyr_github_api.commits_csv(threads, "threads.csv", zephyr_github_api.THREAD_COLUMNS)
    zephyr_github_api.commits_csv(comments, "comments.csv", zephyr_github_api.COMMENT_COLUMNS)
    print(f"Threads: {len(threads)}, comments: {len(comments)}")
    return threads, comments

# TODO: Edit main to execute each of the functions above
def main():
    commits = pydriller_step()
    threads, comments = github_api_conversations()
    logins = sorted({r["author_login"] for r in threads + comments})
    zephyr_github_api.commits_csv([{"contributor_username": u} for u in logins],
                                  "rabbit_users.csv", ["contributor_username"])
    print(f"Unique authors for RABBIT: {len(logins)}")
    # TODO: run RABBIT on logins and save to rabbit.csv (using RABBIT_COLUMNS)
    
    #TODO: reuse existing provenance function, just add checkpoint counts



# ensure that main runs automatically
if __name__ == "__main__":
    main()
