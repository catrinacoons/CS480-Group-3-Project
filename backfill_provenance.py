import json, os
from datetime import datetime, timezone
import pandas as pd
import zephyr_github_api as g

prov = g.provenance_json()
prov["note"] = ("commits, threads and comments were collected before provenance logging was added; "
                "their counts and dates were reconstructed from the output files")
cp, runs = {}, {}
for name, key, col in [("commits.csv", "commits", "sha"), ("threads.csv", "threads", "number"),
                       ("comments.csv", "comments", "comment_id")]:
    if os.path.exists(name):
        cp[key] = len(pd.read_csv(name, usecols=[col], low_memory=False))
        runs[key] = datetime.fromtimestamp(os.path.getmtime(name), timezone.utc).isoformat()
prov["checkpoints"], prov["stage_runs"] = cp, runs
with open("provenance.json", "w", encoding="utf-8") as f:
    json.dump(prov, f, indent=2)