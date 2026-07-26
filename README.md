# AI_REPLICA — Krushna's Personal AI Assistant (KRONOS)

## Status: ⚙️ Phase 3 Development (v3.0.0-dev)

**AI_REPLICA** is a comprehensive, modular AI assistant system built for Krushna Kumbhar. We are currently implementing **Phase 3 - Social Agents** and enhancing the **Voice Processing Layer** (including Speech Detection and Wake Word Engines).

## Quick Architecture

```
┌─────────────────────────────────────────┐
│           JARVIS AI System              │
├─────────────────────────────────────────┤
│  Core: Brain│Memory│Persona│Reasoning  │
├─────────────────────────────────────────┤
│  Agents: Social│Mail│Job│Desktop│Voice │
├─────────────────────────────────────────┤
│  Integrations: Discord│LinkedIn│Gmail   │
├─────────────────────────────────────────┤
│  UI: RingUI│Overlay│Notifications       │
├─────────────────────────────────────────┤
│  Storage: PostgreSQL│Vectors│Cache      │
├─────────────────────────────────────────┤
│  Runtime: EventBus│Workers│Orchestrator │
└─────────────────────────────────────────┘
```

## Features

✅ **Core Intelligence**

- GPT-4 powered AI engine
- Intelligent decision routing
- Adaptive learning system
- Pattern recognition

✅ **6 Specialized Agents**

- Social media management
- Email automation
- Job search & applications
- Desktop control
- Voice interactions
- Calendar & reminders

✅ **5 Service Integrations**

- Discord bot
- LinkedIn API
- Gmail integration
- Telegram messaging
- Web automation

✅ **Advanced Storage**

- PostgreSQL relational DB
- Vector embeddings (semantic search)
- Redis caching layer

✅ **Runtime Orchestration**

- Event-driven architecture
- Thread pool workers
- System orchestration engine

## Setup

### 1. Installation

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create `.env` in project root:

```
OPENAI_API_KEY=sk-...
DISCORD_TOKEN=...
TELEGRAM_TOKEN=...
GMAIL_USER=...
GMAIL_PASS=...
POSTGRESQL_URL=postgresql://...
```

### 3. Run JARVIS

```bash
# Interactive CLI
python -m AI_REPLICA.main

# Or programmatic
from AI_REPLICA.main import init_jarvis
jarvis = init_jarvis()
response = jarvis.process_input("What's on my calendar?")
```

## Architecture Highlights

### Modular Design

- **Separation of concerns**: Each module has single responsibility
- **Easy to extend**: Add new agents, integrations, or storage backends
- **Testable**: Each component can be tested independently

### Scalability

- **Thread pool workers** for concurrent operations
- **Caching layer** for performance
- **Vector database** for semantic search at scale
- **Event bus** for loose coupling

### Maintainability

- **Comprehensive logging** across all systems
- **Type hints** for better code clarity
- **Documentation** at module and function level
- **Clear directory structure**

## Core Components

| Module        | Purpose           | Key Classes                             |
| ------------- | ----------------- | --------------------------------------- |
| **Brain**     | AI reasoning      | AIEngine, DecisionMaker, LearningSystem |
| **Memory**    | Data storage      | Memory, TaskManager                     |
| **Persona**   | Identity          | Personality, Tone                       |
| **Reasoning** | Pattern learning  | PatternLearner                          |
| **Autonomy**  | Activity tracking | ActivityTracker                         |

## Usage Examples

### Basic Chat

```python
from AI_REPLICA.main import init_jarvis

jarvis = init_jarvis()
response = jarvis.process_input("Hello, how are you?")
print(response)
```

### Task Management

```python
# Create task
task = jarvis.task_manager.create_task("Review code", priority=3)

# Complete task
jarvis.task_manager.complete_task(task["id"])

# List tasks
pending = jarvis.task_manager.list_tasks(status="pending")
```

### Memory Operations

```python
# Store fact
jarvis.memory.store_fact("favorite_language", "Python")

# Recall fact
lang = jarvis.memory.recall_fact("favorite_language")

# Record event
jarvis.memory.record_event("learning_started", "Started learning ML")
```

### Pattern Analysis

```python
# Analyze interaction patterns
stats = jarvis.pattern_learner.analyze()
print(f"Total interactions: {stats['total_interactions']}")
```

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=AI_REPLICA tests/

# Run specific test
pytest tests/test_core.py::test_ai_engine
```

## Development Guide

### Adding a New Agent

1. Create `agents/my_agent/` directory
2. Implement agent class with required methods
3. Register with orchestrator

### Adding an Integration

1. Create `integrations/my_service/` directory
2. Implement integration class
3. Configure credentials in `.env`

### Adding Storage Backend

1. Create `storage/my_backend/` directory
2. Implement backend interface
3. Register in system initialization

## Performance Metrics

- **Response Time**: <1s for typical queries (with caching)
- **Throughput**: 100+ queries/minute with thread pool
- **Memory**: ~150MB base + model size
- **Storage**: Scales with database backend

## Security Features

- ✅ Environment variable-based secrets management
- ✅ Input validation on all user inputs
- ✅ Rate limiting on external APIs
- ✅ Secure credential storage
- ✅ Comprehensive audit logging

## Roadmap & Phase Progression

### Phase 3: Social Agents & Voice Upgrades (In Progress)

- [x] **Social Agent Abstraction Framework**: Created `BaseAgent`, `AgentRegistry`, `AgentManager` and agent health check APIs.
- [x] **Production Database Foundation**: Created base mixins (`UUIDMixin`, `TimestampMixin`, `SoftDeleteMixin`) and global schema enums.
- [x] **Voice Activity Detection (VAD) Engine**: Integrated Silero VAD for real-time speech/silence probability detection.
- [x] **Wake Word Engine Prep**: Added `openwakeword`, `onnxruntime`, and `librosa` dependencies and `AssistantState` enums.
- [ ] **Database Models upgrade**: Platform, SocialAccount, Conversation, and Message schema enhancements (Module 2-4).
- [ ] **Social Integrations**: Real connection bots for Discord, Telegram, Gmail, and LinkedIn.

### Future Roadmap

- [ ] Multi-user support with authentication
- [ ] Advanced NLP with fine-tuned models
- [ ] Mobile companion app
- [ ] Real-time collaboration
- [ ] Cloud deployment (AWS/GCP)
- [ ] Advanced analytics dashboard

## Project Structure

See [AI_REPLICA/README.md](./AI_REPLICA/README.md) for detailed architecture documentation.

## Support & Contact

**Creator**: Krushna Kumbhar  
**Email**: krushanakumbhar314@gmail.com  
**GitHub**: @Krushna56

---

**Version**: 3.0.0-dev  
**Status**: Phase 3 Development (In Progress) ⚙️  
**Last Updated**: July 26, 2026
