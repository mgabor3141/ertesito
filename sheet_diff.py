def get_path(tab, datarow, datacol):
    path = []

    for col in range(0, tab["frozenColumnCount"]):
        path.append(tab["data"][datarow][col])

    for row in range(0, tab["frozenRowCount"]):
        path.append(tab["data"][row][datacol])

    return path


def sheet_diff(old_tab, new_tab):
    diff_result = []  # path array, before, after

    if (
        new_tab["frozenRowCount"] != old_tab["frozenRowCount"]
        or new_tab["frozenColumnCount"] != old_tab["frozenColumnCount"]
        or len(new_tab["data"]) != len(old_tab["data"])
        or len(new_tab["data"]) == 0
        or len(old_tab["data"]) == 0
        or len(new_tab["data"][0]) != len(old_tab["data"][0])
    ):
        return [True, {"title": new_tab["title"], "unhandled": True}]

    for row in range(new_tab["frozenRowCount"], len(new_tab["data"])):
        for col in range(new_tab["frozenColumnCount"], len(new_tab["data"][0])):
            if old_tab["data"][row][col] != new_tab["data"][row][col]:
                diff_result.append(
                    {
                        "path": get_path(new_tab, row, col),
                        "before": old_tab["data"][row][col],
                        "after": new_tab["data"][row][col],
                    }
                )

    return [diff_result != [], {"title": old_tab["title"], "diff": diff_result}]
