from typing import Any, TypedDict

class BookingState(TypedDict, total=False):
    session_id: str
    user_message: str
    messages: list[dict[str, str]]
    patient_name: str | None
    patient_email: str | None
    reason: str | None
    preferred_times: list[str]
    treatment: str | None
    duration_minutes: int
    rag_context: list[dict[str, Any]]
    emergency: bool
    candidate_slots: list[dict[str, str]]
    selected_slot: dict[str, str] | None
    appointment_id: str | None
    status: str
    bot_response: str
