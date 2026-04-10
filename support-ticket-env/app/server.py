"""FastAPI server exposing the SupportTicketEnv as an HTTP API.

Endpoints:
    POST /reset  — Reset the environment for a new episode.
    POST /step   — Execute one action step.
    GET  /state  — Get the current environment state.
    GET  /health — Health check endpoint.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.env import SupportTicketEnv
from app.models import Action, ResetRequest

# --- Application Setup ---

app = FastAPI(
    title="SupportTicketEnv",
    description="OpenEnv-compatible customer support ticket resolution environment.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Environment Instance ---
env = SupportTicketEnv()


# --- Endpoints ---

@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok", "environment": "SupportTicketEnv"}


@app.post("/reset")
def reset(request: ResetRequest = ResetRequest()):
    """Reset the environment for a new episode.

    Args:
        request: Optional body with 'task' and 'ticket_id'.

    Returns:
        Initial observation and info.
    """
    try:
        result = env.reset(task=request.task, ticket_id=request.ticket_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step")
def step(action: Action):
    """Execute one action step in the environment.

    Args:
        action: The action to perform (action_type + value).

    Returns:
        Observation, reward, done flag, and info.
    """
    try:
        result = env.step(action)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state")
def state():
    """Get the current environment state.

    Returns:
        Current ticket, completed steps, and environment status.
    """
    try:
        result = env.state()
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tickets")
def tickets():
    """Get ticket queue status: counts and resolved tickets.

    Returns:
        Ticket counts and list of resolved tickets.
    """
    return {
        "ticket_counts": env.get_ticket_counts(),
        "resolved_tickets": env.get_resolved_tickets(),
    }

