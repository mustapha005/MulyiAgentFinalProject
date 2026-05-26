from app.graph.state import BookingState
from app.services.calendar_service import CalendarService

class CalendarAgent:
    def __init__(self, calendar_service: CalendarService):
        self.calendar_service = calendar_service

    def run(self, state: BookingState) -> BookingState:
        slots = self.calendar_service.find_free_slots(
            int(state.get('duration_minutes') or 30),
            state.get('preferred_times') or [],
        )

        state['candidate_slots'] = slots
        state['selected_slot'] = None          # NEVER auto-select — patient must choose
        state['status'] = 'slots_found' if slots else 'no_slots'  # fix typo

        if slots:
            slot_list = '\n'.join(
                f"{i+1}. {slot.get('label', 'Available slot')}"
                for i, slot in enumerate(slots[:3])
            )
            state['bot_response'] = (
                f"I found these available slots:\n\n{slot_list}\n\n"
                "Which one works best for you? Please reply with the number or the day."
            )
        else:
            state['bot_response'] = (
                "I could not find a matching slot for your availability. "
                "Could you give me another day or time window?"
            )

        return state