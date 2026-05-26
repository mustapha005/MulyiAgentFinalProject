from app.graph.state import BookingState
from app.services.rag_store import ClinicRAGStore

class RAGAgent:
    def __init__(self, rag_store: ClinicRAGStore):
        self.rag_store = rag_store

    def run(self, state: BookingState) -> BookingState:
        info = self.rag_store.infer_treatment(state.get('reason'))
        state['treatment'] = info['treatment']
        state['duration_minutes'] = info['duration_minutes']
        state['emergency'] = info['urgency_level'] == 'high'
        state['rag_context'] = self.rag_store.query(f"{state.get('reason')} duration emergency doctor approval")
        state['status'] = 'rag_complete'
        return state
