import os
import sys
 
import numpy as np
import pandas as pd
 
SEED = 480
ID = "number"
STRATUM = "strongest_signal"
SIZES = {"open_coding": 25, "pilot": 30, "irr": 60}
OUT_DIR = "id_lists"

def quotas(counts, k):
    # Largest-remainder allocation of k draws across strata, proportional to stratum size.
    exact = counts * k / counts.sum()
    base = np.floor(exact).astype(int)
    leftover = int(k - base.sum())
    for s in (exact - base).sort_values(ascending=False, kind="stable").index[:leftover]:
        base[s] += 1
    return base
 
 
def split(df):
    rng = np.random.default_rng(SEED)
    pool = df.sort_values(ID).reset_index(drop=True)
    sets = {}
    for name, k in SIZES.items():
        counts = pool[STRATUM].value_counts().sort_index()
        picked = []
        for stratum, n in quotas(counts, k).items():
            if n:
                ids = pool.loc[pool[STRATUM] == stratum, ID].to_numpy()
                picked.extend(rng.choice(ids, size=n, replace=False))
        sets[name] = sorted(int(i) for i in picked)
        pool = pool[~pool[ID].isin(picked)]
    sets["remainder"] = sorted(int(i) for i in pool[ID])
    return sets
 
 
def main(path="coding_sample.csv"):
    df = pd.read_csv(path, keep_default_na=False, low_memory=False)
    df[ID] = df[ID].astype(int)
    assert df[ID].is_unique, f"duplicate {ID} values in {path}"
    need = sum(SIZES.values())
    assert len(df) > need, f"{path} has {len(df)} rows; need more than {need}"
    if len(df) != 300:
        print(f"  WARNING: coding sample has {len(df)} threads, not 300; remainder will be {len(df) - need}")
 
    sets = split(df)
 

    for name, k in SIZES.items():
        assert len(sets[name]) == k, f"{name}: expected {k}, got {len(sets[name])}"
    all_ids = [i for ids in sets.values() for i in ids]
    assert len(all_ids) == len(set(all_ids)), "overlap between sets"
    assert set(all_ids) == set(df[ID]), "sets do not cover the coding sample"
 
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, ids in sets.items():
        pd.DataFrame({ID: ids}).to_csv(f"{OUT_DIR}/{name}_ids.csv", index=False)
 
    which = {i: name for name, ids in sets.items() for i in ids}
    df["set"] = df[ID].map(which)
    summary = pd.crosstab(df[STRATUM], df["set"])[list(sets)]
    summary["total"] = summary.sum(axis=1)
    summary.loc["TOTAL"] = summary.sum()
    summary.to_csv(f"{OUT_DIR}/split_summary.csv")
    print(summary.to_string())
 
 
if __name__ == "__main__":
    main(*sys.argv[1:2])