from __future__ import print_function
import os
from pprint import pprint

import requests
from pympler import asizeof


def part_of_merge(r, c, merges):
    for merge in merges:
        if (
            merge["startRowIndex"] <= r < merge["endRowIndex"]
            and merge["startColumnIndex"] <= c < merge["endColumnIndex"]
        ):
            return [merge["startRowIndex"], merge["startColumnIndex"]]
    return None


def expand_merged_cells(data, merges, frozen_row_count):
    expanded_data = []

    for r, row in enumerate(data):
        expanded_data.append([])

        if sum([c != "" for c in row]) <= 1:
            if r < frozen_row_count:
                frozen_row_count -= 1

            continue

        for c, cell in enumerate(row):
            expanded_data[-1].append(cell)
            merge_origin = part_of_merge(r, c, merges)

            if merge_origin:
                expanded_data[-1][-1] = expanded_data[merge_origin[0]][merge_origin[1]]

    return [list(filter(lambda l: l != [], expanded_data)), frozen_row_count]


def square_data(raw_data):
    max_len = max([len(row) for row in raw_data])

    for row in raw_data:
        row.extend([""] * (max_len - len(row)))

    return raw_data


def get_current_sheet():
    sheets_properties = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{os.getenv('SPREADSHEET_ID')}?key={os.getenv('SHEETS_API_KEY')}"
    ).json()["sheets"]

    sheets_internal = {}

    for sheet in sheets_properties:
        props = sheet["properties"]

        raw_data = (
            requests.get(
                f"https://sheets.googleapis.com/v4/spreadsheets/{os.getenv('SPREADSHEET_ID')}/values/{props['title']}?key={os.getenv('SHEETS_API_KEY')}"
            )
            .json()
            .get("values", [[]])
        )

        squared_data = square_data(raw_data)

        [data, frozen_row_count] = expand_merged_cells(
            squared_data,
            sheet.get("merges", []),
            props.get("gridProperties", {}).get("frozenRowCount", 0),
        )

        sheets_internal[str(props["sheetId"])] = {
            "title": props["title"],
            "data": data,
            "frozenRowCount": frozen_row_count,
            "frozenColumnCount": props.get("gridProperties", {}).get(
                "frozenColumnCount", 0
            ),
        }
        print(props["title"], "betöltve")

    print("TELJESEN BETÖLTVE", asizeof.asizeof(sheets_internal), "B")
    return sheets_internal


if __name__ == "__main__":
    pprint(get_current_sheet())
