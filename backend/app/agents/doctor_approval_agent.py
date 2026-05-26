from uuid import uuid4
from app.db import Database
from app.graph.state import BookingState

class DoctorApprovalAgent:
    def __init__(self, db: Database):
        self.db = db

    def run(self, state: BookingState) -> BookingState:
        slot = state.get('selected_slot')
        if not slot:
            state['status'] = 'needs_new_availability'; return state
        if state.get('appointment_id'):
            state['status'] = 'pending_doctor'; return state
        aid = str(uuid4())
        state['appointment_id'] = aid
        self.db.create_appointment({'id':aid,'session_id':state['session_id'],'patient_name':state['patient_name'],'patient_email':state['patient_email'],'reason':state['reason'],'treatment':state['treatment'],'duration_minutes':state['duration_minutes'],'selected_slot':slot,'status':'pending_doctor'})
        state['status'] = 'pending_doctor'
        state['bot_response'] = f"I found a possible appointment for {state['treatment']} on {slot['label']}. I sent it to the doctor for approval."
        state.setdefault('messages', []).append({'role':'assistant','content':state['bot_response']})
        return state
