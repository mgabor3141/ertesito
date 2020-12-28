import json
import os
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


VOWELS = ['a', 'á', 'e', 'é', 'i', 'í', 'o', 'ó', 'ö', 'ő', 'u', 'ú', 'ü', 'ű']


def data_to_html(added, removed, name):
    html = "<h1>Jelentés változásokról</h1>"

    html += f"<p>Kedves {name}!</p>"
    html += f"<p>Változás történt az ambuláns beosztásodban:</p>"

    if len(added) > 0:
        html += f"<h2>Hozzáadott bejegyzések</h2><p>"

        for entry in added:
            html += f"<u>{print_path(entry[0])}:</u> {entry[1]}"

        html += "</p>"

    if len(removed) > 0:
        html += f"<h2>Törölt bejegyzések</h2><p>"

        for entry in removed:
            html += f"<u>{print_path(entry[0])}:</u> <strike>{entry[1]}</strike>"

        html += "</p>"

    html += "<hr/><small>A táblázat napközben óránként van ellenőrizve. (07-22)<br /> \
            Válaszlevélben jelezd, ha kérésed vagy kérdésed van, illetve ha nem szeretnél több ilyen értesítést kapni.<br/>\
            Az adatok tájékoztató jellegűek, a helyességükért illetve teljességükért felelősséget senki nem vállal.</small>"

    return html


def match(entry, name):
    return fuzz.token_set_ratio(entry[1], name) >= 92


def send_notifications(added, removed):
    emails = json.load(open(os.getenv('USERS_FILE')))

    for email_entry in emails:
        name, email = itemgetter('name', 'email')(email_entry)

        added_matches = [entry for entry in added if match(entry, name)]
        removed_matches = [entry for entry in removed if match(entry, name)]

        if len(added_matches) > 0 or len(removed_matches):
            send_email(data_to_html(added_matches, removed_matches, name), email)


if __name__ == "__main__":
    _added = [
        (('Január Ambulancia', '2021.01.01.', 'péntek', 'I Műszak', 'Pretriázs'), 'Pretriázs: NAME')
    ]

    _removed = [
        (('Január Ambulancia', '2021.01.01.', 'péntek', 'I Műszak', 'Pretriázs'), 'Pretriázs: NAME')
    ]

    print(send_notifications(_added, _removed))
