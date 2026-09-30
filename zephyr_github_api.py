import pandas as pd
import re
import requests
# general imports - API implementations from Adelle's Data Mining Assignment #1 because she used the Github API
import sys
import csv
import json
import os
import platform
import statistics
import argparse
from datetime import datetime, timezone, timedelta
# For setup, look at README.txt
from github import Github, Auth

from dotenv import load_dotenv
load_dotenv()

# TODO: May have to update function names in this if errors occur in mining.py (due to duplicate function names)
# TODO: AI tag search (for tag in zephyr repo)
# TODO: See above and other # TODOs below - thank you! :)

# parameters for mining
REPOSITORY = "zephyrproject-rtos/zephyr"
TAG = "main" 
START_UTC_STR = "2022-09-21T00:00:00Z"
END_UTC_STR = "2026-09-21T00:00:00Z"
# timezone = tz
START = datetime(2022, 9, 21, 0, 0, 0, tzinfo=timezone.utc)
END = datetime(2026, 9, 21, 0, 0, 0, tzinfo=timezone.utc)


# parameters for csv - RABBIT needs the contributor's username
CSV_COLUMNS = [
    "sha",
    "author_name",
    "contributor_user", #TODO: define this in commit_data
    "committer_date",
    "files_changed",
    "additions",
    "deletions",
]

#TODO: Add more columns as needed for RABBIT's data
RABBIT_COLUMNS = [
    "contributor_username", 
    "confidence"
]

# return true if a commit's timezone is within the tz parameters set
def time_parameters(commit_datetime):
    return START <= commit_datetime <= END


# review any new changes to file commits
def updated_stats(commit_file):
# initalize to 0 to set a default
    file_edits = 0
    additions = 0
    deletions = 0
# increment as necessary based on changes and return those
    for files_changed in commit_file.files:
        file_edits += 1
        additions += files_changed.additions
        deletions += files_changed.deletions
    return file_edits, additions, deletions

# build the commit data, identifying merges and anything out of date
def commit_data(mined_data):
# initalize the data and rows
    offset_start = START - timedelta(days=1)
    offset_end = END + timedelta(days=1)
    rows = []
# pull commits from GitHub within the offset range
    data_found = mined_data.get_commits(sha=TAG, since=offset_start, until=offset_end)

    for commit in data_found:
# skip merge commits if there's more than 1 parent
        if len(commit.parents) > 1:
            continue
# pull the commit date, not the author date
        commit_datetime = commit.commit.committer.date.replace(tzinfo=timezone.utc)
# skip anything outside of the datetime window
        if not time_parameters(commit_datetime):
            continue
# pull the statistics for the file and/or line changes for the commit
        file_edits, additions, deletions = updated_stats(commit)
# add this commit's data as one row each then return it
        rows.append({
            "sha": commit.sha,
            "author_name" : commit.commit.author.name,
# TODO: define "contributor_user" so RABBIT pulls a list of usernames
            "committer_date" : commit_datetime.isoformat(),
            "files_changed" : file_edits,
            "additions" : additions,
            "deletions" : deletions,
        })
    return rows


# saves the commit list to commits.csv
def commits_csv(rows, path="commits.csv", columns=CSV_COLUMNS):
# "r" = read    "w" = write     "a" = append
# use "w" to overwrite the file upon each run to ensure that it's updated each time
# encoding="utf-8" makes sure that the author names with weird characters are correct
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
# DictWriter changes each row to dictionary to ensure that it matches the columns required
# fieldname makes sure the columns are in the correct order
        writer = csv.DictWriter(csv_file, fieldnames=columns)
# writes the header rows (column names) as the first line
# then writes the dictionary in one line rows per commit 
        writer.writeheader()
        writer.writerows(rows)

#TODO: Define rabbit_csv to iterate through every unique GitHub username and save results to rabbit.csv

# calculates the summary numbers for results.json
def calculate_results(rows):
# return the correct camel-case for each json
    return {
        "num_commits": len(rows),
        "num_authors": len({row["author_name"] for row in rows}),
        "median_files_changed": statistics.median(row["files_changed"] for row in rows), 
        "total_additions": sum(row["additions"] for row in rows),
        "total_deletions": sum(row["deletions"] for row in rows),
    }


# builds the metadata for provenance.json 
def provenance_json():
# return the correct camel-case for each json
    return {
        "repository": REPOSITORY,
        "tag": TAG,
        "start_utc": START_UTC_STR,
        "end_utc": END_UTC_STR,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "GitHub REST API with PyGithub",
    }


# authenticates using Github's REST API and pulls the Zephyr repo
def authenticate_token():
# reads the token from the hidden environment (so it's not hardcoded)
# recommended by GTA
    token = os.environ["GITHUB_TOKEN"]
# authenticate from GitHub
    authenticate = Auth.Token(token)
    ensure_authentication = Github(auth=authenticate)
    return ensure_authentication.get_repo(REPOSITORY)