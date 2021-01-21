import json
import os
from operator import itemgetter

from fuzzywuzzy import fuzz, process

from send_email import send_email


def print_value(value):
    if value == "":
        return "[üres]"
    return value


def print_path(path):
    if len(path) == 0:
        return "?"

    return " / ".join(path[1:])


VOWELS = ['a', 'á', 'e', 'é', 'i', 'í', 'o', 'ó', 'ö', 'ő', 'u', 'ú', 'ü', 'ű']


def data_to_html(added, removed, name):
    html = f"<p>Kedves {name}!</p>"
    html += f"<p>Változás történt az ambuláns beosztásodban:</p>"

    if len(removed) > 0:
        html += f"<h3>Törölt bejegyzés{'ek' if len(removed) > 1 else ''}:</h3><p>"

        for entry in removed:
            html += f"<u>{print_path(entry[0])}:</u> <strike>{entry[1]}</strike> <br />"

        html += "</p>"

    if len(added) > 0:
        html += f"<h3>Új bejegyzés{'ek' if len(added) > 1 else ''}:</h3><p>"

        for entry in added:
            html += f"<u>{print_path(entry[0])}:</u> {entry[1]}<br />"

        html += "</p>"

    html += "<br /><p>A táblázatok: \
            <a href='https://docs.google.com/spreadsheets/d/1rIOy7sKY3rZb90BSTl3pLZoDn806k9Zm-ht_JyWkikc/edit'>2021 Ambulancia</a> \
            <a href='https://docs.google.com/spreadsheets/d/1k8xgA9KElpYedTPuWkXu-elobqWujw2fh1URE48OVsQ/edit'>2021 Éjszaka</a></p>"

    html += "<hr/><small>A táblázat óránként van ellenőrizve, a személyre szóló naptárad is ezzel egyszerre frissül.<br /> \
            Válaszlevélben jelezd, ha kérésed vagy kérdésed van, illetve ha nem szeretnél több ilyen értesítést kapni.<br/>\
            Az adatok tájékoztató jellegűek, a helyességükért vagy teljességükért felelősséget senki nem vállal.<br/>\
            <small>Verzió: 2.3.1</small></small>"

    return html


def match(entry, name, names):
    results = process.extract(entry[1], names, scorer=fuzz.partial_ratio)

    result, primary_score = results[0]
    secondary_score = results[1][1]

    return result == name and primary_score >= 90 and secondary_score < 90


def send_notifications(added, removed):
    users = json.load(open(os.getenv('USERS_FILE'), encoding="utf8"))
    names = [user['name'] for user in users]

    for email_entry in users:
        name, email = itemgetter('name', 'email')(email_entry)

        added_matches = sorted([entry for entry in added if match(entry, name, names)])
        removed_matches = sorted([entry for entry in removed if match(entry, name, names)])

        if len(added_matches) > 0 or len(removed_matches):
            send_email(data_to_html(added_matches, removed_matches, name), email)


if __name__ == "__main__":
    _added = [
        (('2021 Ambulancia', 'Január Ambulancia', '2021.01.01.', 'péntek', 'I Műszak', 'Pretriázs'),
         'Pretriázs: dr. Magyar Gábor')
    ]

    _removed = [
        (('2021 Ambulancia', 'Január Ambulancia', '2021.01.01.', 'péntek', 'I Műszak', 'Pretriázs'),
         'Pretriázs: dr. Svidro Eszter')
    ]

    print(send_notifications(_added, _removed))
