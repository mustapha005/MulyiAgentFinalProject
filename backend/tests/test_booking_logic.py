from pathlib import Path
from app.agents.intake_agent import PatientIntakeAgent
from app.services.rag_store import ClinicRAGStore

def test_intake_extracts_complete_request():
    state = {'session_id': 's', 'messages': [], 'user_message': 'My name is Sara Benali. My email is sara@example.com. I have tooth pain and I am available Tuesday morning.'}
    result = PatientIntakeAgent().run(state)
    assert result['patient_name'] == 'Sara Benali'
    assert result['patient_email'] == 'sara@example.com'
    assert result['reason'] == 'Tooth pain consultation'
    assert result['preferred_times']
    assert result['status'] == 'intake_complete'

def test_rag_infers_extraction_duration():
    store = ClinicRAGStore(Path('knowledge_base'))
    info = store.infer_treatment('I need tooth extraction')
    assert info['treatment'] == 'Tooth extraction'
    assert info['duration_minutes'] == 60
