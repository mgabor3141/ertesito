import json
import os
from datetime import datetime
from operator import itemgetter

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


def data_to_html(historic_diffs, name):
    html = "<h1>Jelentés változásokról</h1>"

    html += f"<p>Kedves {name}!</p>"
    html += f"<p>Változás történt az ambuláns beosztásodban:</p>"

    for time, entry in reversed(list(historic_diffs.items())):
        html += f"<h2>{datetime.fromtimestamp(int(time)).strftime('%Y-%m-%d %H:%M')}</h2>"

        html += "<p>"
        for sheet in entry["added"]:
            html += f"Új tábla: {sheet['title']}<br />"
        html += "</p>"

        for sheet in entry["diffs"]:
            html += f"<h3>Változtatások a <i>{sheet['title']}</i> fülön</h3><p>"
            for diff in sheet["diff"]:
                highlight = match(diff, name)
                html += f"<u>{print_path(diff['path'])}:</u><br /> &nbsp;&nbsp;&nbsp;&nbsp; \
                                {'<b style=background-color:purple;color:white;padding-left:3px;padding-right:3px;>' if highlight else ''} \
                                {print_value(diff['before'])} -> {print_value(diff['after'])}<br /> \
                                {'</b>' if highlight else ''}"
            html += "</p>"

    html += "<hr/><small>A táblázat napközben óránként van ellenőrizve. (07-21)<br /> \
            Válaszlevélben jelezd, ha kérésed vagy kérdésed van, illetve ha nem szeretnél több ilyen értesítést kapni.</small>"

    return html


def match(diff, name):
    return (
        fuzz.token_set_ratio(diff["before"], name) >= 80
        or fuzz.token_set_ratio(diff["after"], name) >= 80
    )


def send_notification(_historic_diffs):
    email = False

    for time in _historic_diffs:
        entry = _historic_diffs[time]

        if len(entry["added"]) > 0:
            email = True
            break

        for sheet in entry["diffs"]:
            for diff in sheet["diff"]:
                if match(diff, os.getenv("MATCH_STRING")):
                    email = True
                    print("Match found:", diff)
                    break

        send_to_others(entry, time)

    if email:
        send_email(data_to_html(_historic_diffs, os.getenv("MATCH_STRING")), os.getenv('RECEIVER_EMAIL'))
        return True

    return False


EMAILS_FILE = 'emails.json'


def send_to_others(entry, time):
    emails = json.load(open(EMAILS_FILE))

    for email_entry in emails:
        name, email = itemgetter('name', 'email')(email_entry)
        should_send_email = False
        if len(entry["added"]) > 0:
            should_send_email = True
        else:
            for sheet in entry["diffs"]:
                for diff in sheet["diff"]:
                    if match(diff, name):
                        should_send_email = True
                        print(f"Match found for {name}:", diff)
                        break

        if should_send_email:
            send_email(data_to_html({time: entry}, name), email)


if __name__ == "__main__":
    historic_diffs = json.load(open("data/diff/matched_diff.json"))
    print(send_notification(historic_diffs))
