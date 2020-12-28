import re
from pprint import pprint

from download_sheets import download_sheets


def get_path(tab, row, col, row_headers, col_headers):
    path = [tab["title"]]

    for c in range(0, col_headers):
        path.append(tab["data"][row][c].strip())

    for r in range(0, row_headers):
        path.append(tab["data"][r][col].strip())

    return path


date_like = re.compile(r'^\d\d\d\d\.\d\d\.\d\d\.?$')


def find_headers(tab):
    data = tab["data"]

    row_headers, col_headers = 0, 0

    print("Finding headers in", tab["title"])

    # Method 1: Empty cells in corner
    for row in range(0, len(data)):
        if data[row][0].strip():
            row_headers = row
            break

    if row_headers <= 0:
        row_headers = tab["frozenRowCount"]

    if row_headers >= 1:
        for col in range(0, len(data[row_headers - 1])):
            if data[row_headers - 1][col].strip():
                col_headers = col
                break

    if col_headers <= 0:
        col_headers = tab["frozenColumnCount"]

    # Method 2: Where is the first date-like cell?
    if row_headers <= 0 or col_headers <= 0:
        print("Method 1 failed, trying method 2")

        for row in range(0, len(tab["data"])):
            for col in range(0, len(tab["data"][0])):
                value = tab["data"][row][col].strip()

                if date_like.match(value):
                    print("First date found:", value, "at", row, col)
                    return row, col + 2
    else:
        return row_headers, col_headers

    print("Failed to find headers in", tab["title"])
    return None, None


def parse_sheet(sheet):
    entries = []

    for tab in sheet:
        [row_headers, col_headers] = find_headers(tab)
        print(row_headers, col_headers)

        if not row_headers or not col_headers:
            print("Skipping", tab["title"], "because no headers were found")
            continue

        for row in range(row_headers, len(tab["data"])):
            for col in range(col_headers, len(tab["data"][0])):
                value = tab["data"][row][col].strip()

                if value:
                    entries.append(
                        [
                            get_path(tab, row, col, row_headers, col_headers),
                            value
                        ]
                    )

    return entries


if __name__ == "__main__":
    s = download_sheets()
    pprint(parse_sheet(s))
