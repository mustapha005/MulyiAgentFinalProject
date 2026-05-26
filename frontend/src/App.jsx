import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Bot, CalendarCheck, ClipboardCheck, Stethoscope, UserRound, CheckCircle, Clock, ChevronRight } from 'lucide-react'
import { fetchPendingAppointments, sendChatMessage, sendDoctorDecision } from './api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function App() {
  const [tab, setTab] = useState('patient')
  return (
    <main className="sf-app">
      <header className="sf-hero">
        <div className="sf-hero-content">
          <span className="sf-eyebrow">
            <Stethoscope size={14} /> Multi-agent dental clinic assistant
          </span>
          <h1 className="sf-logo">SmileFlow</h1>
          <p className="sf-tagline">Patient intake · RAG · Calendar · Doctor approval · Confirmation</p>
        </div>
        <div className="sf-hero-badge">
          <span className="sf-badge-dot" />
          Human-in-the-loop
        </div>
      </header>

      <nav className="sf-nav">
        <button
          className={`sf-tab ${tab === 'patient' ? 'sf-tab--active' : ''}`}
          onClick={() => setTab('patient')}
        >
          <UserRound size={16} />
          Patient Chat
        </button>
        <button
          className={`sf-tab ${tab === 'doctor' ? 'sf-tab--active' : ''}`}
          onClick={() => setTab('doctor')}
        >
          <ClipboardCheck size={16} />
          Doctor Dashboard
        </button>
      </nav>

      <div style={{ display: tab === 'patient' ? 'block' : 'none' }}>
        <PatientChat isActive={tab === 'patient'} />
      </div>
      <div style={{ display: tab === 'doctor' ? 'block' : 'none' }}>
        <DoctorDashboard />
      </div>
    </main>
  )
}


function PatientChat({ isActive }) {
  const sessionId = useMemo(() => {
    const existingSessionId = localStorage.getItem('smileflow_session_id')
    if (existingSessionId) return existingSessionId
    const newSessionId = `session-${Math.random().toString(16).slice(2)}`
    localStorage.setItem('smileflow_session_id', newSessionId)
    return newSessionId
  }, [])

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! Send your name, email, reason for visit, and availability.',
    },
  ])
  const [input, setInput] = useState('')
  const [status, setStatus] = useState('unknown')
  const [candidateSlots, setCandidateSlots] = useState([])
  const messagesEndRef = useRef(null)

  const loadSession = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/session/${sessionId}`)
      if (!res.ok) return
      const data = await res.json()

      setStatus(data.status || 'unknown')
      setCandidateSlots(data.candidate_slots || [])

      if (data.conversation_history && data.conversation_history.length > 0) {
        setMessages((currentMessages) => {
          const serverLength = data.conversation_history.length
          const localLength = currentMessages.length
          if (serverLength <= localLength) return currentMessages
          return data.conversation_history.map((message) => ({
            role: message.role === 'patient' ? 'patient' : 'assistant',
            content: message.content,
          }))
        })
      } else if (data.bot_response) {
        setMessages((currentMessages) => {
          const alreadyThere = currentMessages.some((m) => m.content === data.bot_response)
          if (alreadyThere) return currentMessages
          return [{ role: 'assistant', content: data.bot_response }]
        })
      }
    } catch (error) {
      console.error('Failed to load session:', error)
    }
  }, [sessionId])

  useEffect(() => {
    loadSession()
    const interval = setInterval(loadSession, 3000)
    return () => clearInterval(interval)
  }, [loadSession])

  useEffect(() => {
    if (isActive) loadSession()
  }, [isActive, loadSession])

  useEffect(() => {
    const timer = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, 100)
    return () => clearTimeout(timer)
  }, [messages, isActive])

  async function submit(e) {
    e.preventDefault()
    if (!input.trim()) return

    const msg = input.trim()
    setInput('')

    setMessages((currentMessages) => [
      ...currentMessages,
      { role: 'patient', content: msg },
    ])

    try {
      const res = await sendChatMessage(sessionId, msg)
      setStatus(res.status || 'unknown')
      setCandidateSlots(res.candidate_slots || [])
      setMessages((currentMessages) => [
        ...currentMessages,
        { role: 'assistant', content: res.reply, status: res.status },
      ])
    } catch (error) {
      console.error('Chat error:', error)
      setMessages((currentMessages) => [
        ...currentMessages,
        { role: 'assistant', content: 'Backend error. Check FastAPI on port 8000.' },
      ])
    }
  }

  function resetSession() {
    localStorage.removeItem('smileflow_session_id')
    window.location.reload()
  }

  const workflowSteps = [
    { label: 'Intake Agent', desc: 'Extracts patient info' },
    { label: 'RAG Agent', desc: 'Retrieves clinic knowledge' },
    { label: 'Calendar Agent', desc: 'Proposes available slots' },
    { label: 'Doctor Review', desc: 'Approves or declines' },
    { label: 'Confirmation', desc: 'Sends calendar & email' },
  ]

  return (
    <section className="sf-grid">
      {/* ── Chat panel ── */}
      <div className="sf-panel">
        <div className="sf-panel-header">
          <h2 className="sf-panel-title">
            <Bot size={18} /> Patient Chat
          </h2>
          <div className="sf-session-meta">
            <span className="sf-meta-chip">
              <Clock size={12} /> {sessionId.slice(0, 16)}…
            </span>
            <span className={`sf-status-chip sf-status--${status}`}>{status}</span>
          </div>
        </div>

        {status === 'pending_doctor' && (
          <div className="sf-notice sf-notice--info">
            <CheckCircle size={15} />
            Your request has been sent to the doctor. Please wait for approval.
          </div>
        )}

        {(status === 'reschedule_options_available' || status === 'reschedule_needed') && (
          <div className="sf-notice sf-notice--warn">
            ⚠ The doctor declined your appointment. Please choose another slot below.
          </div>
        )}

        <div className="sf-messages">
          {messages.map((m, i) => (
            <div key={i} className={`sf-msg sf-msg--${m.role}`}>
              {m.role === 'assistant' && (
                <div className="sf-avatar">
                  <Bot size={14} />
                </div>
              )}
              <div className="sf-bubble">
                <p>{m.content}</p>
                {m.status && <small className="sf-msg-status">{m.status}</small>}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {candidateSlots.length > 0 &&
          status !== 'pending_doctor' &&
          status !== 'confirmed' && (
            <div className="sf-slots">
              <p className="sf-slots-label">Available slots</p>
              <div className="sf-slots-grid">
                {candidateSlots.map((slot, index) => (
                  <button
                    key={index}
                    className="sf-slot-btn"
                    onClick={() => setInput(`I choose ${slot.label}`)}
                  >
                    <ChevronRight size={13} /> {slot.label}
                  </button>
                ))}
              </div>
            </div>
          )}

        <form onSubmit={submit} className="sf-form">
          <input
            className="sf-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message…"
          />
          <button className="sf-send-btn" type="submit">Send</button>
        </form>

        <div className="sf-quick-actions">
          <button
            className="sf-ghost-btn"
            onClick={() =>
              setInput(
                'My name is Sara Benali. My email is sara@example.com. I have tooth pain and I am available Tuesday morning.'
              )
            }
          >
            Use demo message
          </button>
          <button className="sf-ghost-btn sf-ghost-btn--danger" onClick={resetSession}>
            Reset session
          </button>
        </div>
      </div>

      {/* ── Workflow panel ── */}
      <div className="sf-panel sf-panel--workflow">
        <h2 className="sf-panel-title">Workflow</h2>
        <div className="sf-steps">
          {workflowSteps.map((step, i) => (
            <div key={i} className="sf-step">
              <div className="sf-step-num">{i + 1}</div>
              <div className="sf-step-body">
                <strong>{step.label}</strong>
                <span>{step.desc}</span>
              </div>
              {i < workflowSteps.length - 1 && <div className="sf-step-line" />}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}


function DoctorDashboard() {
  const [items, setItems] = useState([])
  const [notice, setNotice] = useState('')

  async function load() {
    try {
      setItems(await fetchPendingAppointments())
    } catch {
      setNotice('Could not load pending appointments.')
    }
  }

  useEffect(() => { load() }, [])

  async function decide(id, decision) {
    try {
      const r = await sendDoctorDecision(
        id,
        decision,
        decision === 'approve' ? 'Approved by doctor.' : 'Please propose another slot.'
      )
      setNotice(r.message)
      await load()
    } catch {
      setNotice('Decision failed.')
    }
  }

  return (
    <section className="sf-dash">
      <div className="sf-dash-header">
        <h2 className="sf-panel-title">
          <CalendarCheck size={18} /> Doctor Approval Dashboard
        </h2>
        <button className="sf-ghost-btn" onClick={load}>Refresh</button>
      </div>

      {notice && <div className="sf-notice sf-notice--info">{notice}</div>}

      {items.length === 0 ? (
        <div className="sf-empty">
          <CalendarCheck size={40} strokeWidth={1} />
          <p>No pending appointments</p>
        </div>
      ) : (
        <div className="sf-cards">
          {items.map((a) => (
            <article key={a.id} className="sf-card">
              <div className="sf-card-top">
                <div>
                  <h3 className="sf-card-name">{a.patient_name}</h3>
                  <p className="sf-card-email">{a.patient_email}</p>
                </div>
                <span className="sf-card-badge">Pending</span>
              </div>
              <div className="sf-card-body">
                <div className="sf-card-row"><span>Reason</span><strong>{a.reason}</strong></div>
                <div className="sf-card-row"><span>Treatment</span><strong>{a.treatment}</strong></div>
                <div className="sf-card-row"><span>Duration</span><strong>{a.duration_minutes} min</strong></div>
                <div className="sf-card-row"><span>Slot</span><strong>{a.selected_slot.label}</strong></div>
              </div>
              <div className="sf-card-actions">
                <button className="sf-approve-btn" onClick={() => decide(a.id, 'approve')}>
                  ✓ Approve
                </button>
                <button className="sf-decline-btn" onClick={() => decide(a.id, 'decline')}>
                  ✕ Decline
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}