"""Rule-based agent for SupportTicketEnv.

This agent calls POST /reset, reads the observation, decides actions based on
simple keyword matching on ticket_text, calls POST /step, and repeats until done.

Usage:
    1. Start the server:  uvicorn app.server:app --host 0.0.0.0 --port 8000
    2. Run the agent:     python agent.py
"""

import os
import sys
import httpx
import json
from datetime import datetime

# --- Configuration ---
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


# --- Rule-based decision engine ---

# Keyword → category mapping (checked in order, first match wins)
CATEGORY_RULES = [
    (["payment", "charge", "invoice", "billing", "subscription", "refund", "discount", "paymnt", "faild", "checkout", "price"], "billing"),
    (["login", "password", "account", "email", "cancel", "profile", "signup", "register", "log in"], "account"),
    (["server", "crash", "error", "bug", "down", "database", "app", "loading", "unresponsive", "api", "deploy"], "technical"),
    (["deliver", "shipping", "package", "track", "shipment", "order", "dispatch", "warehouse"], "delivery"),
    (["refund", "return", "money back", "reimburse"], "refund"),
]

# Keyword → priority mapping
PRIORITY_RULES = [
    (["urgent", "critical", "down", "losing revenue", "production", "emergency", "immediately", "asap", "cannot", "failed"], "high"),
    (["request", "would like", "want to", "change", "update", "help", "understand", "cancel", "crash"], "medium"),
    (["how do", "question", "wondering", "information", "learn"], "low"),
]


def decide_category(ticket_text: str) -> str:
    """Determine ticket category from text using keyword rules."""
    text_lower = ticket_text.lower()

    if not text_lower.strip():
        return "technical"  # Default for empty messages

    for keywords, category in CATEGORY_RULES:
        for keyword in keywords:
            if keyword in text_lower:
                return category

    return "technical"  # Fallback default


def decide_priority(ticket_text: str) -> str:
    """Determine ticket priority from text using keyword rules."""
    text_lower = ticket_text.lower()

    if not text_lower.strip():
        return "medium"  # Default for empty messages

    for keywords, priority in PRIORITY_RULES:
        for keyword in keywords:
            if keyword in text_lower:
                return priority

    return "medium"  # Fallback default


def decide_resolution(ticket_text: str, category: str) -> str:
    """Generate a resolution message based on ticket context."""
    resolutions = {
        "billing": "Billing issue has been reviewed and corrected. A refund or adjustment has been processed.",
        "account": "Account issue has been resolved. Access has been restored and credentials verified.",
        "technical": "Technical issue has been identified and fixed by the engineering team.",
        "delivery": "Delivery issue has been escalated to the logistics team for immediate resolution.",
        "refund": "Refund request has been processed and will be reflected within 5-7 business days.",
    }
    return resolutions.get(category, "Issue has been reviewed and resolved by the support team.")


# --- Agent runner ---

def run_agent(task_name: str, ticket_id: int = None) -> dict:
    """Run the agent on a single task.

    Args:
        task_name: One of easy_task, medium_task, hard_task.
        ticket_id: Optional ticket ID to use (otherwise uses task default).

    Returns:
        Dictionary with results: success, score, steps, rewards.
    """
    client = httpx.Client(base_url=API_BASE_URL, timeout=30.0)
    timestamp = datetime.now().strftime("%H:%M:%S")

    print(f"\n{'='*60}")
    print(f"[{timestamp}] AGENT START | task={task_name}")
    print(f"{'='*60}")

    # --- Reset ---
    reset_body = {"task": task_name}
    if ticket_id is not None:
        reset_body["ticket_id"] = ticket_id

    try:
        resp = client.post("/reset", json=reset_body)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  ERROR: Failed to reset environment: {e}")
        client.close()
        return {"success": False, "score": 0.0, "steps": 0, "rewards": []}

    obs = data["observation"]
    info = data["info"]
    ticket_text = obs["ticket_text"]
    required_steps = info.get("required_steps", [])

    print(f"  Ticket #{obs['ticket_id']}: \"{ticket_text[:80]}{'...' if len(ticket_text) > 80 else ''}\"")
    print(f"  Required steps: {required_steps}")

    # --- Decide actions based on task requirements ---
    category = decide_category(ticket_text)
    priority = decide_priority(ticket_text)
    resolution = decide_resolution(ticket_text, category)

    action_plan = []
    for step_name in required_steps:
        if step_name == "categorize_ticket":
            action_plan.append({"action_type": "categorize_ticket", "value": category})
        elif step_name == "assign_priority":
            action_plan.append({"action_type": "assign_priority", "value": priority})
        elif step_name == "resolve_ticket":
            action_plan.append({"action_type": "resolve_ticket", "value": resolution})
        elif step_name == "close_ticket":
            action_plan.append({"action_type": "close_ticket", "value": "Ticket resolved and verified."})

    # --- Execute steps ---
    rewards = []
    step_count = 0
    done = False
    score = 0.0

    for action in action_plan:
        if done:
            break
        step_count += 1
        try:
            resp = client.post("/step", json=action)
            resp.raise_for_status()
            step_data = resp.json()

            reward = step_data["reward"]
            done = step_data["done"]
            step_info = step_data.get("info", {})
            reason = step_info.get("reason", "")
            error = step_info.get("error", None)
            rewards.append(reward)

            status_icon = "[OK]" if reward > 0 else ("[--]" if reward == 0 else "[XX]")
            error_str = f" | error: {error}" if error else ""
            reason_str = f" | reason: {reason}" if reason else ""

            print(f"  Step {step_count}: {action['action_type']:20s} = {action['value'][:30]:30s} -> reward={reward:+.2f} {status_icon}{reason_str}{error_str}")

            if done:
                score = step_info.get("score", 0.0)

        except Exception as e:
            print(f"  Step {step_count}: {action['action_type']:20s} -> ERROR: {e}")
            rewards.append(0.0)
            step_count += 1

    # --- Result ---
    success = done and score >= 0.5
    result_icon = ">> PASS" if success else ">> FAIL"
    print(f"\n  Result: {result_icon} | score={score:.2f} | steps={step_count} | total_reward={sum(rewards):.2f}")

    client.close()
    return {
        "success": success,
        "score": score,
        "steps": step_count,
        "rewards": rewards,
    }


def main():
    """Run the agent on all three tasks."""
    print("+" + "=" * 58 + "+")
    print("|" + " SupportTicketEnv -- Rule-Based Agent ".center(58) + "|")
    print("|" + f" Server: {API_BASE_URL} ".center(58) + "|")
    print("+" + "=" * 58 + "+")

    tasks = ["easy_task", "medium_task", "hard_task"]
    results = {}

    for task in tasks:
        results[task] = run_agent(task)

    # --- Summary ---
    print(f"\n{'='*60}")
    print("AGENT SUMMARY")
    print(f"{'='*60}")
    total_success = sum(1 for r in results.values() if r["success"])
    total_steps = sum(r["steps"] for r in results.values())
    total_rewards = sum(sum(r["rewards"]) for r in results.values())

    for task, result in results.items():
        status = "PASS" if result["success"] else "FAIL"
        print(f"  {task:15s} -> {status}  score={result['score']:.2f}  steps={result['steps']}")

    print(f"\n  Passed: {total_success}/{len(tasks)}  |  Total steps: {total_steps}  |  Total reward: {total_rewards:.2f}")

    sys.exit(0 if total_success == len(tasks) else 1)


if __name__ == "__main__":
    main()
