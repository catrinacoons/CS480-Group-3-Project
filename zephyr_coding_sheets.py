import csv
import os

TEAM_CODERS = ["alessia", "catrina", "adelle", "julia"]
IRR_CODERS = ["alessia", "catrina"]
COLUMNS = ["thread_number", "primary_category", "secondary_category", "notes", "not_genai_flag"]

def read_ids(set_name):
    with open(f"id_lists/{set_name}_ids.csv", newline="", encoding="utf-8") as f:
        return [row["number"] for row in csv.DictReader(f)]


def write_sheet(set_name, person, numbers):
    os.makedirs(f"coding_sheets/{set_name}", exist_ok=True)
    path = f"coding_sheets/{set_name}/{person}.csv"
    if os.path.exists(path):
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        for number in numbers:
            writer.writerow([number, "", "", "", ""])


def main():
    for person in TEAM_CODERS:
        write_sheet("open_coding", person, read_ids("open_coding"))
        write_sheet("pilot", person, read_ids("pilot"))

    for person in IRR_CODERS:
        write_sheet("irr", person, read_ids("irr"))

    remainder = read_ids("remainder")
    for i, person in enumerate(TEAM_CODERS):
        write_sheet("remainder", person, remainder[i::4])
    print(f"Coding sheets saved: {3 * len(TEAM_CODERS) + len(IRR_CODERS)}")


if __name__ == "__main__":
    main()
