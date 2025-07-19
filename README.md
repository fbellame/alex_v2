# Alex V2 - Multi-Language Dental Booking System

A sophisticated voice-based dental appointment booking system with automatic language detection and routing capabilities.

## Architecture Overview

The system uses a multi-agent architecture with language detection and routing:

### Agent Structure

1. **GreetingAgent** - Entry point and language router
   - Greets users with "Hi Bonjour, welcome to SmileRight Dental Clinic, how can I help you today?"
   - Detects language preference from user's first response
   - Routes to appropriate specialized booking agent

2. **EnglishBookingAgent** - English booking specialist
   - Handles complete booking flow in English
   - Collects: appointment date/time, name, phone, reason
   - Validates business hours and formats

3. **FrenchBookingAgent** - French booking specialist  
   - Handles complete booking flow in French
   - Collects: date/heure rendez-vous, prénom, nom, téléphone, raison
   - Validates business hours and formats

### Workflow

```
User connects → GreetingAgent
    ↓
"Hi Bonjour, welcome to SmileRight Dental Clinic, how can I help you today?"
    ↓
User responds in preferred language
    ↓
Language detection analysis
    ↓
Transfer to specialized agent:
├── French detected → FrenchBookingAgent
└── English detected → EnglishBookingAgent
    ↓
Complete booking process in detected language
```

## File Structure

```
alex_v2/
├── alex_greeting.py              # Main entry point with greeting system
├── alex_main.py                  # Original English-only system
├── alex_main_french.py           # Original French-only system
├── shared/
│   ├── user_data.py             # Shared UserData class
│   └── tools/
│       ├── english_tools.py     # English function tools
│       └── french_tools.py      # French function tools
└── agents/
    ├── greeting_agent.py        # Language detection and routing
    ├── english_booking_agent.py # English booking specialist
    └── french_booking_agent.py  # French booking specialist
```

## Usage

### Running the Greeting System

```bash
python alex_greeting.py
```

This starts the multi-agent system with automatic language detection.

### Running Original Systems (Legacy)

```bash
# English only
python alex_main.py

# French only  
python alex_main_french.py
```

## Language Detection

The system uses keyword-based language detection with scoring:

### French Indicators
- bonjour, salut, bonsoir, oui, non, merci
- je, suis, voudrais, rendez-vous, français
- parle, comprends, dentiste, clinique
- allo, comment, allez, vous, bien, très
- avoir, prendre, besoin

### English Indicators  
- hello, hi, good, yes, no, thank
- i, am, would, like, appointment, english
- speak, understand, dentist, clinic
- need, want, book, schedule, help
- can, you, please, thanks

## Features

### Shared Capabilities
- **Voice Recognition**: Deepgram STT with multilingual support
- **Text-to-Speech**: OpenAI TTS with natural voice
- **Noise Cancellation**: Background noise filtering
- **Turn Detection**: Multilingual conversation flow
- **Data Persistence**: Customer information maintained across transfers

### Booking Flow
1. **Appointment Date/Time**: Validates business hours
2. **Customer Name**: First and last name collection
3. **Phone Number**: Digit-by-digit format (1) 111 222 3333
4. **Visit Reason**: Purpose of appointment
5. **Confirmation**: Complete booking summary

### Business Rules
- **Operating Hours**: Monday-Friday, 8:00 AM-12:00 PM, 1:00 PM-6:00 PM
- **Location**: 5561 St-Denis Street, Montreal, Canada
- **Phone Format**: (1) 111 222 3333 with digit-by-digit entry
- **Language Consistency**: No switching once conversation starts

## Technical Details

### Dependencies
- livekit-agents with deepgram, openai, cartesia, silero plugins
- python-dotenv for environment configuration
- pyyaml for data serialization
- aiosqlite, pandas, matplotlib, seaborn for data handling

### Agent Transfer Mechanism
- Event-driven transfers based on function tool responses
- Preserved user context across agent switches
- Seamless handoff with appropriate language greeting

### Logging
- Comprehensive logging for debugging and monitoring
- User data summarization for session tracking
- Language detection scoring for optimization

## Environment Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_key
LIVEKIT_API_SECRET=your_livekit_secret
```

3. Run the system:
```bash
python alex_greeting.py
```

## Customization

### Adding New Languages
1. Create new tools file in `shared/tools/`
2. Create new booking agent in `agents/`
3. Add language indicators to greeting agent
4. Update main entry point to include new agent

### Modifying Business Rules
- Update clinic info constants in tool files
- Modify operating hours validation
- Adjust phone number format requirements
- Customize booking flow steps

## Monitoring and Debugging

The system provides detailed logging for:
- Language detection scores and decisions
- Agent transfer events and timing
- User data collection and validation
- Session flow and error handling

Check logs for troubleshooting and optimization opportunities.
