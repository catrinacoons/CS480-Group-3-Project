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
import time
from datetime import datetime, timezone, timedelta
# For setup, look at README.txt
from github import Github, Auth

from dotenv import load_dotenv
from genai_signals import detect_genai
load_dotenv()

csv.field_size_limit(2**31 - 1)

# TODO: May have to update function names in this if errors occur in mining.py (due to duplicate function names)

# DONE: AI tag search lives in negai_signals (detect_genai)
# TODO: See above and other # TODOs below - thank you! :)

# parameters for mining
REPOSITORY = "zephyrproject-rtos/zephyr"
TAG = "main" 

# timezone = tz
START = datetime(2022, 9, 21, 0, 0, 0, tzinfo=timezone.utc)
END = datetime(2026, 9, 21, 0, 0, 0, tzinfo=timezone.utc)
START_UTC_STR = START.strftime("%Y-%m-%dT%H:%M:%SZ")
END_UTC_STR = END.strftime("%Y-%m-%dT%H:%M:%SZ")

# parameters for csv - RABBIT needs the contributor's username
# legacy commit columns (commits are mined by zephyr_pydriller.py )
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

THREAD_COLUMNS = [
    "number", "kind", "title", "author_login", "author_type", "created_at",
    "state", "labels", "comment_count", "body",
    "genai_candidate", "signal_types", "matched_text", "html_url", "closed_at", 
    "merged_at", "author_association",
]
COMMENT_COLUMNS = [
    "thread_number", "comment_id", "comment_type", "author_login", "author_type",
    "created_at", "body", "genai_candidate", "signal_types", "matched_text",
    "html_url", "author_association", "in_reply_to_id", "path",
]

# deleted accounts come back as None, this is to handle that
def user_info(user):
    if user is None:
        return "ghost", "Deleted"
    return user.login, user.type

# building the issue/PR data (the issues endpoint returns both)
# reworked time window collection for thread data
def thread_data(client):
    rows = []
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    window_start = START
    while window_start < END:
        window_end = min(window_start + timedelta(days=7), END)
        query_end = window_end - timedelta(seconds=1)
        query = f"repo:{REPOSITORY} created:{window_start.strftime(fmt)}..{query_end.strftime(fmt)}"
        results = client.search_issues(query, sort="created", order="asc")
        if results.totalCount >= 1000:
            print(f"  WARNING: {window_start.date()} window has {results.totalCount} results, search caps at 1000")
        for issue in results:
            login, account_type = user_info(issue.user)
            row = {
                "number": issue.number,
                "kind": "pull_request" if issue.pull_request else "issue",
                "title": issue.title,
                "author_login": login,
                "author_type": account_type,
                "created_at": issue.created_at.isoformat(),
                "state": issue.state,
                "labels": ";".join(label.name for label in issue.labels),
                "comment_count": issue.comments,
                "body": issue.body or "",
                "html_url": issue.html_url,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else "",
                "merged_at": str(getattr(issue.pull_request, "merged_at", "") or "") if issue.pull_request else "",
                "author_association": issue.author_association,
            }
            row.update(detect_genai(f"{issue.title}\n{issue.body or ''}"))
            rows.append(row)
        print(f"... threads through {window_end.date()}: {len(rows)} so far")
        window_start = window_end
        time.sleep(2.5)
    return rows

# build one row per comment
def comment_row(comment, thread_number, comment_type):
    login, account_type = user_info(comment.user)
    row = {
        "thread_number": thread_number,
        "comment_id": comment.id,
        "comment_type": comment_type,
        "author_login": login,
        "author_type": account_type,
        "created_at": comment.created_at.isoformat(),
        "body": comment.body or "",
        "html_url": comment.html_url,
        "author_association": comment.author_association,
        "in_reply_to_id": getattr(comment, "in_reply_to_id", "") or "",
        "path": getattr(comment, "path", "") or "",
    }
    row.update(detect_genai(comment.body))
    return row

# pull all issue/PR comments and inline review comments across the repo 
# edit: fetches one kind of comment, and if GitHub errors out mid-pagination it waits and
# edit: finds what is already saved for this comment type so a rerun resumes instead of restarting
def last_saved(path, comment_type):
    latest, seen = START, set()
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["comment_type"] == comment_type:
                    seen.add(r["comment_id"])
                    t = datetime.fromisoformat(r["created_at"])
                    if t > latest:
                        latest = t
    return latest, seen

# edit: writes each comment to the CSV as it arrives; on repeated errors it waits, shrinks the
# page size, and finally stops with all progress saved (just rerun the stage to continue)
def fetch_comments(make_client, method_name, url_attr, comment_type, path):
    since, seen = last_saved(path, comment_type)
    if seen:
        print(f"  resuming {comment_type}s from {since} ({len(seen)} already saved)")
    new_file = not os.path.exists(path)
    per_page, failures, saved = 100, 0, 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COMMENT_COLUMNS)
        if new_file:
            writer.writeheader()
        while True:
            repo = make_client(per_page).get_repo(REPOSITORY)
            try:
                for c in getattr(repo, method_name)(sort="created", direction="asc", since=since):
                    if c.created_at > END:
                        return saved
                    if str(c.id) in seen or not time_parameters(c.created_at):
                        continue
                    seen.add(str(c.id))
                    writer.writerow(comment_row(c, int(getattr(c, url_attr).rsplit("/", 1)[1]), comment_type))
                    saved += 1
                    since = c.created_at
                    failures = 0
                    if saved % 100 == 0:      # one page: save to disk and pace the requests
                        f.flush()
                        time.sleep(1)
                    if saved % 500 == 0:
                        print(f"  ...{saved} new {comment_type}s (at {since.date()})")
                return saved
            except Exception as e:
                f.flush()
                failures += 1
                if failures == 3:
                    per_page = 20             # smaller pages are less likely to time out
                    print("  switching to 20 per page")
                if failures > 8:
                    print(f"  giving up at {since}. Progress is saved; rerun this stage later to resume.")
                    raise
                wait = 30 * failures
                print(f"  GitHub error ({type(e).__name__}); retry {failures}/8 in {wait}s, resuming from {since}")
                time.sleep(wait)

# pull all issue/PR comments and inline review comments, saving as it goes
def comment_data(make_client, path="comments.csv"):
    for method, url_attr, ctype in [
        ("get_issues_comments", "issue_url", "issue_comment"),
        ("get_pulls_comments", "pull_request_url", "review_comment"),
    ]:
        while True:
            saved = fetch_comments(make_client, method, url_attr, ctype, path)
            print(f"  {ctype}: pass saved {saved} new")
            if saved == 0:
                break

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

def find_prs_for_commits(mined_data, shas):
    links = []
    for sha in shas:
        try:
            for pr in mined_data.get_commit(sha).get_pulls():
                links.append({"sha": sha, "pr_number": pr.number})
        except Exception as e:
            print(f"  could not look up PR for {sha[:8]}: {e}")
    return links

#TODO: Define rabbit_csv to iterate through every unique GitHub username and save results to rabbit.csv
def rabbit_results_csv(rows, path="rabbit.csv"):
    # import
    # define users
    # open as csv
    # writer
    # return users
    pass
    
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
        "start_utc": START.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_utc": END.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "GitHub REST API with PyGithub",
    }


def authenticate_client(per_page=100):
    token = os.environ["GITHUB_TOKEN"]
    return Github(auth=Auth.Token(token), per_page=per_page)

# authenticates using Github's REST API and pulls the Zephyr repo
def authenticate_token(per_page=100):
    return authenticate_client(per_page).get_repo(REPOSITORY)