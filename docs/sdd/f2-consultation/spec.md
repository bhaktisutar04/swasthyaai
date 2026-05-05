# F2 — AI Consultation (Chat): Specification

> **Feature ID**: F2  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05  
> **Depends On**: F1 (Authentication)

---

## 1. Overview

The AI Consultation feature is the core interaction of SwasthyaAI — a real-time chat interface where patients describe their symptoms to an AI health assistant. The assistant asks empathetic follow-up questions, detects medical emergencies, and on completion triggers a full 4-agent analysis pipeline in the background.

---

## 2. Goals

1. Provide a natural, conversational chat experience for symptom collection.
2. Support multilingual interactions (English, Hindi, Marathi).
3. Detect emergency keywords instantly and show nearby hospitals.
4. Determine when enough information is collected and auto-trigger the analysis pipeline.
5. Maintain session state across messages within a consultation.
6. Never diagnose or suggest medicines during the chat phase.

---

## 3. User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-2.1 | As a patient, I can start a new consultation and receive a greeting in my preferred language. | P0 |
| US-2.2 | As a patient, I can describe my symptoms in free text and receive empathetic follow-up questions. | P0 |
| US-2.3 | As a patient, if I describe emergency symptoms (chest pain, difficulty breathing, etc.), I am immediately alerted with emergency instructions and nearby hospitals. | P0 |
| US-2.4 | As a patient, when I've described enough symptoms, the consultation auto-completes and my report starts generating in the background. | P0 |
| US-2.5 | As a patient, I can manually end the consultation by saying "that's all" or similar trigger phrases. | P1 |
| US-2.6 | As a patient, I see a typing indicator while the AI is composing a response. | P1 |
| US-2.7 | As a patient, I can navigate to my report after consultation completion. | P1 |
| US-2.8 | As a patient, if I refresh the page and return to the consultation page, a fresh session starts. | P2 |
| US-2.9 | As a patient, if I have an active in-progress session, it is resumed instead of creating a new one. | P2 |

---

## 4. Functional Requirements

### 4.1 Session Management
- **FR-2.1**: `POST /consultation/start` creates a new consultation session with a unique ID format: `CNS-YYYY-MM-DD-XXXXXX` (6-char hex).
- **FR-2.2**: If the user already has an `in_progress` session in memory, return that session instead of creating a new one.
- **FR-2.3**: New sessions are persisted immediately to the `consultations` table with status `in_progress`.
- **FR-2.4**: Patient's past medical history is loaded from Pinecone at session start.
- **FR-2.5**: Session state is stored in an in-memory Python dictionary (`sessions`).

### 4.2 Chat Interaction
- **FR-2.6**: `POST /consultation/message` accepts `{session_id, message}`.
- **FR-2.7**: The AI uses Groq API directly (not CrewAI) for real-time responses — model: `llama-3.3-70b-versatile`, max_tokens: 200, temperature: 0.3.
- **FR-2.8**: System prompt instructs the AI to: ask ONE follow-up question at a time, collect duration/severity/associated symptoms, be empathetic, NEVER diagnose, NEVER suggest medicines, keep responses to 2-3 sentences.
- **FR-2.9**: Last 8 messages from chat history are used as context window.
- **FR-2.10**: Each message (user + assistant) is appended to `chat_history` in session state.

### 4.3 Emergency Detection
- **FR-2.11**: Check every user message against emergency keywords in English, Hindi, and Marathi.
- **FR-2.12**: Emergency keywords include: "chest pain", "heart attack", "can't breathe", "difficulty breathing", "severe bleeding", "unconscious", "seizure", "stroke", "suicidal", "want to die", "end my life", + Hindi/Marathi equivalents.
- **FR-2.13**: On emergency detection: set `emergency_flag = true`, query Nominatim API for 3 nearby hospitals in the patient's city, return emergency response with hospital list.
- **FR-2.14**: Emergency response includes hospital name, address, and Google Maps link.

### 4.4 Consultation Completion
- **FR-2.15**: Consultation completes when ANY of these conditions is met:
  - User message contains a completion trigger phrase (e.g., "that's all", "done", "finish", "bas itna hi", "thats it")
  - User has sent ≥5 messages
- **FR-2.16**: On completion: extract symptoms from user messages, set status to "completed", disable input, show completion banner.
- **FR-2.17**: Spawn a background daemon thread running the full 4-agent pipeline (`run_full_crew`).
- **FR-2.18**: Return immediate response to user without waiting for pipeline completion.

### 4.5 Greeting
- **FR-2.19**: Greeting in English: "Namaste {name}! I'm your AI health assistant. How are you feeling today? Please describe your symptoms."
- **FR-2.20**: Greeting in Hindi: "Namaste {name}! Main aapka AI health assistant hoon. Aaj aap kaisa feel kar rahe hain?"
- **FR-2.21**: Greeting in Marathi: "Namaste {name}! Mi tumcha AI health assistant ahe. Aaj tumhi kase vatate?"

---

## 5. API Contract

### POST `/consultation/start`
```json
// Request: No body (uses auth token to identify user)
// Response 200
{
  "success": true,
  "data": {
    "session_id": "CNS-2026-05-05-A1B2C3",
    "greeting": "Namaste Bhakti! I'm your AI health assistant...",
    "language": "english"
  }
}
```

### POST `/consultation/message`
```json
// Request
{ "session_id": "CNS-2026-05-05-A1B2C3", "message": "I have a headache since yesterday" }

// Response 200 — Normal
{
  "success": true,
  "data": {
    "response": "I'm sorry to hear about your headache. On a scale of 1 to 10, how severe would you rate it?",
    "agent": "agent1",
    "emergency_detected": false,
    "consultation_complete": false
  }
}

// Response 200 — Emergency
{
  "success": true,
  "data": {
    "response": "🚨 Emergency detected! Please call 108 immediately...",
    "agent": "agent1",
    "emergency_detected": true,
    "hospitals": [
      { "name": "City Hospital", "address": "...", "maps_link": "https://..." }
    ],
    "consultation_complete": false
  }
}

// Response 200 — Completion
{
  "success": true,
  "data": {
    "response": "Thank you! Your full health report is being prepared...",
    "agent": "agent2",
    "emergency_detected": false,
    "consultation_complete": true,
    "summary": { "conditions": [], "severity_flag": "mild", "see_doctor": false }
  }
}
```

---

## 6. UI Specification

### Chat Page (`consultation.html`)
- Top bar: session ID display, agent status indicator, end consultation button.
- Chat area: scrollable message container with AI bubbles (left, light background) and user bubbles (right, primary color).
- Typing indicator: animated dots when AI is responding.
- Input area: text input + send button, disabled after completion.
- Emergency modal: overlay with 108 call prompt + hospital list with Maps links.
- Completion banner: in-chat card with "View Report →" button.

---

## 7. External Services

| Service | Purpose | Fallback |
|---------|---------|----------|
| Groq API (`llama-3.3-70b-versatile`) | Real-time chat responses | Hardcoded generic follow-up question |
| Nominatim (OpenStreetMap) | Hospital geolocation on emergency | Empty hospital list |
| Pinecone | Load past patient history at session start | Empty history array |
