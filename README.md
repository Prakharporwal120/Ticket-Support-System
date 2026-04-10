# Ticket-Support-System
# 🎫 SupportTicketEnv

> An **OpenEnv-compatible** environment that simulates a real-world customer support ticket resolution workflow. Built for hackathon evaluation of AI agents.

---

## 📌 Problem Statement

Customer support teams handle hundreds of tickets daily. Each ticket must be **categorized**, **prioritized**, **resolved**, and **closed** — a tedious, error-prone process. This environment provides a standardized testbed where AI agents learn to automate this workflow, measurable through deterministic scoring.

---

## 🏗️ System Architecture

```
┌──────────────┐     HTTP/JSON      ┌──────────────────────┐
│              │ ◄─────────────────► │                      │
│   AI Agent   │   POST /reset      │   FastAPI Server     │
│  (agent.py)  │   POST /step       │   (app/server.py)    │
│              │   GET  /state      │                      │
└──────────────┘                    └──────────┬───────────┘
                                               │
                                    ┌──────────▼───────────┐
                                    │  SupportTicketEnv    │
                                    │  (app/env.py)        │
                                    │                      │
                                    │  ┌─────────────────┐ │
                                    │  │ Tasks & Graders  │ │
                                    │  └─────────────────┘ │
                                    │  ┌─────────────────┐ │
                                    │  │ tickets.json     │ │
                                    │  └─────────────────┘ │
                                    └──────────────────────┘
```

**Flow:** Agent calls `/reset` → reads ticket → decides action → calls `/step` → receives reward → repeats until done.

---

## 📁 Folder Structure

```
support-ticket-env/
├── app/
│   ├── __init__.py          # Package init
│   ├── env.py               # Core environment (reset/step/state)
│   ├── models.py            # Pydantic models (Action, Observation, State)
│   ├── tasks.py             # Task definitions (easy/medium/hard)
│   ├── graders.py           # Deterministic graders (0.0–1.0)
│   └── server.py            # FastAPI server
├── data/
│   └── tickets.json         # 25 tickets with edge cases
├── agent.py                 # Rule-based AI agent
├── evaluate.py              # Evaluation script (runs all tasks)
├── metrics.py               # Metrics tracker (success rate, avg reward)
├── inference.py             # OpenEnv inference script
├── demo.py                  # Interactive endpoint demo
├── openenv.yaml             # OpenEnv manifest
├── Dockerfile               # Docker container
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## 🚀 How to Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
uvicorn app.server:app --host 0.0.0.0 --port 8000

# 3. In another terminal, choose what to run:
python agent.py         # Run the AI agent
python evaluate.py      # Run evaluation suite
python inference.py     # Run OpenEnv inference
python demo.py          # Interactive API demo
```

---

## 🐳 How to Run with Docker

```bash
# Build the image
docker build -t support-ticket-env .

# Run the container
docker run -p 8000:8000 support-ticket-env

# Test against container (in another terminal)
API_BASE_URL=http://localhost:8000 python evaluate.py
```

---

## 📋 API Endpoints

### `GET /health` — Health Check

```json
{ "status": "ok", "environment": "SupportTicketEnv" }
```

### `POST /reset` — Start New Episode

**Request:**
```json
{ "task": "easy_task", "ticket_id": 1 }
```

**Response:**
```json
{
  "observation": {
    "ticket_id": 1,
    "ticket_text": "My payment failed and I was still charged twice...",
    "category": null,
    "priority": null,
    "status": "open"
  },
  "info": {
    "task": "easy_task",
    "required_steps": ["categorize_ticket"],
    "max_steps": 3
  }
}
```

### `POST /step` — Execute Action

**Request:**
```json
{ "action_type": "categorize_ticket", "value": "billing" }
```

**Response:**
```json
{
  "observation": { "ticket_id": 1, "category": "billing", "status": "categorized" },
  "reward": 0.4,
  "done": true,
  "info": { "step": 1, "reason": "correct_category", "score": 1.0 }
}
```

### `GET /state` — Current Environment State

```json
{
  "current_ticket": { "ticket_id": 1, "status": "categorized" },
  "completed_steps": ["categorize_ticket"],
  "status": "done"
}
```

---

## 🔄 Example Workflow

```
1. POST /reset {"task": "hard_task"}
   → Ticket: "Production database is unresponsive..."

2. POST /step {"action_type": "categorize_ticket", "value": "technical"}
   → reward: +0.40, reason: correct_category

3. POST /step {"action_type": "assign_priority", "value": "high"}
   → reward: +0.30, reason: correct_priority

4. POST /step {"action_type": "resolve_ticket", "value": "Database restored"}
   → reward: +0.30, reason: valid_resolution

5. POST /step {"action_type": "close_ticket", "value": "Verified"}
   → reward: 0.00, done: true, score: 1.0, reason: task_completed
```

---

## 🎯 Tasks & Scoring

| Task | Difficulty | Goal | Required Steps | Scoring |
|------|-----------|------|----------------|---------|
| `easy_task` | Easy | Categorize ticket | `categorize_ticket` | 1.0 if correct, 0.0 if wrong |
| `medium_task` | Medium | Assign priority | `assign_priority` | 1.0 exact, 0.5 valid but wrong |
| `hard_task` | Hard | Full workflow | All 4 steps | 0.25 per correct step |

## 💰 Reward Table

| Action | Reward | Info Reason |
|--------|--------|-------------|
| Correct category | +0.4 | `correct_category` |
| Correct priority | +0.3 | `correct_priority` |
| Valid resolution | +0.3 | `valid_resolution` |
| Wrong answer | -0.2 | `wrong_category` / `wrong_priority` |
| Repeat action | -0.1 | `repeated_action` |
| Close ticket | 0.0 | `ticket_closed` |

---

## 📊 Dataset

**25 tickets** across 5 categories with edge cases:

| Category | Count | Example |
|----------|-------|---------|
| Billing | 7 | "My payment failed and I was charged twice" |
| Technical | 5 | "The server is down and nobody can access the dashboard" |
| Account | 5 | "I cannot log into my account after resetting my password" |
| Delivery | 3 | "My package has not arrived even though tracking says delivered" |
| Refund | 2 | "I want my money back for the defective product" |

**Edge cases:** Empty message, typo message, very long message, multi-issue ticket.

---

## 🔮 Future Improvements

- [ ] LLM-powered agent (replace rule-based with GPT/Claude)
- [ ] Multi-turn conversation support
- [ ] Agent memory across tickets
- [ ] Real-time dashboard for metrics visualization
- [ ] Leaderboard for comparing agent performance
- [ ] Support for custom ticket datasets via upload
- [ ] Webhook notifications on task completion
- [ ] A/B testing framework for agent strategies

---

## 🏗️ Runtime Requirements

- **CPU:** 2 cores
- **RAM:** 8 GB
- **Inference timeout:** < 20 minutes
- **Docker:** Compatible with `docker build` + `docker run`

---

## 📜 License

MIT
