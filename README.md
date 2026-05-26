# SmileFlow — Multi-Agent Dental Clinic Assistant

## Group Members

| Full Name | Role / Contribution |
|---|---|
| Member 1 | Mustapha AARAB |
| Member 2 | Aya AGRIGAH |
| Member 3 | Atiqa ESSAYOUTI |

---



# 1. Project Overview

SmileFlow is a multi-agent dental clinic assistant designed to manage appointment booking through an intelligent web interface.

The patient interacts with a chatbot to request an appointment. The system collects the required information, retrieves clinic knowledge using RAG, checks the dentist's Google Calendar availability, proposes appointment slots, waits for doctor validation, and finally creates the appointment and sends an email confirmation.

The project demonstrates how a multi-agent system can reason, plan, and execute a complex workflow in a semi-autonomous way while keeping a human expert in the loop for critical decisions.

---

# 2. Project Objective

The objective of this project is to implement an intelligent multi-agent ecosystem capable of:

- Understanding a patient's appointment request.
- Collecting required information such as name, email, reason for visit, and availability.
- Retrieving clinic-specific knowledge dynamically using RAG.
- Checking doctor availability using Google Calendar.
- Asking the doctor to approve or decline the appointment.
- Creating a real calendar event after doctor approval.
- Sending a confirmation email to the patient.
- Providing a real-time web interface for both patient and doctor.

The chosen sector is the healthcare / dental clinic sector, where safety, validation, and reliability are important.

---

# 3. Main Features

- Patient chatbot interface.
- Doctor approval dashboard.
- Multi-agent workflow with LangGraph.
- RAG system for clinic-specific knowledge.
- Human-in-the-loop validation.
- Google Calendar integration.
- Gmail confirmation email integration.
- Grok API integration as the LLM.
- Session memory for patient conversation.
- Rescheduling flow when the doctor declines a slot.
- Frontend authentication demo with separate patient and doctor dashboards.
- Prompt evaluation methodology.

---

# 4. Technologies Used

## Backend

| Technology | Purpose |
|---|---|
| Python | Main backend language |
| FastAPI | REST API backend |
| LangGraph | Multi-agent workflow orchestration |
| Pydantic | Data validation and settings management |
| SQLite | Local database |
| uv | Python dependency management |
| Google Calendar API | Checking doctor availability and creating events |
| Gmail API | Sending confirmation emails |
| Grok API / xAI | LLM used for natural language generation |

## Frontend

| Technology | Purpose |
|---|---|
| React | Web user interface |
| Vite | Frontend development server and build tool |
| JavaScript | Frontend logic |
| CSS | Styling |
| Lucide React | Icons |

---

# 5. Global Architecture

The system is composed of two main applications:

```text
Frontend React Vite
        |
        v
Backend FastAPI
        |
        v
LangGraph Multi-Agent Workflow
        |
        +--> Patient Intake Agent
        +--> RAG Agent
        +--> Calendar Agent
        +--> Doctor Approval / Human-in-the-loop
        +--> Notification Agent
        |
        v
External Services
        |
        +--> Google Calendar API
        +--> Gmail API
        +--> Grok API
```

---

# 6. Multi-Agent Architecture

SmileFlow uses a hierarchical and sequential orchestration.

The workflow is sequential because appointment booking follows a logical order:

```text
Collect patient information
        |
Retrieve clinic knowledge
        |
Check calendar availability
        |
Propose appointment slot
        |
Doctor validation
        |
Create appointment
        |
Send confirmation email
```

It is also hierarchical because the global booking workflow controls and coordinates specialized agents.

---

# 7. Agents Description

## 7.1 Patient Intake Agent

The Patient Intake Agent is responsible for collecting the required information from the patient.

It extracts:

- Patient name
- Patient email
- Reason for visit
- Availability
- Appointment preferences

### Example

```text
My name is Sara Benali.
My email is sara@example.com.
I have tooth pain.
I am available Tuesday morning.
```

The agent checks whether enough information is available to continue the booking process.

---

## 7.2 RAG Agent

The RAG Agent retrieves clinic-specific knowledge from the local knowledge base.

### Examples of retrieved information

- Clinic opening hours
- Appointment policy
- Emergency policy
- Treatment durations
- Doctor specialties
- Cancellation rules

The RAG Agent helps the system make better decisions. For example, if the patient says they have tooth pain, the system can retrieve that a tooth pain consultation usually requires a specific duration and may require doctor validation.

---

## 7.3 Calendar Agent

The Calendar Agent interacts with Google Calendar.

### Responsibilities

- Check doctor availability.
- Find free appointment slots.
- Avoid already booked periods.
- Prepare candidate appointment slots.
- Create a final calendar event after doctor approval.

The Calendar Agent does not confirm the appointment by itself. It only prepares possible options.

---

## 7.4 Doctor Approval Agent / Human-in-the-loop

This is the human validation step.

When the system finds a possible appointment slot, it sends the request to the doctor dashboard.

The doctor can:

- Approve the appointment.
- Decline the appointment.

### If the doctor approves

- Calendar event is created.
- Confirmation email is sent.
- Patient receives confirmation.

### If the doctor declines

- The patient is informed.
- Alternative slots are proposed.
- The patient can choose another slot.

This guarantees safety and reliability because the system does not make critical healthcare scheduling decisions without human validation.

---

## 7.5 Notification Agent

The Notification Agent is responsible for final confirmation.

After doctor approval, it:

- Creates the Google Calendar event.
- Sends a confirmation email to the patient using Gmail API.

The email contains appointment details such as:

- Patient name
- Appointment date and time
- Reason for visit
- Confirmation message

---

# 8. LangGraph Workflow and Orchestration

LangGraph is used to model the booking process as a graph of steps.

The workflow can be represented as:

```text
START
  |
  v
Patient Intake
  |
  v
Information Complete?
  |
  +-- No --> Ask patient for missing information
  |
  +-- Yes
        |
        v
RAG Retrieval
        |
        v
Calendar Availability Search
        |
        v
Candidate Slot Selection
        |
        v
Doctor Approval
        |
        +-- Approved --> Calendar Event + Email Confirmation
        |
        +-- Declined --> Offer Alternative Slots
        |
        v
END
```

## Justification of the Collaboration Method

We chose a hierarchical sequential architecture because the appointment booking process is structured and requires a safe order of execution.

The system must not send an email before the doctor validates the appointment. It must not create a calendar event before checking availability. It must not propose slots before collecting the patient's availability.

This makes sequential orchestration the safest and clearest choice.

The workflow is hierarchical because the main booking workflow supervises all agents and decides the next step based on the current state.

---

# 9. RAG Agentique

The project includes a local knowledge base used by the RAG Agent.

### Example folder

```text
backend/
└── knowledge_base/
    ├── clinic_hours.md
    ├── appointment_policy.md
    ├── emergency_policy.md
    ├── treatment_durations.csv
    └── doctor_specialties.csv
```

The RAG Agent retrieves relevant information dynamically during the conversation.

| Patient Question | Retrieved Knowledge |
|---|---|
| "Are you open on Saturday?" | Clinic hours |
| "How long does a cleaning take?" | Treatment duration |
| "I have severe pain" | Emergency policy |
| "Can I cancel my appointment?" | Appointment policy |

This satisfies the requirement of Retrieval-Augmented Generation, because the agents can access specific contextual information instead of relying only on the LLM.

---

# 10. Human-in-the-loop

The Human-in-the-loop mechanism is implemented in the doctor dashboard.

The critical action is appointment confirmation.

The system pauses before:

- Creating the calendar event.
- Sending the confirmation email.
- Confirming the appointment to the patient.

The doctor must approve the request first.

## Approval Flow

```text
Patient chooses slot
        |
Appointment request sent to doctor
        |
Doctor approves
        |
Google Calendar event is created
        |
Email confirmation is sent
```

## Decline Flow

```text
Patient chooses slot
        |
Appointment request sent to doctor
        |
Doctor declines
        |
Patient is notified
        |
Alternative slots are shown
        |
Patient chooses another slot
```

This ensures safety, reliability, and human supervision.

---

# 11. Prompt Evaluation

The project includes a prompt evaluation methodology to compare and improve prompt quality.

## Evaluation Goal

The objective is to test whether the assistant:

- Collects all required patient information.
- Uses clinic knowledge correctly.
- Does not confirm appointments before doctor approval.
- Gives short and professional answers.
- Handles declined appointments correctly.
- Avoids medical diagnosis.

---

## Example Prompt Versions

### Prompt A — Basic Prompt

```text
You are a dental clinic assistant. Help patients book appointments.
```

### Prompt B — Optimized Prompt

```text
You are SmileFlow, a dental clinic appointment assistant.

Your tasks:
- Collect patient name, email, reason for visit, and availability.
- Use clinic context when answering questions.
- Never confirm an appointment before doctor approval.
- If information is missing, ask one clear follow-up question.
- Keep answers short and professional.
- Do not give medical diagnosis.
```

---

## Evaluation Criteria

| Criterion | Description |
|---|---|
| Information completeness | Did the assistant collect name, email, reason, and availability? |
| Tool usage | Did the system use RAG and calendar logic at the correct time? |
| Safety | Did the assistant avoid confirming before doctor approval? |
| Accuracy | Did answers match clinic knowledge? |
| User experience | Was the response clear and professional? |
| Rescheduling | Did the assistant handle doctor decline correctly? |

---

## Example Test Cases

| Test Case | Expected Behavior |
|---|---|
| Patient gives full information | System checks availability and sends request to doctor |
| Patient forgets email | Assistant asks for email |
| Patient asks clinic hours | RAG Agent retrieves clinic hours |
| Doctor approves | Calendar event and email are created |
| Doctor declines | Patient receives alternative slots |
| Patient asks for medical diagnosis | Assistant avoids diagnosis and recommends contacting the clinic |

---

## Result

The optimized prompt performs better because it clearly defines:

- The assistant's role.
- Required patient information.
- Safety rules.
- Human approval constraint.
- Response style.

---

# 12. Web Interface

The project includes a functional React Vite web interface.

---

## Authentication Page

The frontend includes a demo authentication system with two user roles:

- Patient
- Doctor

This separates the patient dashboard from the doctor dashboard.

---

## Patient Dashboard

The patient dashboard contains:

- Chatbot interface.
- Session memory.
- Appointment status.
- Candidate appointment slots.
- Rescheduling messages.
- Confirmation messages.

The patient can:

- Send appointment requests.
- Choose appointment slots.
- Wait for doctor approval.
- Choose another slot if the doctor declines.

---

## Doctor Dashboard

The doctor dashboard contains:

- Pending appointment requests.
- Patient name and email.
- Reason for visit.
- Treatment type.
- Appointment duration.
- Selected slot.
- Approve button.
- Decline button.

The doctor validates or rejects the appointment request.

---

# 13. LLM Integration

The project uses Grok API as the LLM provider.

The LLM is used for:

- Natural language response generation.
- Rewriting safe workflow responses in a more human style.
- Improving patient communication.

The LLM does not directly execute actions.

Critical actions are controlled by:

- LangGraph workflow
- Doctor approval
- Google Calendar API
- Gmail API

This design prevents the LLM from inventing appointments or sending emails without validation.

---

# 14. Environment Variables

The project uses a `.env` file in the backend.

### Example

```env
APP_NAME=multiagent
APP_MODE=google
DATABASE_URL=sqlite:///./smileflow.db
TIMEZONE=Africa/Casablanca
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

GOOGLE_CREDENTIALS_FILE=./credentials/google_credentials.json
GOOGLE_CALENDAR_TOKEN_FILE=./credentials/token_calendar.json
GOOGLE_GMAIL_TOKEN_FILE=./credentials/token_gmail.json
GOOGLE_CALENDAR_ID=primary

EMAIL_PROVIDER=gmail_api
EMAIL_FROM=your_email@gmail.com

LLM_PROVIDER=grok
XAI_API_KEY=your_xai_api_key_here
GROK_BASE_URL=https://api.x.ai/v1
GROK_MODEL=grok-4.3
LLM_TIMEOUT_SECONDS=30
```

## Modes

### For safe testing

```env
APP_MODE=mock
```

### For real Google Calendar and Gmail

```env
APP_MODE=google
```

---

# 15. Installation

## 15.1 Clone the Repository

```bash
git clone PASTE_GITHUB_LINK_HERE
cd smileflow_project_real_google
```

---

## 15.2 Backend Installation

Go to the backend folder:

```bash
cd backend
```

Install dependencies using uv:

```bash
uv sync
```

If needed, add dependencies:

```bash
uv add fastapi uvicorn pydantic pydantic-settings langgraph google-api-python-client google-auth google-auth-oauthlib openai
```

Create `.env`:

```bash
cp .env.example .env
```

Then edit `.env` with your own keys.

---

## 15.3 Frontend Installation

Go to the frontend folder:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Run frontend:

```bash
npm run dev
```

---

# 16. Google Cloud Setup

To use real Calendar and Gmail features, configure Google Cloud:

1. Create a Google Cloud project.
2. Enable Google Calendar API.
3. Enable Gmail API.
4. Configure OAuth consent screen.
5. Add your Gmail as a test user.
6. Create OAuth Client ID.
7. Choose Desktop App.
8. Download credentials JSON.

Rename it:

```text
google_credentials.json
```

Place it here:

```text
backend/credentials/google_credentials.json
```

When the backend first calls Google Calendar or Gmail, a browser window opens to request authorization.

After authorization, the system creates:

```text
backend/credentials/token_calendar.json
backend/credentials/token_gmail.json
```

Do not share these token files.

---

# 17. How to Run the Project

## Terminal 1 — Backend

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

### Backend health check

```text
http://127.0.0.1:8000/api/health
```

### LLM test

```text
http://127.0.0.1:8000/api/llm-test
```

---

## Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

Open:

```text
http://localhost:5173
```

---

# 18. Demo Accounts

The frontend includes demo authentication.

## Patient

```text
Email: patient@smileflow.local
Password: patient123
```

## Doctor

```text
Email: doctor@smileflow.local
Password: doctor123
```

> Note: This is demo authentication for presentation purposes. A production system should use backend authentication with hashed passwords and secure sessions or JWT.

---

# 19. Demo Scenario

## Step 1 — Patient Login

Login as patient.

---

## Step 2 — Patient Sends Request

### Example message

```text
My name is Sara Benali. My email is sara@example.com. I have tooth pain and I am available Tuesday morning.
```

---

## Step 3 — System Processes Request

The system:

- Extracts patient information.
- Uses RAG to understand treatment context.
- Checks calendar availability.
- Proposes a slot.
- Sends the appointment request to the doctor.

---

## Step 4 — Doctor Login

Login as doctor.

---

## Step 5 — Doctor Decision

The doctor dashboard shows the pending appointment.

The doctor can approve or decline.

---

## Step 6A — If Approved

The system:

- Creates a Google Calendar event.
- Sends a confirmation email.
- Updates patient dashboard.

---

## Step 6B — If Declined

The system:

- Informs the patient.
- Shows alternative slots.
- Allows the patient to choose another appointment.

---

# 20. API Endpoints

## General

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Checks backend status |
| GET | `/api/llm-test` | Tests LLM provider |

---

## Patient

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Sends patient message to agentic workflow |
| GET | `/api/session/{session_id}` | Gets patient session state and conversation history |

---

## Doctor

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/doctor/pending` | Gets pending appointment requests |
| POST | `/api/doctor/appointments/{appointment_id}/decision` | Approves or declines appointment |

---

# 21. Database and Session State

The project uses SQLite.

## Main stored data

- Patient session state.
- Conversation history.
- Candidate slots.
- Appointment requests.
- Appointment status.
- Doctor decisions.
- Calendar event IDs.

### Example session state

```json
{
  "session_id": "session-abc123",
  "status": "pending_doctor",
  "bot_response": "Your request has been sent to the doctor.",
  "candidate_slots": [],
  "appointment_id": "appt-123",
  "conversation_history": [
    {
      "role": "patient",
      "content": "I am available Tuesday morning."
    },
    {
      "role": "assistant",
      "content": "I found a slot and sent it to the doctor."
    }
  ]
}
```

---

# 22. Security and Reliability

The project includes several safety mechanisms:

- The LLM does not directly create appointments.
- The doctor validates appointments before confirmation.
- Calendar event creation happens only after approval.
- Email confirmation happens only after approval.
- Patient session state is saved.
- The system handles doctor decline and rescheduling.
- Sensitive keys are stored in `.env`.

## Important files that should not be committed

```text
.env
backend/credentials/google_credentials.json
backend/credentials/token_calendar.json
backend/credentials/token_gmail.json
```

---

# 23. Project Structure

```text
smileflow_project_real_google/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── notification_agent.py
│   │   ├── graph/
│   │   │   └── workflow.py
│   │   ├── services/
│   │   │   ├── calendar_service.py
│   │   │   ├── email_service.py
│   │   │   ├── google_auth.py
│   │   │   └── llm_service.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── prompts.py
│   ├── credentials/
│   ├── knowledge_base/
│   ├── pyproject.toml
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
└── README.md
```

---

# 24. Troubleshooting

## Problem: Backend error in frontend

Check backend terminal.

### Common causes

- Backend is not running.
- Google token expired.
- `.env` missing a key.
- LLM API key missing.

---

## Problem: Google token expired or revoked

### Error

```text
invalid_grant: Token has been expired or revoked
```

### Fix

```bash
cd backend
rm credentials/token_calendar.json
rm credentials/token_gmail.json
uv run uvicorn app.main:app --reload --port 8000
```

### On Windows PowerShell

```powershell
Remove-Item .\credentials\token_calendar.json -Force -ErrorAction SilentlyContinue
Remove-Item .\credentials\token_gmail.json -Force -ErrorAction SilentlyContinue
uv run uvicorn app.main:app --reload --port 8000
```

Then authorize Google again.

---

## Problem: LLM not working

Check:

```text
http://127.0.0.1:8000/api/llm-test
```

Verify `.env`:

```env
LLM_PROVIDER=grok
XAI_API_KEY=your_xai_api_key_here
GROK_MODEL=grok-4.3
```

---

## Problem: Frontend cannot start

Make sure `package.json` exists in the frontend folder.

```bash
cd frontend
npm install
npm run dev
```

---

## Problem: Pydantic error "Extra inputs are not permitted"

This means there is a variable in `.env` that does not exist in `config.py`.

### Fix

- Add the missing variable to `Settings` in `config.py`.
- Or remove the unused variable from `.env`.

---

# 25. How the Project Meets the Teacher's Requirements

| Requirement | Implementation in SmileFlow |
|---|---|
| Multi-agent system | Patient Intake Agent, RAG Agent, Calendar Agent, Doctor Approval, Notification Agent |
| Workflow Agentique et Orchestration | LangGraph coordinates the complete booking workflow |
| Justification of collaboration method | Sequential and hierarchical because appointment booking has ordered, safety-critical steps |
| RAG Agentique | Local clinic knowledge base used to retrieve context dynamically |
| Human-in-the-loop | Doctor approval dashboard before final booking |
| Prompt Evaluation | A/B prompt comparison and test scenarios are defined |
| Web UI | React Vite interface with patient and doctor dashboards |
| Real-time interaction | Patient chat and dashboard polling |
| Real tool execution | Google Calendar and Gmail integration |
| Report and GitHub | README and final report include architecture and code link |

---

# 26. Limitations

- The authentication system is a frontend demo and not production-level security.
- The RAG system can be improved with embeddings and a vector database.
- Google OAuth tokens may expire and require reauthorization.
- The system depends on external APIs when using Google and Grok.
- The project is designed for academic demonstration, not direct medical production use.

---

# 27. Future Improvements

Possible improvements:

- Add backend authentication with JWT.
- Add hashed passwords.
- Add user roles in the backend.
- Add PostgreSQL instead of SQLite.
- Add vector database for stronger RAG.
- Add source citations for RAG answers.
- Add doctor notes when declining appointments.
- Add appointment cancellation and rescheduling.
- Add SMS notifications.
- Add admin dashboard.
- Add automated prompt evaluation script.
- Add unit and integration tests.

---

# 28. Conclusion

SmileFlow demonstrates a complete multi-agent system for dental clinic appointment scheduling.

The project combines:

- LangGraph orchestration.
- RAG-based contextual knowledge.
- Human-in-the-loop validation.
- LLM-based natural language generation.
- Google Calendar and Gmail tool execution.
- A functional React web interface.

This architecture shows how agentic AI can be used in a real-world domain while keeping critical actions safe through human validation.
