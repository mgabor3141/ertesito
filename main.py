import json
import time
from pathlib import Path
from pprint import pprint

from send_notification import send_notification
from sheet_diff import sheet_diff
from get_sheet import get_current_sheet


PREVIOUS_FILE = Path("data/raw/previous.json")
DIFF_FILE = Path("data/diff/diff.json")


def main():
    if not PREVIOUS_FILE.parent.exists():
        PREVIOUS_FILE.parent.mkdir(parents=True)

    if not DIFF_FILE.parent.exists():
        DIFF_FILE.parent.mkdir(parents=True)

    sheet = get_current_sheet()

    if PREVIOUS_FILE.exists():
        old_sheet = json.load(open(PREVIOUS_FILE))
    else:
        json.dump(sheet, open(PREVIOUS_FILE, "w"), indent=2)
        return

    json.dump(sheet, open(PREVIOUS_FILE, "w"), indent=2)

    diffs = []
    added = []

    for tab_key in sheet.keys():
        if tab_key not in old_sheet.keys():
            added.append({"id": tab_key, "title": sheet[tab_key]["title"]})
            continue

        [diff_exists, diff] = sheet_diff(old_sheet[tab_key], sheet[tab_key])
        if diff_exists:
            diffs.append(diff)

    pprint(diffs)

    if DIFF_FILE.exists():
        historic_diffs = json.load(open(DIFF_FILE))
    else:
        historic_diffs = {}

    if len(diffs) == 0 and len(added) == 0:
        return

    historic_diffs[str(int(time.time()))] = {"diffs": diffs, "added": added}

    email_sent = send_notification(historic_diffs)

    if email_sent:
        print("Email sent")
        historic_diffs = {}
    else:
        print("No match found, email held")

    json.dump(historic_diffs, open(DIFF_FILE, "w"), indent=2)


if __name__ == "__main__":
    main()
