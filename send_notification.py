import os
from datetime import datetime
import json
from fuzzywuzzy import fuzz

from send_email import send_email


def print_value(value):
    if value == "":
        return "[üres]"
    return value


def print_path(path):
    if len(path) == 0:
        return "?"

    return " / ".join(path)


def data_to_html(historic_diffs):
    html = "<h1>Jelentés változásokról</h1>"

    for time in historic_diffs:
        html += f"<h2>{datetime.fromtimestamp(int(time))}</h2>"

        entry = historic_diffs[time]

        html += "<p>"
        for sheet in entry["added"]:
            html += f"Új tábla: {sheet['title']}<br />"
        html += "</p>"

        for sheet in entry["diffs"]:
            html += f"<h3>Változtatások a <i>{sheet['title']}</i> fülön</h3><p>"
            for diff in sheet["diff"]:
                highlight = match(diff)
                html += f"<u>{print_path(diff['path'])}:</u><br /> &nbsp;&nbsp;&nbsp;&nbsp; \
                                {'<b style=background-color:purple;color:white;padding-left:3px;padding-right:3px;>' if highlight else ''} \
                                {print_value(diff['before'])} -> {print_value(diff['after'])}<br /> \
                                {'</b>' if highlight else ''}"
            html += "</p>"

    return html


def match(diff):
    return (
        fuzz.token_set_ratio(diff["before"], os.getenv("MATCH_STRING")) >= 80
        or fuzz.token_set_ratio(diff["after"], os.getenv("MATCH_STRING")) >= 80
    )


def send_notification(historic_diffs):
    email = False

    for time in historic_diffs:
        entry = historic_diffs[time]

        if len(entry["added"]) > 0:
            email = True
            break

        for sheet in entry["diffs"]:
            for diff in sheet["diff"]:
                if match(diff):
                    email = True
                    print("Match found:", diff)
                    break

    if email:
        send_email(data_to_html(historic_diffs))
        return True

    return False


if __name__ == "__main__":
    historic_diffs = json.load(open("data/diff/matched_diff.json"))
    print(send_notification(historic_diffs))
