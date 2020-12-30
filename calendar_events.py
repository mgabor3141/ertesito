import json
import os
import re

import unicodedata
from operator import itemgetter
from pprint import pprint
from datetime import datetime, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from send_notification import match


def authorize():
    credentials = service_account.Credentials.from_service_account_file(
        'calendar-service-account.json', scopes=['https://www.googleapis.com/auth/calendar'])

    service = build('calendar', 'v3', credentials=credentials)

    return service


calendar = authorize()


id_disallowed_chars = re.compile(r'[^a-v0-9]')


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def path_to_event_id(path):
    return id_disallowed_chars.sub("00", strip_accents("".join(path).lower()))


def muszak_to_time(muszak, date):
    start_time, end_time = None, None
    end_date_offset = 0

    day = date.isoweekday()
    week = date.isocalendar()[1]

    if muszak == 3:
        start_time = "20:00:00"
        end_time = "08:00:00"
        end_date_offset = 1
    elif day == 6 or day == 7:
        start_time = "07:30:00"
        end_time = "19:30:00"
    elif muszak == 1 or muszak == 2:
        if day == 5:  # Friday
            delelott = bool(week % 2)
        else:
            delelott = not bool(day % 2)

        if muszak == 2:
            delelott = not delelott

        if delelott:
            start_time = "07:30:00"   # fel 8 - fel2 ; fel 2 - fel 8
            end_time = "13:30:00"
        else:
            start_time = "13:30:00"
            end_time = "19:30:00"

    return start_time, end_time, end_date_offset


muszak1 = re.compile(r'(i|1)\.?\smuszak|muszak\s(i|1)\.?')
muszak2 = re.compile(r'(ii|2)\.?\smuszak|muszak\s(ii|2)\.?')
ejszaka = re.compile(r'ejszaka')
protetika = re.compile(r'protetika')
szajseb = re.compile(r'szajsebeszeti?\sgyakorlat')

date_formats = [
    "%Y.%m.%d.",
    "%Y.%m.%d",
    "%Y-%m-%d",
]


def entry_to_event(entry):
    path, value = entry

    title = path[0].replace("2021 ", "")  # Sheet title
    date, muszak = None, None

    for path_element in path:
        node = strip_accents(path_element.strip().lower())

        if muszak2.search(node) is not None:
            muszak = 2
            continue

        if muszak1.search(node) is not None:
            muszak = 1
            continue

        if ejszaka.search(node) is not None:
            muszak = 3  # Ejszakai muszak
            continue

        if szajseb.search(node):
            title = 'Szájsebészet gyakorlat'
            continue

        if node == "pretriazs" or node == "orvos" or node == "szajsebesz" or node == "rezidens" or node == "annotalas" or protetika.search(node):
            title += ' ' + path_element.strip()
            continue

        for date_format in date_formats:
            try:
                date = datetime.strptime(node, date_format)
                continue
            except ValueError:
                pass

    if not (title and date and path):
        return None

    start_time, end_time, end_date_offset = muszak_to_time(muszak, date)

    if start_time and end_time:
        timing = {
            "start": {
                "dateTime": f"{date.date().isoformat()}T{start_time}",
                "timeZone": "Europe/Budapest"
            },
            "end": {
                "dateTime": f"{(date + timedelta(days=end_date_offset)).date().isoformat()}T{end_time}",
                "timeZone": "Europe/Budapest"
            },
        }
    else:
        timing = {
            "start": {
                "date": date.date().isoformat(),
            },
            "end": {
                "date": (date + timedelta(days=end_date_offset)).date().isoformat(),
            },
        }

    return {
        **timing,
        "summary": title,
        "id": path_to_event_id(path),
        "description": f"Eredeti bejegyzés:<br />{' / '.join(path)}: <i>{value}</i>"
    }


def add_event(calendar_id, entry):
    print("Adding", entry)
    event = entry_to_event(entry)

    if not event:
        print("Something went wrong trying to convert the above entry to an event")
        return

    try:
        calendar.events().insert(calendarId=calendar_id, body=event).execute()
    except HttpError as e:
        if e.resp.status == 409:
            # 409, id in use
            calendar.events().update(calendarId=calendar_id, eventId=event['id'], body=event).execute()
        else:
            raise e


def remove_event(calendar_id, event_id):
    calendar.events().delete(calendarId=calendar_id, eventId=event_id).execute()


def full_sync(entries):
    users = json.load(open(os.getenv('USERS_FILE')))

    for user in users:
        name, email, calendar_id = itemgetter('name', 'email', 'calendar')(user)

        # Skip if user doesn't have calendar enabled
        if not calendar_id:
            continue

        print("Processing calendar for", name)

        user_entries = [entry for entry in entries if match(entry, name)]

        # Local events
        entry_ids = set([path_to_event_id(item[0]) for item in user_entries])

        # Get events from calendar
        events_in_calendar = set([item['id'] for item in calendar.events().list(
            calendarId=calendar_id,
            pageToken=None,
            maxResults=2500,
            fields="items(id)").execute()["items"]]
        )

        # Add / update all entries
        # for entry in user_entries:
        #     add_event(calendar_id, entry)

        # Add missing entries
        for entry in [entry for entry in user_entries if path_to_event_id(entry[0]) in entry_ids - events_in_calendar]:
            add_event(calendar_id, entry)

        # Remove entries that are no longer valid
        for event_id in events_in_calendar - entry_ids:
            remove_event(calendar_id, event_id)


if __name__ == "__main__":
    # ###### Calendar creation

    # result = calendar.calendars().insert(body={
    #     "summary": "NAME"
    # }).execute()
    #
    # print(result["id"])
    #
    # result = calendar.acl().insert(calendarId=result["id"], body={
    #     'scope': {
    #         'type': 'user',
    #         'value': os.getenv("SENDER_EMAIL")
    #     },
    #     'role': 'owner'
    # }).execute()

    pprint(calendar.calendarList().list().execute())