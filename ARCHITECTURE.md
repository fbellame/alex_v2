# Alex V2 - Agent Architecture & Workflow

## Agent Structure Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Alex V2 System                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Entry Point                               │
│                   alex_greeting.py                             │
│                                                                 │
│  • Initializes all agents                                      │
│  • Sets up AgentSession with multilingual STT                  │
│  • Manages agent transfers                                     │
│  • Handles event-driven routing                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GreetingAgent                               │
│                 (Language Router)                              │
│                                                                 │
│  Greeting: "Hi Bonjour, welcome to SmileRight Dental          │
│            Clinic, how can I help you today?"                  │
│                                                                 │
│  Function Tools:                                               │
│  • detect_language_and_transfer()                             │
│                                                                 │
│  Language Detection Logic:                                     │
│  • Keyword-based scoring system                               │
│  • French vs English indicators                               │
│  • Default to English if unclear                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │  Language Detection │
                    │     Analysis        │
                    └─────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌─────────────────────────────┐    ┌─────────────────────────────┐
│     EnglishBookingAgent     │    │     FrenchBookingAgent      │
│    (English Specialist)     │    │     (French Specialist)     │
│                             │    │                             │
│ Greeting: "Perfect! I'll    │    │ Greeting: "Parfait ! Je     │
│ help you book your          │    │ vais vous aider à prendre   │
│ appointment in English..."  │    │ votre rendez-vous..."       │
│                             │    │                             │
│ Function Tools:             │    │ Function Tools:             │
│ • set_first_name()          │    │ • definir_prenom()          │
│ • set_last_name()           │    │ • definir_nom_famille()     │
│ • set_phone()               │    │ • definir_telephone()       │
│ • set_booking_date_time()   │    │ • definir_date_heure_...()  │
│ • set_booking_reason()      │    │ • definir_raison_...()      │
│ • get_current_datetime()    │    │ • obtenir_date_heure_...()  │
│ • get_clinic_info()         │    │ • obtenir_info_clinique()   │
│                             │    │                             │
│ Booking Flow:               │    │ Processus de Réservation:   │
│ 1. Date/Time                │    │ 1. Date/Heure               │
│ 2. First Name               │    │ 2. Prénom                   │
│ 3. Last Name (spelled)      │    │ 3. Nom (épelé)             │
│ 4. Phone (digit by digit)   │    │ 4. Téléphone (chiffre)     │
│ 5. Reason                   │    │ 5. Raison                   │
│ 6. Confirmation             │    │ 6. Confirmation             │
└─────────────────────────────┘    └─────────────────────────────┘
```

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        UserData                                │
│                   (Shared Context)                             │
│                                                                 │
│  Customer Information:                                         │
│  • customer_first_name                                         │
│  • customer_last_name                                          │
│  • customer_phone                                              │
│  • booking_date_time                                           │
│  • booking_reason                                              │
│                                                                 │
│  System State:                                                 │
│  • detected_language                                           │
│  • current_agent                                               │
│  • agents (dictionary)                                         │
│  • prev_agent                                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Transfer Flow                          │
│                                                                 │
│  1. User connects → GreetingAgent starts                       │
│  2. GreetingAgent says bilingual greeting                      │
│  3. User responds in preferred language                        │
│  4. detect_language_and_transfer() analyzes response           │
│  5. Function returns transfer signal                           │
│  6. Event handler catches transfer signal                      │
│  7. AgentManager.transfer_to_agent() called                    │
│  8. session.transfer_agent() performs handoff                  │
│  9. Specialized agent takes over with context                  │
│  10. Booking flow continues in detected language               │
└─────────────────────────────────────────────────────────────────┘
```

## Component Relationships

```
alex_greeting.py
├── shared/
│   ├── user_data.py ──────────────┐
│   └── tools/                     │
│       ├── english_tools.py ──────┼─── Used by EnglishBookingAgent
│       └── french_tools.py ───────┼─── Used by FrenchBookingAgent
│                                  │
└── agents/                        │
    ├── greeting_agent.py ─────────┼─── Uses UserData
    ├── english_booking_agent.py ──┼─── Uses UserData + English Tools
    └── french_booking_agent.py ───┘─── Uses UserData + French Tools
```

## Language Detection Algorithm

```python
def detect_language(user_response):
    french_indicators = [
        'bonjour', 'salut', 'bonsoir', 'oui', 'non', 'merci',
        'je', 'suis', 'voudrais', 'rendez-vous', 'français',
        'parle', 'comprends', 'dentiste', 'clinique', 'allo',
        'comment', 'allez', 'vous', 'bien', 'très', 'avoir',
        'prendre', 'besoin'
    ]
    
    english_indicators = [
        'hello', 'hi', 'good', 'yes', 'no', 'thank',
        'i', 'am', 'would', 'like', 'appointment', 'english',
        'speak', 'understand', 'dentist', 'clinic', 'need',
        'want', 'book', 'schedule', 'help', 'can', 'you',
        'please', 'thanks'
    ]
    
    french_score = count_matches(user_response, french_indicators)
    english_score = count_matches(user_response, english_indicators)
    
    if french_score > english_score:
        return "french"
    elif english_score > french_score:
        return "english"
    else:
        return "english"  # Default fallback
```

## Session Configuration

```python
session = AgentSession(
    userdata=UserData(),
    stt=deepgram.STT(model="nova-3", language="multi"),  # Multilingual
    llm=openai.LLM(model="gpt-4o-mini"),
    tts=openai.TTS(voice="nova"),
    vad=silero.VAD.load(),                               # Voice Activity Detection
    turn_detection=MultilingualModel(),                  # Conversation flow
    max_tool_steps=5,
)
```

## Business Rules Implementation

### Operating Hours Validation
- **Hours**: Monday-Friday, 8:00 AM-12:00 PM, 1:00 PM-6:00 PM
- **Validation**: Both agents check appointment times against business hours
- **Fallback**: Suggest nearest available slot if outside hours

### Phone Number Format
- **Required Format**: (1) 111 222 3333
- **Collection Method**: Digit by digit for accuracy
- **Auto-correction**: Add country code (1) if omitted
- **Verification**: Repeat back digit by digit

### Language Consistency
- **Rule**: No language switching once conversation starts
- **Implementation**: Each specialized agent operates in single language
- **Override**: Only GreetingAgent handles bilingual interaction

## Error Handling & Fallbacks

1. **Language Detection Uncertainty**: Default to English
2. **Agent Transfer Failure**: Log error, continue with current agent
3. **Tool Execution Error**: Graceful degradation, ask user to repeat
4. **Session Interruption**: Preserve UserData for recovery
5. **Invalid Input**: Polite redirection to required information

## Monitoring & Logging

- **Language Detection**: Scores and decision rationale
- **Agent Transfers**: Timing and success/failure
- **User Data**: Complete booking information tracking
- **Session Flow**: Step-by-step conversation progress
- **Error Events**: Detailed error context for debugging
