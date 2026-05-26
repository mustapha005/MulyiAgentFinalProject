from pathlib import Path
from app.agents.calendar_agent import CalendarAgent
from app.agents.doctor_approval_agent import DoctorApprovalAgent
from app.agents.intake_agent import PatientIntakeAgent
from app.agents.rag_agent import RAGAgent
from app.db import Database
from app.graph.state import BookingState
from app.services.calendar_service import CalendarService
from app.services.rag_store import ClinicRAGStore


class BookingWorkflow:
    def __init__(self, db: Database, calendar_service: CalendarService, knowledge_dir: Path):
        self.intake = PatientIntakeAgent()
        self.rag = RAGAgent(ClinicRAGStore(knowledge_dir))
        self.calendar = CalendarAgent(calendar_service)
        self.doctor = DoctorApprovalAgent(db)
        self.graph = self._build_graph()

    def _build_graph(self):
        try:
            from langgraph.checkpoint.memory import MemorySaver
            from langgraph.graph import END, StateGraph
        except Exception:
            return None

        g = StateGraph(BookingState)
        g.add_node('intake', self.intake.run)
        g.add_node('rag', self.rag.run)
        g.add_node('calendar', self.calendar.run)
        g.add_node('slot_selection', self._handle_slot_selection)  # NEW NODE
        g.add_node('doctor_approval', self.doctor.run)

        g.set_entry_point('intake')

        # After intake: stop to collect info, or continue to rag
        g.add_conditional_edges(
            'intake',
            self._after_intake,
            {
                'stop': END,               # still collecting patient info
                'select_slot': 'slot_selection',  # patient is choosing a slot
                'continue': 'rag',         # all info collected, search calendar
            }
        )

        g.add_edge('rag', 'calendar')

        # After calendar: STOP to show slots to patient — never auto-proceed
        g.add_conditional_edges(
            'calendar',
            self._after_calendar,
            {
                'stop': END,     # no slots found OR slots found → both stop, patient must respond
                'continue': 'doctor_approval',  # only if slot already confirmed by patient
            }
        )

        # After slot selection: if valid choice go to doctor, else stop and re-ask
        g.add_conditional_edges(
            'slot_selection',
            lambda s: 'continue' if s.get('status') == 'slot_confirmed' else 'stop',
            {'stop': END, 'continue': 'doctor_approval'}
        )

        g.add_edge('doctor_approval', END)

        return g.compile(checkpointer=MemorySaver())

    # ----------------------------------------------------------------
    # Routing logic
    # ----------------------------------------------------------------

    def _after_intake(self, state: BookingState) -> str:
        status = state.get('status', '')

        # Patient is responding to the slot list — route to slot_selection
        if status in ('slots_found', 'reschedule_options_available', 'reschedule_needed'):
            user_message = state.get('user_message', '').lower()
            slot_keywords = ['choose', 'i pick', 'i want', 'option', 'slot', 'tuesday', 'wednesday',
                             'monday', 'thursday', 'friday', 'morning', 'afternoon', 'first', 'second',
                             'third', '1', '2', '3']
            if any(kw in user_message for kw in slot_keywords):
                return 'select_slot'
            # Patient said something but not a clear slot choice — stop and re-ask
            return 'stop'

        # Still gathering name, email, reason, availability
        if status == 'collecting':
            return 'stop'

        # All info ready — search calendar
        return 'continue'

    def _after_calendar(self, state: BookingState) -> str:
        status = state.get('status', '')

        # Slot already confirmed by patient in this same turn (edge case)
        if status == 'slot_confirmed':
            return 'continue'

        # No slots available — stop and tell patient
        if status == 'no_slots':
            return 'stop'

        # Slots found — ALWAYS stop so patient can choose
        # This is the critical fix: was 'continue' before, causing auto-booking
        return 'stop'

    # ----------------------------------------------------------------
    # New node: handle the patient's slot choice
    # ----------------------------------------------------------------

    def _handle_slot_selection(self, state: BookingState) -> BookingState:
        candidate_slots = state.get('candidate_slots', [])
        user_message = state.get('user_message', '').lower()

        if not candidate_slots:
            state['bot_response'] = (
                "I don't have any available slots on record. "
                "Could you please tell me your availability again?"
            )
            state['status'] = 'reschedule_needed'
            return state

        chosen_slot = None

        # Try to match by slot number ("first", "1", "option 1")
        number_map = {
            '1': 0, 'first': 0, 'one': 0,
            '2': 1, 'second': 1, 'two': 1,
            '3': 2, 'third': 2, 'three': 2,
        }
        for word, index in number_map.items():
            if word in user_message and index < len(candidate_slots):
                chosen_slot = candidate_slots[index]
                break

        # Try to match by slot label content (day name, time, etc.)
        if not chosen_slot:
            for slot in candidate_slots:
                label = slot.get('label', '').lower()
                label_words = label.split()
                if any(word in user_message for word in label_words if len(word) > 3):
                    chosen_slot = slot
                    break

        if not chosen_slot:
            # Could not match — list slots again and ask clearly
            slot_list = '\n'.join(
                f"{i+1}. {slot.get('label', 'Available slot')}"
                for i, slot in enumerate(candidate_slots[:3])
            )
            state['bot_response'] = (
                "I'm not sure which slot you meant. Here are your options:\n\n"
                f"{slot_list}\n\n"
                "Please reply with the number or the day that works best for you."
            )
            state['status'] = 'slots_found'
            return state

        # Valid slot chosen
        state['selected_slot'] = chosen_slot
        state['status'] = 'slot_confirmed'
        state['bot_response'] = (
            f"Got it — you chose {chosen_slot.get('label')}. "
            "I'm sending this to the doctor for approval. "
            "You will be notified once the appointment is confirmed."
        )
        return state

    # ----------------------------------------------------------------
    # Fallback run without LangGraph
    # ----------------------------------------------------------------

    def run_turn(self, state: BookingState) -> BookingState:
        if self.graph is None:
            return self._run_fallback(state)

        return self.graph.invoke(
            state,
            config={'configurable': {'thread_id': state.get('session_id', 'default')}}
        )

    def _run_fallback(self, state: BookingState) -> BookingState:
        state = self.intake.run(state)

        route = self._after_intake(state)

        if route == 'stop':
            return state

        if route == 'select_slot':
            state = self._handle_slot_selection(state)
            if state.get('status') != 'slot_confirmed':
                return state
            return self.doctor.run(state)

        # route == 'continue' → full pipeline
        state = self.rag.run(state)
        state = self.calendar.run(state)

        if self._after_calendar(state) == 'stop':
            return state

        return self.doctor.run(state)