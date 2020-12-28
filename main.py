import json
from pathlib import Path
from pprint import pprint

from parse_sheet import parse_sheet
from send_notification import send_notifications
from download_sheets import download_sheets
from to_tuple import to_tuple


PREVIOUS_FILE = Path("data/raw/previous.json")


def main():
    # Create folders needed for running if they don't exist
    if not PREVIOUS_FILE.parent.exists():
        PREVIOUS_FILE.parent.mkdir(parents=True)

    # Load latest version of spreadsheet
    sheet = download_sheets()

    # Parse to entries
    entries = [to_tuple(entry) for entry in parse_sheet(sheet)]

    # TODO: Generate calendars

    # Load previously saved state
    if PREVIOUS_FILE.exists():
        old_entries = [to_tuple(entry) for entry in json.load(open(PREVIOUS_FILE))]
    else:
        # If we don't have past data save this for next time and just quit
        json.dump(entries, open(PREVIOUS_FILE, "w"), indent=2)
        return

    # Save (and overwrite) previous past state with current
    json.dump(entries, open(PREVIOUS_FILE, "w"), indent=2)

    # Diffs
    added = set(entries) - set(old_entries)
    removed = set(old_entries) - set(entries)

    print("Added")
    pprint(added)
    print("Removed")
    pprint(removed)

    send_notifications(added, removed)


if __name__ == "__main__":
    main()
