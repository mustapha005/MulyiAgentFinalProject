from __future__ import annotations

import base64
import smtplib
from email.message import EmailMessage
from typing import Protocol

from app.services.google_auth import build_google_service


class EmailService(Protocol):
    def send_confirmation(self, patient_name: str, patient_email: str, treatment: str, slot: dict[str, str]) -> str: ...


class MockEmailService:
    def send_confirmation(self, patient_name: str, patient_email: str, treatment: str, slot: dict[str, str]) -> str:
        return f'mock-email-sent-to-{patient_email}'


class GmailApiEmailService:
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    def __init__(self, credentials_file: str, token_file: str, email_from: str | None = None):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.email_from = email_from or 'me'
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = build_google_service(
                'gmail', 'v1', self.credentials_file, self.token_file, self.SCOPES
            )
        return self._service

    def send_confirmation(self, patient_name: str, patient_email: str, treatment: str, slot: dict[str, str]) -> str:
        msg = EmailMessage()
        if self.email_from != 'me':
            msg['From'] = self.email_from
        msg['To'] = patient_email
        msg['Subject'] = 'Dental appointment confirmation'
        msg.set_content(
            f'Hello {patient_name},\n\n'
            f'Your appointment for {treatment} is confirmed: {slot.get("label", slot.get("start"))}.\n\n'
            'Please arrive 10 minutes early.\n\n'
            'Best regards,\nSmileFlow Dental Clinic\n'
        )
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        sent = self.service.users().messages().send(userId='me', body={'raw': raw}).execute()
        return sent.get('id', f'gmail-sent-to-{patient_email}')


class SMTPEmailService:
    def __init__(self, host: str, port: int, user: str, password: str, email_from: str):
        self.host, self.port, self.user, self.password, self.email_from = host, port, user, password, email_from

    def send_confirmation(self, patient_name: str, patient_email: str, treatment: str, slot: dict[str, str]) -> str:
        msg = EmailMessage()
        msg['From'] = self.email_from
        msg['To'] = patient_email
        msg['Subject'] = 'Dental appointment confirmation'
        msg.set_content(f'Hello {patient_name},\n\nYour appointment for {treatment} is confirmed: {slot.get("label", slot.get("start"))}.\n\nPlease arrive 10 minutes early.\n')
        with smtplib.SMTP(self.host, self.port) as server:
            server.starttls(); server.login(self.user, self.password); server.send_message(msg)
        return f'email-sent-to-{patient_email}'
