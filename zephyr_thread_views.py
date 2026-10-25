# T5 - Build the Coder Tools;
import csv
import os
from collections import defaultdict

OUT_DIR = "thread_views"
csv.field_size_limit(2**31 - 1)

def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_view(thread, comments):
    lines = [
        f"URL:   {thread['html_url']}",
        f"TITLE: {thread['title']}",
        "",
        f"*--- opening post by {thread['author_login']} ({thread['created_at']})",
        thread["body"].strip(),
    ]
    for c in sorted(comments, key=lambda c: c["created_at"]):
        lines += ["", f"*--- {c['author_login']} ({c['created_at']})", c["body"].strip()]
    return "\n".join(lines) + "\n"


def main():
    comments_by_thread = defaultdict(list)
    for c in read_rows("coding_sample_comments.csv"):
        comments_by_thread[c["thread_number"]].append(c)

    os.makedirs(OUT_DIR, exist_ok=True)
    threads = read_rows("coding_sample.csv")
    for thread in threads:
        number = thread["number"]
        with open(f"{OUT_DIR}/{number}.txt", "w", encoding="utf-8") as f:
            f.write(build_view(thread, comments_by_thread[number]))
    print(f"Thread views saved: {len(threads)}")


if __name__ == "__main__":
    main()
