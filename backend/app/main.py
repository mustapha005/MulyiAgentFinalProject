from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.agents.notification_agent import NotificationAgent
from app.config import Settings, get_settings
from app.db import Database
from app.graph.workflow import BookingWorkflow
from app.models import ChatRequest, ChatResponse, DoctorDecisionRequest, DoctorDecisionResponse
from app.services.calendar_service import GoogleCalendarService, MockCalendarService
from app.services.email_service import GmailApiEmailService, MockEmailService, SMTPEmailService
from app.prompts import SMILEFLOW_SYSTEM_PROMPT
from app.services.llm_service import get_llm_service


MAX_MEMORY_MESSAGES = 20


def append_conversation_message(state: dict, role: str, content: str) -> dict:
    history = state.get("conversation_history", [])

    history.append({
        "role": role,
        "content": content,
    })

    state["conversation_history"] = history[-MAX_MEMORY_MESSAGES:]
    return state


def format_conversation_history(state: dict) -> str:
    history = state.get("conversation_history", [])[-MAX_MEMORY_MESSAGES:]

    if not history:
        return "No previous conversation."

    return "\n".join(
        f"{message['role']}: {message['content']}"
        for message in history
    )






def patient_can_choose_slot(status: str) -> bool:
    return status in {
        "slots_found",
        "reschedule_options_available",
        "reschedule_needed",
    }


def get_patient_visible_slots(state: dict) -> list:
    status = state.get("status", "unknown")

    if not patient_can_choose_slot(status):
        return []

    return state.get("candidate_slots", [])


def slot_key(slot: dict) -> tuple:
    return (
        slot.get("start"),
        slot.get("end"),
        slot.get("label"),
    )


def build_alternative_slots(state: dict, appt: dict) -> list:
    selected_slot = appt.get("selected_slot") or state.get("selected_slot")
    old_candidate_slots = state.get("candidate_slots", [])

    if not old_candidate_slots:
        return []

    if not selected_slot:
        return old_candidate_slots

    selected_key = slot_key(selected_slot)

    alternatives = [
        slot
        for slot in old_candidate_slots
        if slot_key(slot) != selected_key
    ]

    return alternatives

















app = FastAPI(title='SmileFlow API', version='0.1.0')
_settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=_settings.cors_origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def get_db(settings: Settings = Depends(get_settings)) -> Database:
    return Database(settings.database_url)

def get_calendar_service(settings: Settings = Depends(get_settings)):
    if settings.app_mode == 'google':
        return GoogleCalendarService(settings.google_credentials_file, settings.google_calendar_token_file, settings.google_calendar_id, settings.timezone)
    return MockCalendarService(settings.timezone)

def get_email_service(settings: Settings = Depends(get_settings)):
    if settings.app_mode == 'google' and settings.email_provider == 'gmail_api':
        return GmailApiEmailService(settings.google_credentials_file, settings.google_gmail_token_file, settings.email_from)
    if settings.app_mode == 'google' and settings.email_provider == 'smtp' and settings.smtp_user and settings.smtp_password and settings.email_from:
        return SMTPEmailService(settings.smtp_host, settings.smtp_port, settings.smtp_user, settings.smtp_password, settings.email_from)
    return MockEmailService()

@app.get('/api/health')
def health(settings: Settings = Depends(get_settings)) -> dict:
    return {'status': 'ok', 'app': settings.app_name, 'mode': settings.app_mode, 'email_provider': settings.email_provider, "llm_provider": settings.llm_provider,
        "ollama_model": settings.ollama_model,}




@app.post('/api/chat', response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Database = Depends(get_db),
    calendar_service=Depends(get_calendar_service),
) -> ChatResponse:
    workflow = BookingWorkflow(
        db,
        calendar_service,
        Path(__file__).resolve().parents[1] / 'knowledge_base',
    )

    state = db.get_session_state(request.session_id)

    state['session_id'] = request.session_id
    state['user_message'] = request.message

    # Save patient message in memory
    state = append_conversation_message(
        state,
        role="patient",
        content=request.message,
    )

    conversation_history = format_conversation_history(state)

    new_state = workflow.run_turn(state)

    # Original safe workflow response
    reply = new_state.get(
        'bot_response',
        'I am ready to help.'
    )
    SKIP_LLM_REWRITE_STATUSES = {'pending_doctor', 'confirmed', 'no_slots' , 'slot_confirmed', 
    'reschedule_options_available', 
    'reschedule_needed',}

    # Optional Ollama rewrite layer
    llm = get_llm_service()
    if llm is not None and new_state.get('status') not in SKIP_LLM_REWRITE_STATUSES:  # ADD THIS CHECK

        llm_input = f"""
Conversation history:
{conversation_history}

Latest patient message:
{request.message}

Current safe workflow response:
{reply}

Current workflow status:
{new_state.get('status', 'unknown')}

Appointment ID:
{new_state.get('appointment_id')}

Candidate slots:
{new_state.get('candidate_slots', [])}

Rewrite the current safe workflow response in a natural, friendly dental clinic assistant style.

Important rules:
- Use the conversation history to remember previous details.
- Do not change the appointment status.
- Do not say the appointment is confirmed unless the safe workflow response says it is confirmed.
- Do not invent calendar slots.
- Do not invent patient information.
- Do not give medical diagnosis.
- Keep the response short and professional.
- NEVER choose or select a time slot on behalf of the patient.   # ADD THIS
- If there are candidate slots, LIST them and ASK the patient to choose one. # ADD THIS
- Output ONLY the message to send to the patient. No preamble, no meta-commentary,  # ADD
  no phrases like 'Here is a rewritten response'. Just the message itself.
"""

        llm_result = llm.generate(
            system_prompt=SMILEFLOW_SYSTEM_PROMPT,
            user_message=llm_input,
        )

        if llm_result.used_llm and llm_result.content.strip():
             cleaned = llm_result.content.strip()

    
    # Save final assistant reply in memory
    new_state = append_conversation_message(
        new_state,
        role="assistant",
        content=reply,
    )

    new_state['bot_response'] = reply

    db.save_session_state(request.session_id, new_state)

    return ChatResponse(
        session_id=request.session_id,
        reply=reply,
        status=new_state.get('status', 'unknown'),
        appointment_id=new_state.get('appointment_id'),
        candidate_slots=get_patient_visible_slots(new_state),
    )




@app.get("/api/session/{session_id}")
def get_session_state(
    session_id: str,
    db: Database = Depends(get_db),
):
    state = db.get_session_state(session_id)

    return {
        "session_id": session_id,
        "status": state.get("status", "unknown"),
        "bot_response": state.get("bot_response"),
        "appointment_id": state.get("appointment_id"),
        "candidate_slots": get_patient_visible_slots(state),
        "conversation_history": state.get("conversation_history", []),
    }














@app.get('/api/doctor/pending')
def pending(db: Database = Depends(get_db)) -> list[dict]:
    return db.pending_appointments()




@app.post('/api/doctor/appointments/{appointment_id}/decision', response_model=DoctorDecisionResponse)
def decision(
    appointment_id: str,
    request: DoctorDecisionRequest,
    db: Database = Depends(get_db),
    calendar_service=Depends(get_calendar_service),
    email_service=Depends(get_email_service),
) -> DoctorDecisionResponse:
    appt = db.get_appointment(appointment_id)

    if not appt:
        raise HTTPException(status_code=404, detail='Appointment not found')

    if appt['status'] != 'pending_doctor':
        raise HTTPException(
            status_code=400,
            detail=f"Appointment is already {appt['status']}",
        )

    session_id = appt['session_id']
    state = db.get_session_state(session_id)

    # ---------------------------------------------------------
    # Doctor declined appointment
    # ---------------------------------------------------------
    if request.decision == 'decline':
        db.update_appointment_status(
            appointment_id,
            'declined',
            request.note,
        )

        alternative_slots = build_alternative_slots(state, appt)

        if alternative_slots:
            slot_labels = "\n".join(
                f"- {slot.get('label', 'Available slot')}"
                for slot in alternative_slots[:3]
            )

            patient_message = (
                "The doctor declined the previous proposed appointment time. "
                "No problem — here are other available options:\n\n"
                f"{slot_labels}\n\n"
                "Please choose one of these options, or send me another day or hour."
            )

            new_status = "reschedule_options_available"

        else:
            patient_message = (
                "The doctor declined the previous proposed appointment time. "
                "Could you please send me another day or hour so I can search again?"
            )

            new_status = "reschedule_needed"

        state.update({
            "status": new_status,
            "bot_response": patient_message,
            "appointment_id": None,
            "candidate_slots": alternative_slots,
            "selected_slot": None,

            # Keep these. Do not clear them.
            "preferred_times": state.get("preferred_times", []),
        })

        state = append_conversation_message(
            state,
            role="assistant",
            content=patient_message,
        )

        db.save_session_state(session_id, state)

        return DoctorDecisionResponse(
            appointment_id=appointment_id,
            status='declined',
            message='Appointment declined. The patient has been asked to choose another option.',
        )

    # ---------------------------------------------------------
    # Doctor approved appointment
    # ---------------------------------------------------------
    event_id, email_id = NotificationAgent(
        calendar_service,
        email_service,
    ).confirm(appt)

    db.update_appointment_status(
        appointment_id,
        'confirmed',
        request.note,
        event_id,
    )

    approved_message = (
        f"Good news! The doctor approved your appointment for "
        f"{appt['selected_slot']['label']}. A confirmation email has been sent."
    )

    state["status"] = "confirmed"
    state["bot_response"] = approved_message
    state["candidate_slots"] = []
    state["selected_slot"] = None

    state = append_conversation_message(
        state,
        role="assistant",
        content=approved_message,
    )

    db.save_session_state(session_id, state)

    return DoctorDecisionResponse(
        appointment_id=appointment_id,
        status='confirmed',
        message=f'Appointment confirmed. Calendar event: {event_id}. Email: {email_id}.',
    )







@app.get("/api/llm-test")
def llm_test():
    settings = get_settings()
    llm = get_llm_service()

    if llm is None:
        return {
            "used_llm": False,
            "reply": None,
            "error": "LLM provider is not set to ollama",
            "provider": settings.llm_provider,
            "model": settings.ollama_model,
        }

    result = llm.generate(
        system_prompt="Reply only with OLLAMA_OK.",
        user_message="Test message.",
    )

    return {
        "used_llm": result.used_llm,
        "reply": result.content.strip(),
        "error": result.error,
        "provider": settings.llm_provider,
        "model": settings.ollama_model,
    }
