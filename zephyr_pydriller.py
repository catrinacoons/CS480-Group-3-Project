import pandas as pd 

from pydriller import Repository 
from datetime import datetime, timezone

zephyr_path = "../zephyr" # make sure that you clone this repo and the zephyr repo under the same directory

startdate = datetime(2022, 9, 21, tzinfo=timezone.utc)
enddate = datetime(2026, 9, 21, tzinfo=timezone.utc)

commits = {}

for commit in Repository(zephyr_path, since=startdate, to=enddate):
	commit_data = {
		"author": commit.author.name,
		"hash": commit.hash,
		"email": commit.author.email,
		"date": commit.committer_date,
		"message": commit.msg
	}

	commits.append(commit_data)
