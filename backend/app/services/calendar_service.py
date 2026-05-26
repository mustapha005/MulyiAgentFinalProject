from __future__ import annotations

from datetime import datetime, timedelta, time
from typing import Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.services.google_auth import build_google_service


class CalendarService(Protocol):
    def find_free_slots(self, duration_minutes: int, preferred_times: list[str]) -> list[dict[str, str]]: ...
    def create_event(self, patient_name: str, patient_email: str, treatment: str, slot: dict[str, str]) -> str: ...


def safe_zoneinfo(timezone: str):
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo('UTC')


class MockCalendarService:
    def __init__(self, timezone: str = 'Africa/Casablanca'):
        self.timezone = timezone
        self.tz = safe_zoneinfo(timezone)

    def find_free_slots(self, duration_minutes: int, preferred_times: list[str]) -> list[dict[str, str]]:
        candidates = candidate_slots(duration_minutes, preferred_times, self.tz)
        return candidates[:3]

    def create_event(self, patient_name: str, patient_email: str, treatment: str, slot: dict[str, str]) -> str:
        return 'mock-event-' + patient_name.lower().replace(' ', '-') + '-' + slot['start'][:10]


class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, credentials_file: str, token_file: str, calendar_id: str, timezone: str):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.calendar_id = calendar_id
        self.timezone = timezone
        self.tz = safe_zoneinfo(timezone)
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = build_google_service(
                'calendar', 'v3', self.credentials_file, self.token_file, self.SCOPES
            )
        return self._service

    def find_free_slots(self, duration_minutes: int, preferred_times: list[str]) -> list[dict[str, str]]:
        candidates = candidate_slots(duration_minutes, preferred_times, self.tz)
        if not candidates:
            return []

        time_min = candidates[0]['start']
        time_max = candidates[-1]['end']
        body = {
            'timeMin': time_min,
            'timeMax': time_max,
            'timeZone': self.timezone,
            'items': [{'id': self.calendar_id}],
        }
        freebusy = self.service.freebusy().query(body=body).execute()
        busy_periods = freebusy.get('calendars', {}).get(self.calendar_id, {}).get('busy', [])

        free_slots = []
        for slot in candidates:
            if not overlaps_busy(slot, busy_periods):
                free_slots.append(slot)
            if len(free_slots) == 3:
                break
        return free_slots

    def create_event(self, patient_name: str, patient_email: str, treatment: str, slot: dict[str, str]) -> str:
        body = {
            'summary': f'Dental appointment - {patient_name}',
            'description': (
                f'Patient: {patient_name}\n'
                f'Email: {patient_email}\n'
                f'Treatment: {treatment}\n'
                'Created by SmileFlow after doctor approval.'
            ),
            'start': {'dateTime': slot['start'], 'timeZone': self.timezone},
            'end': {'dateTime': slot['end'], 'timeZone': self.timezone},
            'attendees': [{'email': patient_email}],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        event = self.service.events().insert(
            calendarId=self.calendar_id,
            body=body,
            sendUpdates='all',
        ).execute()
        return event.get('id', 'google-event-created')


def candidate_slots(duration_minutes: int, preferred_times: list[str], tz: ZoneInfo) -> list[dict[str, str]]:
    now = datetime.now(tz)
    preferred = ' '.join(preferred_times).lower()
    weekdays = parse_weekdays(preferred)
    hours = parse_hours(preferred)
    slots: list[dict[str, str]] = []
    for offset in range(1, 21):
        day = (now + timedelta(days=offset)).date()
        if day.weekday() >= 5:
            continue
        if weekdays and day.weekday() not in weekdays:
            continue
        for h in hours:
            start = datetime.combine(day, time(hour=h), tzinfo=tz)
            if start <= now:
                continue
            end = start + timedelta(minutes=duration_minutes)
            slots.append({
                'start': start.isoformat(),
                'end': end.isoformat(),
                'label': start.strftime('%A %d %B at %H:%M'),
            })
    return slots


def parse_weekdays(text: str) -> list[int]:
    data = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4,
        'lundi': 0, 'mardi': 1, 'mercredi': 2, 'jeudi': 3, 'vendredi': 4,
    }
    return sorted({v for k, v in data.items() if k in text})


def parse_hours(text: str) -> list[int]:
    if any(x in text for x in ['morning', 'matin']):
        return [9, 10, 11]
    if any(x in text for x in ['afternoon', 'evening', 'après', 'apres', 'soir']):
        return [14, 15, 16]
    return [9, 10, 11, 14, 15, 16]


def overlaps_busy(slot: dict[str, str], busy_periods: list[dict[str, str]]) -> bool:
    slot_start = datetime.fromisoformat(slot['start'])
    slot_end = datetime.fromisoformat(slot['end'])
    for busy in busy_periods:
        busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
        busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
        if slot_start < busy_end and slot_end > busy_start:
            return True
    return False
