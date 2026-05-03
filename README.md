# Edtronaut AI Co-worker Engine

## Project Structure

```
npc_engine/
│
├── main.py
│
├── models/
│   ├── session_state.py
│   └── personas.py
│
├── agents/
│   ├── npc_agent.py
│   └── supervisor_agent.py
│
└── utils/
    ├── safety_filter.py
    └── rag_retriever.py
```

## Architecture Overview

```
User Message
     │
     ▼
┌─────────────────────────────────────────────┐
│              NPCAgent.run()                 │
│                                             │
│  1. SafetyFilter   → jailbreak / off-topic  │
│  2. SupervisorAgent→ stuck / director hint  │
│  3. RAGRetriever   → relevant context       │
│  4. Prompt Builder → system prompt          │
│  5. Message Builder→ history + context      │
│  6. LLM Call       → Claude Sonnet          │
│  7. State Update   → mood, history, rubric  │
└─────────────────────────────────────────────┘
     │
     ▼
AgentResponse(message, state_update, safety_flags, director_action)
```

## Key Design Decisions

### 3-Layer Persona Design

Each NPC persona has three layers:

- **Public layer** — what learners can see (name, role, mission)
- **Business-rule layer** — hidden constraints (never reveal salaries, etc.)
- **Emotional-state layer** — `mood_score` –2.0 to +2.0, affects tone

### Mood-Driven Tone

`mood_score` changes every turn based on learner behavior:

- Jailbreak attempt → –1.5
- Off-topic message → –0.3
- Short/vague message → –0.1
- On-topic message → +0.3
- Detailed message (30+ words) → +0.5

### Supervisor Agent (Director Layer)

Runs invisibly after every turn. Three escalating interventions:

1. **SUBTLE_HINT** (turn 3+): inject hint into NPC prompt
2. **DIRECT_NUDGE** (turn 6+): show progress reminder on UI
3. **SCAFFOLD** (turn 9+): NPC switches to guided questioning mode

### Safety Filter

Runs **before** LLM call — jailbreak patterns never reach the model

## Running the Demo

```bash
python main.py
```

## Production Stack

| Component     | Prototype        | Production                |
| ------------- | ---------------- | ------------------------- |
| LLM           | Mock response    | Claude Sonnet (streaming) |
| Vector DB     | Keyword matching | FAISS → Pinecone          |
| Session store | In-memory        | Redis with TTL            |
| API framework | —                | FastAPI + WebSocket       |
| Orchestration | Direct call      | LangGraph workflow        |

## NPCAgent Interface

```python
agent = NPCAgent()

response = agent.run(
    persona_id    = "chro_gucci",
    user_message  = "Explain the competency framework",
    session_state = SessionState(),
    simulation_id = "gucci_hrm",
    current_module= "module_1"
)
```
