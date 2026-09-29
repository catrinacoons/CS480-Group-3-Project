import pandas as pd 
import statistics

from pydriller import Repository 
from datetime import datetime, timezone

# make sure that you clone this repo and the zephyr repo under the same directory
zephyr_path = "cd../zephyr"
# then <git pull> and <git status> when in it to ensure you're up to date. 

startdate = datetime(2022, 9, 21, tzinfo=timezone.utc)
enddate = datetime(2026, 9, 21, tzinfo=timezone.utc)

# below is code copied from assignment 1 -- if some of this does not work with our assignment, feel free to take it out!
commits = []
all_authors = [] 
files_changed_values = [] 
additions_values = [] 
deletions_values = []

for commit in Repository(zephyr_path, since=startdate, to=enddate).traverse_commits():

	if commit.merge:
		continue

	if commit.committer_date < startdate or commit.committer_date > enddate:
		continue

	files_changed = len(commit.modified_files)
	
	additions = 0
	deletions = 0

	for i in commit.modified_files:
		if i.added_lines is not None:
			additions += i.added_lines
		if i.deleted_lines is not None:
			deletions += i.deleted_lines

	# review this and ensure it has all necessary info/no additional info
	# edit: PyDriller (v2) uses commit.modified_files, not commit.modifications (v1), so "modifications" was removed.
	commit_data = {
		"sha": commit.hash,
		"author_name": commit.author.name,
		"committer_date": commit.committer_date.isoformat(),
		"files_changed": files_changed,
		"additions": additions,
		"deletions": deletions,
		"message": commit.msg 
	}

	commits.append(commit_data)

# update according to commit_data 
for row in commits:
	all_authors.append(row["author_name"])
	files_changed_values.append(row["files_changed"])
	additions_values.append(row["additions"])
	deletions_values.append(row["deletions"])

# edit: commits is the list, not commit_data
num_commits = len(commits)
num_authors = len(set(all_authors))
median_files_changed = statistics.median(files_changed_values)
total_additions = sum(additions_values)
total_deletions = sum(deletions_values)

pydriller_summary = {
	"num_commits": num_commits,
    "num_authors": num_authors,
    "median_files_changed": median_files_changed,
    "total_additions": total_additions,
    "total_deletions": total_deletions,
}
