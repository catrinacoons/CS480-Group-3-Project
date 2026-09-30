import zephyr_pydriller
import zephyr_github_api
import csv
import json

# this will use both pydriller and PyGithub files to create our results

# TODO - set up json result file(s) (???)
#        - UPDATE: commit.csv exists in github_api and pydriller - rename or find a way to combine? 
#          - (RABBIT requires contributor usernames, initalization began in github_api)
#      - runs everything and writes to the following output files:
#        - commits.csv -- done in github_api AND pydriller (TODO: review above)
#        - results.json -- done in github_api
#        - provenance.json -- done in github_api
# TODO - define pydriller & rabbit execution; implement main


# TODO: define pydriller execution


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
def rabbit_csv(rows, path="commits.csv"):
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

# TODO: Edit main to execute each of the functions above
def main():
    commits = pydriller_step()
# ensure that main runs automatically
if __name__ == "__main__":
    main()
