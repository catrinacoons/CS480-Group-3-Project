"""
Completes task T14: It computes Cohen's kappa, raw agreement, 
and a table of which categories get confused, from two coders' sheets.


Commands to run: 
python agreement.py
- runs on the IRR set

python agreement.py --set pilot --coders [insert_coder_name1] [insert_coder_name2]
- runs on two specified pilot sets, used for testing on pilot labels
"""
 
import argparse
import csv
import os
import re
from collections import Counter
 
IRR_CODERS = ["alessia", "catrina"]
COLUMNS = ["thread_number", "primary_category", "secondary_category", "notes", "not_genai_flag"]
 
# Label written for a thread flagged not_genai_flag = yes (categories left blank).
FALSE_POSITIVE = "False Positive"
 
PRIMARY_CATEGORIES = [
    "No Engagement",
    "Accepted and Applied",
    "Questioned or Discussed",
    "Rejected or Rebutted",
    "Disclosure Requested",
    "Tested or Verified",
]
SECONDARY_CATEGORIES = [
    "AI reviewer",
    "AI Assisted, disclosed",
    "AI Assisted, disclosed later",
]
YES_VALUES = {"yes", "y", "true", "1", "x"}
 
 
def simplify(text):
    # Lowercase and drop punctuation
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
 
 
def make_lookup(categories):
    lookup = {simplify(c): c for c in categories}
    lookup[simplify(FALSE_POSITIVE)] = FALSE_POSITIVE
    return lookup
 
 
PRIMARY_LOOKUP = make_lookup(PRIMARY_CATEGORIES)
SECONDARY_LOOKUP = make_lookup(SECONDARY_CATEGORIES)
 
 
def read_sheet(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"{path} is missing columns: {missing}")
        rows = {}
        for row in reader:
            number = row["thread_number"].strip()
            if number:
                rows[number] = row
        return rows
 
 
def label_for(row, field, lookup, warnings, coder):
    # Return the coded label for one field, or None if the coder left it blank.
    if row["not_genai_flag"].strip().lower() in YES_VALUES:
        return FALSE_POSITIVE
    raw = row[field].strip()
    if not raw:
        return None
    label = lookup.get(simplify(raw))
    if label is None:
        warnings.append(f"{coder}, thread {row['thread_number']}: '{raw}' is not a codebook {field}")
        return raw
    return label
 
 
def flag_for(row):
    return "yes" if row["not_genai_flag"].strip().lower() in YES_VALUES else "no"
 
 
def cohens_kappa(pairs):
    n = len(pairs)
    if n == 0:
        return None, None
    observed = sum(a == b for a, b in pairs) / n
    count_a = Counter(a for a, _ in pairs)
    count_b = Counter(b for _, b in pairs)
    expected = sum(count_a[k] * count_b[k] for k in count_a) / (n * n)
    if expected == 1:
        # Both coders used a single, identical category for everything: kappa is undefined.
        return observed, None
    return observed, (observed - expected) / (1 - expected)
 
 
def interpret(kappa):
    # Landis & Koch bands (standard used)
    if kappa is None:
        return "undefined"
    if kappa < 0:
        return "poor"
    for cutoff, name in [(0.20, "slight"), (0.40, "fair"), (0.60, "moderate"), (0.80, "substantial")]:
        if kappa <= cutoff:
            return name
    return "almost perfect"
 
 
def confusion_table(pairs, known):
    used = {a for a, _ in pairs} | {b for _, b in pairs}
    labels = [c for c in known if c in used] + sorted(used - set(known))
    counts = Counter(pairs)
    return labels, [[counts[(r, c)] for c in labels] for r in labels]
 
 
def clusters(pairs):
    # Disagreement pairs, ignoring which coder said which.
    counts = Counter(tuple(sorted((a, b))) for a, b in pairs if a != b)
    return counts.most_common()
 
 
def analyze(name, pairs, known, coders):
    observed, kappa = cohens_kappa(pairs)
    labels, matrix = confusion_table(pairs, known)
    return {
        "name": name,
        "n": len(pairs),
        "agree": sum(a == b for a, b in pairs),
        "observed": observed,
        "kappa": kappa,
        "labels": labels,
        "matrix": matrix,
        "clusters": clusters(pairs),
        "coders": coders,
    }
 
 
def fmt(value, pct=False):
    if value is None:
        return "N/A"
    return f"{value:.1%}" if pct else f"{value:.3f}"
 
 
def table_text(result):
    a, b = result["coders"]
    labels = result["labels"]
    width = max([len(l) for l in labels] + [len(a) + len(b) + 4])
    corner = a + " \\ " + b
    lines = [f"{corner:<{width}} | " + " | ".join(f"{l[:12]:>12}" for l in labels)]
    lines.append("-" * len(lines[0]))
    for label, row in zip(labels, result["matrix"]):
        lines.append(f"{label:<{width}} | " + " | ".join(f"{v:>12}" for v in row))
    return "\n".join(lines)
 
 
def report_text(results, set_name, coders, notes):
    out = [f"Agreement report: {set_name} set, {coders[0]} vs {coders[1]}", ""]
    out.append(f"{'Field':<20}{'Threads':>9}{'Raw agreement':>16}{'Kappa':>9}  Strength")
    for r in results:
        out.append(f"{r['name']:<20}{r['n']:>9}{fmt(r['observed'], pct=True):>16}"
                   f"{fmt(r['kappa']):>9}  {interpret(r['kappa'])}")
    for r in results:
        out += ["", f"== {r['name']} ==", f"Agreed on {r['agree']} of {r['n']} threads.", "",
                table_text(r), "", "Where disagreements cluster:"]
        if r["clusters"]:
            out += [f"  {count} x  {x}  <->  {y}" for (x, y), count in r["clusters"]]
        else:
            out.append("  (no disagreements)")
    if notes:
        out += ["", "Notes:"] + [f"  - {n}" for n in notes]
    return "\n".join(out)
 
 
def write_outputs(folder, results, rows, report):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
 
    with open(os.path.join(folder, "summary.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["field", "threads", "agreed", "raw_agreement", "cohens_kappa", "strength"])
        for r in results:
            writer.writerow([r["name"], r["n"], r["agree"],
                             "" if r["observed"] is None else round(r["observed"], 4),
                             "" if r["kappa"] is None else round(r["kappa"], 4),
                             interpret(r["kappa"])])
 
    for r in results:
        file_name = "confusion_" + r["name"].lower().replace(" ", "_") + ".csv"
        with open(os.path.join(folder, file_name), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([f"{r['coders'][0]} \\ {r['coders'][1]}"] + r["labels"])
            for label, row in zip(r["labels"], r["matrix"]):
                writer.writerow([label] + row)
 
    with open(os.path.join(folder, "disagreements.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["thread_number", "field", "coder_a", "coder_b"])
        writer.writerows(rows)
 
 
def main():
    parser = argparse.ArgumentParser(description="Inter-rater agreement for two coding sheets.")
    parser.add_argument("--set", default="irr", help="coding_sheets subfolder (default: irr)")
    parser.add_argument("--coders", nargs=2, default=IRR_CODERS, metavar=("CODER_A", "CODER_B"))
    parser.add_argument("--sheets-dir", default="coding_sheets")
    parser.add_argument("--out-dir", default="agreement_results")
    args = parser.parse_args()
 
    coder_a, coder_b = args.coders
    sheet_a = read_sheet(os.path.join(args.sheets_dir, args.set, f"{coder_a}.csv"))
    sheet_b = read_sheet(os.path.join(args.sheets_dir, args.set, f"{coder_b}.csv"))
 
    notes = []
    only_a = sorted(set(sheet_a) - set(sheet_b))
    only_b = sorted(set(sheet_b) - set(sheet_a))
    if only_a:
        notes.append(f"Only in {coder_a}'s sheet (skipped): {', '.join(only_a)}")
    if only_b:
        notes.append(f"Only in {coder_b}'s sheet (skipped): {', '.join(only_b)}")
    shared = sorted(set(sheet_a) & set(sheet_b), key=lambda n: (len(n), n))
 
    fields = [
        ("Primary category", "primary_category", PRIMARY_LOOKUP, PRIMARY_CATEGORIES + [FALSE_POSITIVE]),
        ("Secondary category", "secondary_category", SECONDARY_LOOKUP, SECONDARY_CATEGORIES + [FALSE_POSITIVE]),
    ]
    results, disagreement_rows = [], []
    for name, field, lookup, known in fields:
        pairs, blank = [], []
        for number in shared:
            a = label_for(sheet_a[number], field, lookup, notes, coder_a)
            b = label_for(sheet_b[number], field, lookup, notes, coder_b)
            if a is None or b is None:
                blank.append(number)
                continue
            pairs.append((a, b))
            if a != b:
                disagreement_rows.append([number, name, a, b])
        if blank:
            notes.append(f"{name}: left blank by at least one coder, skipped: {', '.join(blank)}")
        results.append(analyze(name, pairs, known, (coder_a, coder_b)))
 
    flag_pairs = []
    for number in shared:
        a, b = flag_for(sheet_a[number]), flag_for(sheet_b[number])
        flag_pairs.append((a, b))
        if a != b:
            disagreement_rows.append([number, "not_genai_flag", a, b])
    results.append(analyze("not_genai_flag", flag_pairs, ["yes", "no"], (coder_a, coder_b)))
 
    report = report_text(results, args.set, (coder_a, coder_b), notes)
    print(report)
    out_folder = os.path.join(args.out_dir, args.set)
    write_outputs(out_folder, results, disagreement_rows, report)
    print(f"\nResults saved to {out_folder}/")
 
 
if __name__ == "__main__":
    main()