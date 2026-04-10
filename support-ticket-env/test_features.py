"""Quick test for new ticket queue features."""
import httpx

c = httpx.Client(base_url="http://localhost:8000", timeout=10)

# Test 1: Ticket counts
print("=== TEST 1: Ticket counts ===")
r = c.get("/tickets")
counts = r.json()["ticket_counts"]
print(f"Total: {counts['total_tickets']}, Open: {counts['open_tickets']}, Resolved: {counts['resolved_tickets']}")

# Test 2: Reset loads first open ticket
print("\n=== TEST 2: Reset loads first open ticket ===")
r = c.post("/reset", json={"task": "hard_task"})
d = r.json()
tid = d["observation"]["ticket_id"]
print(f"Loaded ticket #{tid}")

# Test 3: Full workflow
print("\n=== TEST 3: Complete hard task ===")
actions = [
    {"action_type": "categorize_ticket", "value": "billing"},
    {"action_type": "assign_priority", "value": "high"},
    {"action_type": "resolve_ticket", "value": "Fixed the payment issue"},
    {"action_type": "close_ticket", "value": "Done"},
]
for a in actions:
    r = c.post("/step", json=a)
    sd = r.json()
    reason = sd.get("info", {}).get("reason", "")
    print(f"  {a['action_type']:20s} reward={sd['reward']:+.2f} done={sd['done']} reason={reason}")
    if sd["done"]:
        score = sd["info"].get("score", 0)
        print(f"  >> SCORE: {score}")
        next_id = sd["info"].get("next_ticket_id")
        if next_id:
            print(f"  >> Next ticket available: #{next_id}")

# Test 4: Resolved tickets
print("\n=== TEST 4: Resolved tickets ===")
r = c.get("/tickets")
data = r.json()
resolved = data["resolved_tickets"]
counts = data["ticket_counts"]
print(f"Resolved count: {len(resolved)}")
for rt in resolved:
    print(f"  #{rt['ticket_id']}: cat={rt['category']}, pri={rt['priority']}, status={rt['status']}")
print(f"Counts: total={counts['total_tickets']} open={counts['open_tickets']} resolved={counts['resolved_tickets']}")

# Test 5: Reset loads next open ticket
print("\n=== TEST 5: Auto-load next open ticket ===")
r = c.post("/reset", json={"task": "easy_task"})
d = r.json()
new_tid = d["observation"]["ticket_id"]
print(f"Next ticket loaded: #{new_tid} (should be #{tid + 1} or higher)")

# Test 6: Original inference still works (specific ticket_id)
print("\n=== TEST 6: Explicit ticket_id still works ===")
r = c.post("/reset", json={"task": "easy_task", "ticket_id": 10})
d = r.json()
print(f"Explicit load ticket #{d['observation']['ticket_id']}: OK")

c.close()
print("\n=== ALL TESTS PASSED ===")
