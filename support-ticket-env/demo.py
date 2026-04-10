"""Interactive demo showing how every endpoint of SupportTicketEnv works."""

import httpx
import json

BASE = "http://localhost:8000"
client = httpx.Client(base_url=BASE)

def pretty(data):
    print(json.dumps(data, indent=2))

# ── 1. Health Check ──────────────────────────────────────────
print("=" * 60)
print("1. HEALTH CHECK  (GET /health)")
print("=" * 60)
r = client.get("/health")
pretty(r.json())

# ── 2. Reset with easy_task ──────────────────────────────────
print("\n" + "=" * 60)
print("2. RESET - easy_task  (POST /reset)")
print("=" * 60)
r = client.post("/reset", json={"task": "easy_task"})
pretty(r.json())

# ── 3. Check state ───────────────────────────────────────────
print("\n" + "=" * 60)
print("3. STATE - should be in_progress  (GET /state)")
print("=" * 60)
r = client.get("/state")
pretty(r.json())

# ── 4. Step - correct categorization ─────────────────────────
print("\n" + "=" * 60)
print('4. STEP - categorize_ticket = "billing" (correct!)')
print("=" * 60)
r = client.post("/step", json={"action_type": "categorize_ticket", "value": "billing"})
data = r.json()
pretty(data)
print(f"\n  >> reward={data['reward']}, done={data['done']}, score={data['info'].get('score')}")

# ── 5. State after completion ────────────────────────────────
print("\n" + "=" * 60)
print("5. STATE - should be done  (GET /state)")
print("=" * 60)
r = client.get("/state")
pretty(r.json())

# ── 6. Wrong action demo ────────────────────────────────────
print("\n" + "=" * 60)
print("6. RESET + WRONG ACTION DEMO  (wrong category)")
print("=" * 60)
client.post("/reset", json={"task": "easy_task"})
r = client.post("/step", json={"action_type": "categorize_ticket", "value": "technical"})
data = r.json()
print(f"  >> reward={data['reward']} (negative = wrong!)")
print(f"  >> error: {data['info'].get('error')}")

# ── 7. Hard task - full workflow ─────────────────────────────
print("\n" + "=" * 60)
print("7. HARD TASK - Full 4-step workflow")
print("=" * 60)
client.post("/reset", json={"task": "hard_task"})

actions = [
    {"action_type": "categorize_ticket", "value": "technical"},
    {"action_type": "assign_priority", "value": "high"},
    {"action_type": "resolve_ticket", "value": "Database restored by ops team"},
    {"action_type": "close_ticket", "value": "Confirmed resolved"},
]

for i, action in enumerate(actions, 1):
    r = client.post("/step", json=action)
    d = r.json()
    score_str = ""
    if d["info"].get("score") is not None:
        score_str = f"  FINAL SCORE={d['info']['score']}"
    print(f"  Step {i}: {action['action_type']:20s} -> reward={d['reward']:+.2f}  done={d['done']}{score_str}")

# ── 8. Repeat action demo ───────────────────────────────────
print("\n" + "=" * 60)
print("8. REPEAT ACTION DEMO  (penalty = -0.1)")
print("=" * 60)
client.post("/reset", json={"task": "hard_task"})
client.post("/step", json={"action_type": "categorize_ticket", "value": "technical"})
r = client.post("/step", json={"action_type": "categorize_ticket", "value": "billing"})
data = r.json()
print(f"  >> reward={data['reward']} (repeat penalty)")
print(f"  >> error: {data['info'].get('error')}")

client.close()
print("\n" + "=" * 60)
print("DEMO COMPLETE - All endpoints working!")
print("=" * 60)
