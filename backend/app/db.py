import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

class Database:
    def __init__(self, database_url: str):
        if not database_url.startswith('sqlite:///'):
            raise ValueError('Use sqlite:///./smileflow.db for this starter project')
        self.db_path = Path(database_url.replace('sqlite:///', '', 1))
        self.init_db()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self):
        with self.connect() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, state_json TEXT NOT NULL)')
            conn.execute('''CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                patient_name TEXT NOT NULL,
                patient_email TEXT NOT NULL,
                reason TEXT NOT NULL,
                treatment TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                selected_slot_json TEXT NOT NULL,
                status TEXT NOT NULL,
                doctor_note TEXT,
                calendar_event_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

    def get_session_state(self, session_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute('SELECT state_json FROM sessions WHERE session_id=?', (session_id,)).fetchone()
        return json.loads(row['state_json']) if row else {'session_id': session_id, 'messages': []}

    def save_session_state(self, session_id: str, state: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute('''INSERT INTO sessions(session_id,state_json) VALUES (?,?)
                ON CONFLICT(session_id) DO UPDATE SET state_json=excluded.state_json''',
                (session_id, json.dumps(state, ensure_ascii=False)))

    def create_appointment(self, appointment: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute('''INSERT INTO appointments
                (id,session_id,patient_name,patient_email,reason,treatment,duration_minutes,selected_slot_json,status,doctor_note)
                VALUES (?,?,?,?,?,?,?,?,?,?)''',
                (appointment['id'], appointment['session_id'], appointment['patient_name'], appointment['patient_email'],
                 appointment['reason'], appointment['treatment'], appointment['duration_minutes'],
                 json.dumps(appointment['selected_slot'], ensure_ascii=False), appointment['status'], appointment.get('doctor_note')))

    def pending_appointments(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM appointments WHERE status='pending_doctor' ORDER BY created_at DESC").fetchall()
        return [self._row(row) for row in rows]

    def get_appointment(self, appointment_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM appointments WHERE id=?', (appointment_id,)).fetchone()
        return self._row(row) if row else None

    def update_appointment_status(self, appointment_id: str, status: str, doctor_note: str | None = None, calendar_event_id: str | None = None):
        with self.connect() as conn:
            conn.execute('''UPDATE appointments SET status=?, doctor_note=?, calendar_event_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?''',
                         (status, doctor_note, calendar_event_id, appointment_id))

    @staticmethod
    def _row(row):
        data = dict(row)
        data['selected_slot'] = json.loads(data.pop('selected_slot_json'))
        return data
