import pandas as pd 
import statistics

from pydriller import Repository 
from datetime import datetime, timezone
from genai_signals import detect_genai

# make sure that you clone this repo and the zephyr repo under the same directory
zephyr_path = "../zephyr"
# then <git pull> and <git status> when in it to ensure you're up to date. 

from zephyr_github_api import START as startdate, END as enddate

# mines commits from local Zephyr clone and adds genai signal columns
def mine_commits():
	# print check for reassurance
	print("Starting PyDriller traversal (this may take a while) ...")
	commits = []


	for commit in Repository(zephyr_path, since=startdate, to=enddate).traverse_commits():

		if commit.merge:
			continue

		if commit.committer_date < startdate or commit.committer_date > enddate:
			continue

		# edit: this uses git's own stats instead of computing differences per file, this should be faster
		files_changed = commit.files
		additions = commit.insertions
		deletions = commit.deletions

		# review this and ensure it has all necessary info/no additional info
		# edit: PyDriller (v2) uses commit.modified_files, not commit.modifications (v1), so "modifications" was removed.
		commit_data = {
			"sha": commit.hash,
			"author_name": commit.author.name,
			"author_email": commit.author.email,
			"committer_date": commit.committer_date.isoformat(),
			"files_changed": files_changed,
			"additions": additions,
			"deletions": deletions,
			"message": commit.msg 
		}

		commit_data.update(detect_genai(commit.msg))
		commits.append(commit_data)

		# print checkpoint for reassurance
		if len(commits) % 500 == 0:
			print(f"  ...{len(commits)} commits processed (latest: {commit.committer_date.date()})")

	return commits


def summarize_commits(commits):
	all_authors = [] 
	files_changed_values = [] 
	additions_values = [] 
	deletions_values = []
	# update according to commit_data 
	for row in commits:
		all_authors.append(row["author_name"])
		files_changed_values.append(row["files_changed"])
		additions_values.append(row["additions"])
		deletions_values.append(row["deletions"])

	# edit: commits is the list, not commit_data
	num_commits = len(commits)
	num_authors = len(set(all_authors))
	total_additions = sum(additions_values)
	total_deletions = sum(deletions_values)

	pydriller_summary = {
		"num_commits": num_commits,
		"num_authors": num_authors,
		"total_additions": total_additions,
		"total_deletions": total_deletions,
	}
	return pydriller_summary

# setup for later file, will add completions later
PYDRILLER_COLUMNS = [
	"sha", "author_name", "author_email", "committer_date", "files_changed",
	"additions", "deletions", "message",
	"genai_candidate", "signal_types", "matched_text",
]