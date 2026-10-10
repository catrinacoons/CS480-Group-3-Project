# filters + cleans the raw CSVs, builds thread-level variables, writes the analysis-ready dataset
import json
import os
import re
import pandas as pd
from zephyr_github_api import START, END

FLAG = "genai_candidate"
# automation accounts are excluded (verify against the top authors in comments.csv)
AUTOMATION_BOTS = {"zephyrbot", "github-actions[bot]", "dependabot[bot]", "stale[bot]", "claassistant"}
# AI-assistant bot accounts are kept and labelled: their output is what the RQ studies
AI_BOT = re.compile(r"copilot|claude|chatgpt|gemini|codex|cursor|devin", re.I)


def load_rabbit(path="rabbit.csv"):
    if not os.path.exists(path):
        print("  (no rabbit.csv yet: bot detection uses account type and name only)")
        return {}
    r = pd.read_csv(path, dtype=str, keep_default_na=False)
    return {u: t.lower() for u, t in zip(r.contributor_username, r.contributor_type)}


def classify(df, rabbit):
    is_bot, is_ai = [], []
    for login, atype in zip(df.author_login, df.author_type):
        l = str(login)
        bot = (atype == "Bot" or l.endswith("[bot]") or l.lower() in AUTOMATION_BOTS
               or rabbit.get(l) == "bot")
        is_bot.append(bot)
        is_ai.append(bot and bool(AI_BOT.search(l)))
    df["author_is_bot"], df["author_is_ai_bot"] = is_bot, is_ai
    return df


def drop_automation(df):
    return df[~(df.author_is_bot & ~df.author_is_ai_bot)].copy()


def union_signals(series):
    found = set()
    for s in series:
        found.update(x for x in str(s).split(";") if x)
    return ";".join(sorted(found))


def strongest(row):
    s = row.all_signals
    for name in ("assisted_by_tag", "ai_coauthor"):
        if name in s:
            return name
    if row.author_is_ai_bot or row.n_ai_bot_comments > 0:
        return "ai_bot"
    if "ai_keyword" in s:
        return "ai_keyword"
    return "linked_commit_only" if row.linked_flagged_commit else ""


def build():
    cp = {}
    rabbit = load_rabbit()
    threads = pd.read_csv("threads.csv", keep_default_na=False, low_memory=False)
    comments = pd.read_csv("comments.csv", keep_default_na=False, low_memory=False)
    commits = pd.read_csv("commits.csv", keep_default_na=False, low_memory=False)
    cp["commits_retrieved"] = len(commits)
    cp["commits_flagged"] = int((commits[FLAG].astype(str) == "True").sum())
    cp["threads_retrieved"] = len(threads)
    cp["comments_retrieved"] = len(comments)

    # cleaning: remove duplicates left by resumed or overlapping collection passes
    threads = threads.drop_duplicates(subset=["number"]).copy()
    comments = comments.drop_duplicates(subset=["comment_type", "comment_id"]).copy()
    cp["threads_after_dedupe"] = len(threads)
    cp["comments_after_dedupe"] = len(comments)

    for df in (threads, comments):
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
        df[FLAG] = df[FLAG].astype(str) == "True"
    for col in ("closed_at", "merged_at"):
        threads[col] = pd.to_datetime(threads[col].replace("", pd.NA), utc=True,
                                      errors="coerce", format="mixed")

    # 1. observation-period filter
    threads = threads[(threads.created_at >= START) & (threads.created_at <= END)].copy()
    comments = comments[(comments.created_at >= START) & (comments.created_at <= END)].copy()
    cp["threads_after_period_filter"] = len(threads)
    cp["comments_after_period_filter"] = len(comments)

    # 2. exclusions: automation bots, and comments on threads outside the study set
    threads, comments = classify(threads, rabbit), classify(comments, rabbit)
    threads = drop_automation(threads)
    comments = drop_automation(comments)
    comments = comments[comments.thread_number.isin(threads.number)].copy()
    cp["threads_after_exclusions"] = len(threads)
    cp["comments_after_exclusions"] = len(comments)

    # 3. derived thread-level variables
    stats = comments.groupby("thread_number").agg(
        n_comments=("comment_id", "count"),
        n_participants=("author_login", "nunique"),
        n_ai_bot_comments=("author_is_ai_bot", "sum"))
    flagged = comments[comments[FLAG]].groupby("thread_number").agg(
        n_genai_comments=("comment_id", "count"),
        comment_signals=("signal_types", union_signals),
        first_genai_comment_at=("created_at", "min"))
    df = threads.rename(columns={FLAG: "genai_in_body", "signal_types": "body_signals",
                                 "matched_text": "body_matched"})
    df = df.merge(stats, left_on="number", right_index=True, how="left")
    df = df.merge(flagged, left_on="number", right_index=True, how="left")
    for col in ("n_comments", "n_participants", "n_genai_comments", "n_ai_bot_comments"):
        df[col] = df[col].fillna(0).astype(int)
    df["comment_signals"] = df["comment_signals"].fillna("")

    # time-based variables (threads still open at END are right-censored at END)
    df["is_merged"] = df.merged_at.notna()
    df["censored"] = df.closed_at.isna()
    df["days_open"] = (df.closed_at.fillna(pd.Timestamp(END)) - df.created_at).dt.total_seconds() / 86400
    df["days_to_first_genai_comment"] = (df.first_genai_comment_at - df.created_at).dt.total_seconds() / 86400
    cp["prs_with_merged_at"] = int(df[df.kind == "pull_request"].is_merged.sum())

    linked = set(pd.read_csv("commit_pr_links.csv")["pr_number"].dropna().astype(int))
    if os.path.exists("commit_pr_links.csv"):
        linked = set(pd.read_csv("commit_pr_links.csv")["pr_number"])
    else:
        print("  WARNING: commit_pr_links.csv not found, linked_flagged_commit will be all False")
    df["linked_flagged_commit"] = df.number.isin(linked)
    df["all_signals"] = [union_signals([a, b]) for a, b in zip(df.body_signals, df.comment_signals)]
    df["has_assisted_by_tag"] = df.all_signals.str.contains("assisted_by_tag")
    df["thread_genai_candidate"] = (df.genai_in_body | (df.n_genai_comments > 0)
                                    | df.linked_flagged_commit | df.author_is_ai_bot
                                    | (df.n_ai_bot_comments > 0))
    df["strongest_signal"] = df.apply(strongest, axis=1)
    df.to_csv("threads_derived.csv", index=False, encoding="utf-8")

    # 4. final dataset: one row per candidate thread, plus its comments for coding
    final = df[df.thread_genai_candidate].copy()
    final_comments = comments[comments.thread_number.isin(final.number)]
    final_comments = final_comments.sort_values(["thread_number", "created_at"])
    cp["final_threads"] = len(final)
    cp["final_comments"] = len(final_comments)

    # edit: stratified random sample for qualitative coding (fixed seed, reproducible)
    CODING_N = 300
    share = CODING_N / len(final)
    final["in_coding_sample"] = False
    for _, g in final.groupby("strongest_signal"):
        idx = g.sample(n=max(1, round(len(g) * share)), random_state=480).index
        final.loc[idx, "in_coding_sample"] = True
    cp["coding_sample_threads"] = int(final.in_coding_sample.sum())
    final_comments = final_comments.merge(final[["number", "in_coding_sample"]],
                                          left_on="thread_number", right_on="number", how="left").drop(columns="number")

    # 5. RABBIT input: only authors involved in candidate threads
    users = sorted(set(final.author_login) | set(final_comments.author_login))
    pd.DataFrame({"contributor_username": users}).to_csv("rabbit_users.csv", index=False)
    cp["unique_authors_for_rabbit"] = len(users)

    # 6. validation: up to 20 candidates per signal type + 40 non-candidates (recall check)
    # is_true_genai: candidates -> is GenAI really involved? non_candidate -> did we miss GenAI? (yes/no)
    cols = ["number", "kind", "title", "html_url", "strongest_signal",
            "body_signals", "comment_signals", "body_matched"]
    if os.path.exists("validation_sample.csv"):
        print("  validation_sample.csv exists: keeping it so labels are not overwritten")
        sample = pd.read_csv("validation_sample.csv", dtype=str, keep_default_na=False)
    else:
        pos = pd.concat([g.sample(n=min(20, len(g)), random_state=480)
                         for _, g in final.groupby("strongest_signal")])[cols].copy()
        pos["stratum"] = pos["strongest_signal"]
        rest = df[~df.thread_genai_candidate]
        neg = rest.sample(n=min(40, len(rest)), random_state=480)[cols].copy()
        neg["stratum"] = "non_candidate"
        sample = pd.concat([pos, neg])
        for col in ("is_true_genai", "validator", "notes"):
            sample[col] = ""
        sample.to_csv("validation_sample.csv", index=False, encoding="utf-8")

    labelled = sample[sample.is_true_genai.str.lower().isin(["yes", "no"])]
    if len(labelled):
        res = {}
        for stratum, g in labelled.groupby("stratum"):
            yes = int((g.is_true_genai.str.lower() == "yes").sum())
            res[stratum] = {"yes": yes, "n": len(g), "rate": round(yes / len(g), 3)}
        with open("validation_results.json", "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
        print("validation (candidate strata = precision, non_candidate = miss rate):", res)
    final["validation_label"] = final.number.astype(str).map(
        dict(zip(sample.number.astype(str), sample.is_true_genai))).fillna("")
    final.to_csv("final_dataset.csv", index=False, encoding="utf-8")
    final_comments.to_csv("final_comments.csv", index=False, encoding="utf-8")
    final[final.in_coding_sample].to_csv("coding_sample.csv", index=False, encoding="utf-8")
    final_comments[final_comments.thread_number.isin(final[final.in_coding_sample].number)] \
        .to_csv("coding_sample_comments.csv", index=False, encoding="utf-8")

    with open("checkpoints.json", "w", encoding="utf-8") as f:
        json.dump(cp, f, indent=2)
    for k, v in cp.items():
        print(f"{k}: {v}")
    return final

if __name__ == "__main__":
    build()