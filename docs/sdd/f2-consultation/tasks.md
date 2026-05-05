# F2 — AI Consultation (Chat): Tasks

> **Feature ID**: F2  
> **Status**: ✅ All Complete  
> **Last Updated**: 2026-05-05

---

## Task Checklist

### Backend — Session Management
- [x] **T2.1**: Create in-memory `sessions` dict for active consultation state
- [x] **T2.2**: Implement `build_patient_profile(user)` — constructs 35-key profile dict from User ORM object
- [x] **T2.3**: `POST /consultation/start` — generate unique session ID (`CNS-YYYY-MM-DD-XXXXXX`), store profile, create DB record
- [x] **T2.4**: Resume existing in-progress session for same user instead of creating duplicate
- [x] **T2.5**: Load past medical history from Pinecone at session start via `get_patient_memory()`
- [x] **T2.6**: Session reconstruction from DB if session_id not found in memory (server restart recovery)

### Backend — Chat Engine
- [x] **T2.7**: Implement `call_groq_directly()` — Groq SDK call with system prompt, 8-message context, 200 max tokens
- [x] **T2.8**: System prompt: multilingual, empathetic, no diagnosis, no medicines, 2-3 sentence responses
- [x] **T2.9**: Append user message and AI response to `chat_history` in session state
- [x] **T2.10**: Fallback response on Groq API failure

### Backend — Emergency Detection
- [x] **T2.11**: Define emergency keyword lists for English (11), Hindi (4), Marathi (3)
- [x] **T2.12**: Check every user message against keywords (case-insensitive)
- [x] **T2.13**: On detection: set `emergency_flag = true`, call Nominatim API for hospitals
- [x] **T2.14**: Return emergency response with hospital list (name, address, maps_link)
- [x] **T2.15**: Nominatim API call with 5-second timeout and error handling

### Backend — Completion Logic
- [x] **T2.16**: Define completion trigger phrases (14 phrases in English + Hindi)
- [x] **T2.17**: Auto-complete when user message count ≥ 5
- [x] **T2.18**: On completion: extract symptoms from user messages, set status = "completed"
- [x] **T2.19**: Spawn background daemon thread running `run_pipeline_background(session_id)`
- [x] **T2.20**: Background thread creates own DB session (`SessionLocal()`) for thread safety
- [x] **T2.21**: Return immediate completion response with "View Report" prompt

### Backend — Multilingual Greetings
- [x] **T2.22**: English greeting with patient name
- [x] **T2.23**: Hindi greeting with patient name
- [x] **T2.24**: Marathi greeting with patient name

### Frontend — Chat UI (`consultation.html`)
- [x] **T2.25**: Top bar with session ID display and agent status indicator
- [x] **T2.26**: Scrollable chat message container
- [x] **T2.27**: AI bubbles (left-aligned, light background) and user bubbles (right-aligned, primary color)
- [x] **T2.28**: Message timestamp display
- [x] **T2.29**: Text input with send button at bottom
- [x] **T2.30**: End consultation button in top bar

### Frontend — Chat Logic (`consultation.js`)
- [x] **T2.31**: `startConsultation()` — call `/start`, display greeting, store session ID
- [x] **T2.32**: `sendMessage()` — add user bubble, call `/message`, handle response types
- [x] **T2.33**: `addMessage(text, sender, time)` — create and append bubble DOM element
- [x] **T2.34**: `showTyping()` / `removeTyping()` — animated typing indicator (3 dots)
- [x] **T2.35**: `handleKeyPress()` — Enter key sends message (Shift+Enter for newline)
- [x] **T2.36**: Prevent double-send with `isSending` flag
- [x] **T2.37**: `showEmergencyModal(hospitals)` — overlay with 108 call prompt + hospital list with Maps links
- [x] **T2.38**: `closeEmergencyModal()` — dismiss emergency overlay
- [x] **T2.39**: Completion banner — in-chat card with "View Report →" button
- [x] **T2.40**: Disable input + send button after consultation completion
- [x] **T2.41**: Agent status indicator: update to "Preparing Report..." on completion, "Analysis Complete" after 90s timeout
- [x] **T2.42**: `viewReport()` — navigate to `report.html?id={sessionId}`
- [x] **T2.43**: `endConsultation()` — confirm dialog, redirect to dashboard
- [x] **T2.44**: Clear `current_session_id` from localStorage on page load (fresh start)
- [x] **T2.45**: Auto-scroll chat container to bottom on new messages

---

## Verification

- [x] Starting a consultation returns greeting in correct language
- [x] Messages get AI responses within 2-3 seconds
- [x] Typing indicator shows during AI response generation
- [x] Emergency keywords trigger modal with hospital list
- [x] "that's all" triggers consultation completion
- [x] 5th user message auto-triggers completion
- [x] Completion disables input and shows banner with report link
- [x] Background pipeline starts without blocking the UI
- [x] Session reconstruction works after simulated server restart
