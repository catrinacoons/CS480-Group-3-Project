import zephyr_pydriller
import zephyr_github_api
# import zephyr_build_dataset
import csv
import json
import sys

# this will use both pydriller and PyGithub files to create our results
# zephyr_pydriller: commits + stats -> commits.csv
# zephyr_github_api: issues/prs/comments -> threads.csv, comments.csv
# unique thread/comment authors -> rabbit_users.csv (RABBIT input)
# TODO: provenance.json to get settings and checkpoint counts
# DONE - run RABBIT and save rabbit.csv

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

# RABBIT execution which gathers everyone who authored a thread / comment and passes it
# into rabbit_results_csv() in zephyr_github_api, which saves to rabbit.csv for the results
def rabbit_gathering(): 
    rows = []
        # zephyr_github_api: issues/prs/comments -> threads.csv, comments.csv
    for path in ("threads.csv", "comments.csv"):
        try:
            with open(path, "r", newline="", encoding="utf-8") as csv_file:
                rows += list(csv.DictReader(csv_file))
        # error out if threads.csv and comments.csv aren't working
        except FileNotFoundError:
            print(f"RABBIT: {path} not found, create threads.csv and comments.csv first")
        # users will run RABBIT and save the results to rabbit.csv
    users = zephyr_github_api.rabbit_results_csv(rows, "rabbit.csv")
    print("RABBIT has finished running and results have been saved to rabbit.csv")
    return users

def pydriller_step():
    commits = zephyr_pydriller.mine_commits()
    zephyr_github_api.commits_csv(commits, "commits.csv", zephyr_pydriller.PYDRILLER_COLUMNS)
    print(f"Commits found by PyDriller: {len(commits)}")
    return commits



# TODO: Edit main to execute each of the functions above
def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    counts = {}

    if stage in ("commits", "all"):
        commits = pydriller_step()
        counts["commits"] = len(commits)

    if stage in ("threads", "all"):
        client = zephyr_github_api.authenticate_client()      
        threads = zephyr_github_api.thread_data(client)
        zephyr_github_api.commits_csv(threads, "threads.csv", zephyr_github_api.THREAD_COLUMNS)
        print(f"Threads saved: {len(threads)}")
        counts["threads"] = len(threads)

    if stage in ("comments", "all"):
        repo = zephyr_github_api.authenticate_token()
        comments = zephyr_github_api.comment_data(repo)
        zephyr_github_api.commits_csv(comments, "comments.csv", zephyr_github_api.COMMENT_COLUMNS)
        print(f"Comments saved: {len(comments)}")
        counts["comments"] = len(comments)

	if stage in ("rabbit", "all"):
		users = rabbit_gathering()
		print(f"Unique usernames checked by RABBIT: {len(users)}")
		counts["rabbit_users"] = len(users)
		
    if stage in ("links", "all"):
        repo = zephyr_github_api.authenticate_token()
        with open("commits.csv", newline="", encoding="utf-8") as f:
            flagged = [r["sha"] for r in csv.DictReader(f) if r["genai_candidate"] == "True"]
        links = zephyr_github_api.find_prs_for_commits(repo, flagged)
        zephyr_github_api.commits_csv(links, "commit_pr_links.csv", ["sha", "pr_number"])
        print(f"Flagged commits: {len(flagged)}, links: {len(links)}")
        counts["links"] = len(links)
	
    build = zephyr_github_api.provenance_json(counts)
    with open("provenance.json", "w", encoding="utf-8") as provenance:
        json.dump(build, provenance)

# ensure that main runs automatically
if __name__ == "__main__":
    main()
