# filters + cleans the raw CSVs, builds thread-level variables, writes the analysis-ready dataset
import json
import os
import pandas as pd
from zephyr_github_api import START, END, REPOSITORY

BOT_LOGINS = {"zephyrbot"}   # verify against the most frequent commenters in comments.csv
FLAG = "genai_candidate"

def is_bot(login, account_type):
    return account_type == "Bot" or str(login).endswith("[bot]") or login in BOT_LOGINS

def drop_bots(df):
    mask = pd.Series([is_bot(l, t) for l, t in zip(df.author_login, df.author_type)],
                    index=df.index, dtype=bool)
    return df[~mask].copy()

def union_signals(series):
    found = set()
    for s in series:
        found.update(x for x in str(s).split(";") if x)
    return ";".join(sorted(found))

def build():
    cp = {}
    threads = pd.read_csv("threads.csv", keep_default_na=False)
    comments = pd.read_csv("comments.csv", keep_default_na=False)
    commits = pd.read_csv("commits.csv", keep_default_na=False)
    cp["commits_retrieved"] = len(commits)
    cp["threads_retrieved"] = len(threads)
    cp["comments_retrieved"] = len(comments)

    for df in (threads, comments):
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
        df[FLAG] = df[FLAG].astype(str) == "True"

    # 1. observation-period filter
    threads = threads[(threads.created_at >= START) & (threads.created_at <= END)].copy()
    comments = comments[(comments.created_at >= START) & (comments.created_at <= END)].copy()
    cp["threads_after_period_filter"] = len(threads)
    cp["comments_after_period_filter"] = len(comments)

    # 2. exclusions: bot-authored threads/comments, and comments on threads outside the study set
    threads = drop_bots(threads)
    comments = drop_bots(comments)
    comments = comments[comments.thread_number.isin(threads.number)].copy()
    cp["threads_after_exclusions"] = len(threads)
    cp["comments_after_exclusions"] = len(comments)

    # 3. derived thread-level variables
    stats = comments.groupby("thread_number").agg(
        n_comments=("comment_id", "count"),
        n_participants=("author_login", "nunique"))
    flagged = comments[comments[FLAG]].groupby("thread_number").agg(
        n_genai_comments=("comment_id", "count"),
        comment_signals=("signal_types", union_signals),
        first_genai_comment_at=("created_at", "min"))
    df = threads.rename(columns={FLAG: "genai_in_body", "signal_types": "body_signals",
                                "matched_text": "body_matched"})
    df = df.merge(stats, left_on="number", right_index=True, how="left")
    df = df.merge(flagged, left_on="number", right_index=True, how="left")
    for col in ("n_comments", "n_participants", "n_genai_comments"):
        df[col] = df[col].fillna(0).astype(int)
    df["comment_signals"] = df["comment_signals"].fillna("")

    linked = set()
    if os.path.exists("commit_pr_links.csv"):
        linked = set(pd.read_csv("commit_pr_links.csv")["pr_number"])
    df["linked_flagged_commit"] = df.number.isin(linked)
    df["all_signals"] = [union_signals([a, b]) for a, b in zip(df.body_signals, df.comment_signals)]
    df["has_assisted_by_tag"] = df.all_signals.str.contains("assisted_by_tag")
    df["thread_genai_candidate"] = (df.genai_in_body | (df.n_genai_comments > 0)
                                    | df.linked_flagged_commit)
    df.to_csv("threads_derived.csv", index=False, encoding="utf-8")

    # 4. final dataset: one row per candidate thread, plus its comments for coding
    final = df[df.thread_genai_candidate].copy()
    final_comments = comments[comments.thread_number.isin(final.number)]
    final_comments = final_comments.sort_values(["thread_number", "created_at"])
    final.to_csv("final_dataset.csv", index=False, encoding="utf-8")
    final_comments.to_csv("final_comments.csv", index=False, encoding="utf-8")
    cp["final_threads"] = len(final)
    cp["final_comments"] = len(final_comments)

    # 5. RABBIT input: only authors involved in candidate threads
    users = sorted(set(final.author_login) | set(final_comments.author_login))
    pd.DataFrame({"contributor_username": users}).to_csv("rabbit_users.csv", index=False)
    cp["unique_authors_for_rabbit"] = len(users)

    # 6. validation sample (fixed seed so it's reproducible)
    sample = final.sample(n=min(60, len(final)), random_state=480)
    sample = sample[["number", "kind", "title", "body_signals", "comment_signals", "body_matched"]].copy()
    sample["url"] = f"https://github.com/{REPOSITORY}/issues/" + sample.number.astype(str)
    for col in ("is_true_genai", "validator", "notes"):
        sample[col] = ""
    sample.to_csv("validation_sample.csv", index=False, encoding="utf-8")

    with open("checkpoints.json", "w", encoding="utf-8") as f:
        json.dump(cp, f, indent=2)
    for k, v in cp.items():
        print(f"{k}: {v}")
    return final

if __name__ == "__main__":
    build()