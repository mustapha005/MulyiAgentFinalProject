from app.services.calendar_service import CalendarService
from app.services.email_service import EmailService

class NotificationAgent:
    def __init__(self, calendar_service: CalendarService, email_service: EmailService):
        self.calendar_service = calendar_service
        self.email_service = email_service

    def confirm(self, appointment: dict) -> tuple[str, str]:
        event_id = self.calendar_service.create_event(appointment['patient_name'], appointment['patient_email'], appointment['treatment'], appointment['selected_slot'])
        email_id = self.email_service.send_confirmation(appointment['patient_name'], appointment['patient_email'], appointment['treatment'], appointment['selected_slot'])
        return event_id, email_id
