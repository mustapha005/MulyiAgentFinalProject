from __future__ import annotations
import re
from app.graph.state import BookingState

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
NAME_PATTERNS = [re.compile(r"my name is ([A-Za-zÀ-ÿ' -]{2,})", re.I), re.compile(r"i am ([A-Za-zÀ-ÿ' -]{2,})", re.I), re.compile(r"i'm ([A-Za-zÀ-ÿ' -]{2,})", re.I)]
REASONS = {'pain':'Tooth pain consultation','toothache':'Tooth pain consultation','clean':'Dental cleaning','whitening':'Teeth whitening','extract':'Tooth extraction','implant':'Implant consultation','braces':'Braces consultation','swelling':'Emergency swelling'}
TIME_WORDS = ['monday','tuesday','wednesday','thursday','friday','morning','afternoon','evening','tomorrow','lundi','mardi','mercredi','jeudi','vendredi','matin','après','apres']

SLOT_SELECTION_STATUSES = {
    'slots_found',
    'reschedule_options_available', 
    'reschedule_needed',
}

class PatientIntakeAgent:
    def run(self, state: BookingState) -> BookingState:
        msg = state.get('user_message', '')
        state.setdefault('messages', []).append({'role': 'patient', 'content': msg})

        # If patient is responding to a slot list, don't re-run intake logic.
        # Let the workflow route to slot_selection instead.
        if state.get('status') in SLOT_SELECTION_STATUSES:
            return state

        state['patient_email'] = state.get('patient_email') or self.extract_email(msg)
        state['patient_name'] = state.get('patient_name') or self.extract_name(msg)
        state['reason'] = state.get('reason') or self.extract_reason(msg)

        availability = self.extract_availability(msg)
        if availability:
            times = state.setdefault('preferred_times', [])
            if availability not in times:
                times.append(availability)

        missing = self.missing(state)
        if missing:
            state['status'] = 'collecting'
            state['bot_response'] = self.ask(missing[0], state)
            state['messages'].append({'role': 'assistant', 'content': state['bot_response']})
        else:
            state['status'] = 'intake_complete'

        return state


    @staticmethod
    def extract_email(text):
        m = EMAIL_RE.search(text); return m.group(0) if m else None

    @staticmethod
    def extract_name(text):
        for p in NAME_PATTERNS:
            m = p.search(text)
            if m:
                raw = re.split(r"\b(my email|email|and|i have|available|want|need)\b", m.group(1), flags=re.I)[0]
                return raw.strip(' .,')
        return None

    @staticmethod
    def extract_reason(text):
        low = text.lower()
        for k,v in REASONS.items():
            if k in low: return v
        return 'Dental consultation' if any(x in low for x in ['appointment','visit','consultation']) else None

    @staticmethod
    def extract_availability(text):
        low = text.lower()
        return text.strip() if any(w in low for w in TIME_WORDS) or re.search(r"\b\d{1,2}(:\d{2})?\b", low) else None

    @staticmethod
    def missing(state):
        out = []
        if not state.get('patient_name'): out.append('name')
        if not state.get('patient_email'): out.append('email')
        if not state.get('reason'): out.append('reason')
        if not state.get('preferred_times'): out.append('availability')
        return out

    @staticmethod
    def ask(field, state):
        questions = {
            'name':'What is your full name?',
            'email':'What email should we use for confirmation?',
            'reason':'What is the reason for your visit? For example cleaning, pain, whitening, extraction.',
            'availability':'When are you available? Please give one or two date/time options.'
        }
        return 'Thanks. ' + questions[field]
